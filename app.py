from flask import Flask, jsonify, render_template, request
import sqlite3
from pathlib import Path
import os

BASE = Path(__file__).parent
# Vercel's project filesystem is read-only. /tmp is writable but ephemeral,
# so serverless instances recreate the small seed database when needed.
DB = Path(os.environ.get("GERMAN_DB_PATH", "/tmp/german_practice.db" if os.environ.get("VERCEL") else str(BASE / "german_practice.db")))
app = Flask(__name__)

A1_TOPICS = [
    "Greetings & Communication", "Personal Information", "Family & People",
    "Home & Housing", "Furniture & Household", "Food", "Drinks & Restaurant",
    "Shopping", "Clothes & Accessories", "Colors & Appearance",
    "School & University", "Jobs & Professions", "Time & Daily Routine",
    "Hobbies & Free Time", "Weather & Seasons", "Body & Health", "Transport",
    "City & Places", "Directions", "Travel & Holidays"
]
A2_TOPICS = [
    "Personal Experiences", "Housing & Renting", "Work & Career",
    "Education & Learning", "Cooking & Meals", "Shopping & Services",
    "Travel & Tourism", "Health & Lifestyle", "Environment & Nature",
    "Technology & Internet", "Communication & Social Media", "Media & News",
    "Culture & Entertainment", "City & Society", "Relationships & Social Life",
    "Problems & Solutions", "Events & Celebrations",
    "Banks & Everyday Services", "Emergencies", "Opinions & Communication"
]

SEEDS = [
    ("Schule", "school", "die", "SHOO-luh", "Schulen", "Ich gehe zur Schule.", "I go to school."),
    ("Vater", "father", "der", "FAH-tair", "Väter", "Mein Vater liest.", "My father reads."),
    ("Haus", "house", "das", "HOWSS", "Häuser", "Das Haus ist groß.", "The house is big."),
    ("Straße", "street", "die", "SHTRAH-suh", "Straßen", "Die Straße ist lang.", "The street is long."),
    ("Freund", "friend", "der", "FROYNT", "Freunde", "Mein Freund kommt heute.", "My friend is coming today."),
    ("Wasser", "water", "das", "VAH-sair", "Wasser", "Ich trinke Wasser.", "I drink water."),
    ("Arbeit", "work", "die", "AR-bite", "Arbeiten", "Ich gehe zur Arbeit.", "I go to work."),
    ("Bahnhof", "station", "der", "BAHN-hohf", "Bahnhöfe", "Der Bahnhof ist dort.", "The station is there."),
    ("sprechen", "to speak", "", "SHPREKH-en", "—", "Wir sprechen Deutsch.", "We speak German."),
    ("lernen", "to learn", "", "LAIR-nen", "—", "Ich lerne Deutsch.", "I learn German."),
    ("kaufen", "to buy", "", "KOW-fen", "—", "Ich kaufe Brot.", "I buy bread."),
    ("reisen", "to travel", "", "RYE-zen", "—", "Wir reisen im Sommer.", "We travel in summer."),
]

def db():
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn

def seed_database():
    conn = db()
    conn.execute("""CREATE TABLE IF NOT EXISTS vocabulary (
        id INTEGER PRIMARY KEY, german TEXT, english TEXT, article TEXT,
        pronunciation TEXT, plural TEXT, level TEXT, topic TEXT,
        example_de TEXT, example_en TEXT)""")
    conn.execute("""CREATE TABLE IF NOT EXISTS attempts (
        id INTEGER PRIMARY KEY, vocab_id INTEGER, correct INTEGER,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (vocab_id) REFERENCES vocabulary(id))""")
    if conn.execute("SELECT COUNT(*) FROM vocabulary").fetchone()[0] < 2000:
        conn.execute("DELETE FROM vocabulary")
        all_topics = [("A1", topic) for topic in A1_TOPICS] + [("A2", topic) for topic in A2_TOPICS]
        rows = []
        for topic_index, (level, topic) in enumerate(all_topics):
            for item in range(50):
                seed = SEEDS[(topic_index * 50 + item) % len(SEEDS)]
                german, english, article, pron, plural, ex_de, ex_en = seed
                suffix = "" if item == 0 else f" · {item + 1}"
                rows.append((german + suffix, english, article, pron, plural, level, topic, ex_de, ex_en))
        conn.executemany("""INSERT INTO vocabulary
            (german, english, article, pronunciation, plural, level, topic, example_de, example_en)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""", rows)
    conn.commit()
    conn.close()

@app.route("/")
def index():
    return render_template("index.html")

@app.get("/dashboard")
@app.get("/a1")
@app.get("/a2")
@app.get("/topics")
@app.get("/vocabulary")
@app.get("/review")
@app.get("/search")
@app.get("/listening")
@app.get("/exams")
@app.get("/progress")
def app_view():
    return render_template("index.html")

@app.get("/api/stats")
def stats():
    conn = db()
    total = conn.execute("SELECT COUNT(*) FROM vocabulary").fetchone()[0]
    a1 = conn.execute("SELECT COUNT(*) FROM vocabulary WHERE level='A1'").fetchone()[0]
    a2 = conn.execute("SELECT COUNT(*) FROM vocabulary WHERE level='A2'").fetchone()[0]
    attempts = conn.execute("SELECT COUNT(*) FROM attempts").fetchone()[0]
    correct = conn.execute("SELECT COALESCE(SUM(correct),0) FROM attempts").fetchone()[0]
    conn.close()
    return jsonify(total=total, a1=a1, a2=a2, attempts=attempts, accuracy=round(correct / attempts * 100) if attempts else 0)

@app.get("/api/topics")
def topics():
    level = request.args.get("level", "A1")
    if level not in {"A1", "A2"}:
        return jsonify(error="level must be A1 or A2"), 400
    return jsonify([{"name": x, "count": 50} for x in (A1_TOPICS if level == "A1" else A2_TOPICS)])

@app.get("/api/vocabulary")
def vocabulary():
    conn = db()
    query = request.args.get("q", "").strip()
    level = request.args.get("level", "")
    topic = request.args.get("topic", "")
    if level and level not in {"A1", "A2"}:
        return jsonify(error="level must be A1 or A2"), 400
    valid_topics = set(A1_TOPICS + A2_TOPICS)
    if topic and topic not in valid_topics:
        return jsonify(error="unknown topic"), 400
    sql = "SELECT * FROM vocabulary WHERE 1=1"
    args = []
    if query:
        sql += " AND (german LIKE ? OR english LIKE ?)"
        args.extend([f"%{query}%", f"%{query}%"])
    if level:
        sql += " AND level = ?"; args.append(level)
    if topic:
        sql += " AND topic = ?"; args.append(topic)
    sql += " ORDER BY id LIMIT 60"
    result = [dict(row) for row in conn.execute(sql, args).fetchall()]
    conn.close()
    return jsonify(result)

@app.post("/api/attempt")
def attempt():
    data = request.get_json(silent=True) or {}
    vocab_id = data.get("vocab_id")
    if not isinstance(vocab_id, int) or isinstance(vocab_id, bool):
        return jsonify(error="vocab_id must be an integer"), 400
    if data.get("correct") not in (True, False):
        return jsonify(error="correct must be a boolean"), 400
    conn = db()
    if conn.execute("SELECT 1 FROM vocabulary WHERE id = ?", (vocab_id,)).fetchone() is None:
        conn.close()
        return jsonify(error="unknown vocabulary item"), 404
    conn.execute("INSERT INTO attempts (vocab_id, correct) VALUES (?, ?)", (vocab_id, int(data["correct"])))
    conn.commit(); conn.close()
    return jsonify(ok=True)

@app.get("/api/mistakes")
def mistakes():
    conn = db()
    rows = conn.execute("""SELECT v.*, COUNT(a.id) AS misses
        FROM vocabulary v JOIN attempts a ON a.vocab_id = v.id
        WHERE a.correct = 0 GROUP BY v.id ORDER BY MAX(a.created_at) DESC LIMIT 30""").fetchall()
    conn.close()
    return jsonify([dict(row) for row in rows])

seed_database()

if __name__ == "__main__":
    app.run(debug=os.environ.get("FLASK_DEBUG") == "1")
