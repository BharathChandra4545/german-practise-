from flask import Flask, jsonify, render_template, request
import os
from database import connect, placeholder_sql

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
    return connect()


def execute(conn, sql, params=()):
    return conn.execute(placeholder_sql(sql), params)


def scalar(row, key):
    return row[key] if isinstance(row, dict) else row[0]

def seed_database():
    from init_db import main as init_db
    init_db()
    conn = db()
    count = scalar(execute(conn, "SELECT COUNT(*) AS count FROM vocabulary").fetchone(), "count")
    conn.close()
    if count < 2000:
        from seed_database import seed
        seed()


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
    total = scalar(execute(conn, "SELECT COUNT(*) AS count FROM vocabulary").fetchone(), "count")
    a1 = scalar(execute(conn, "SELECT COUNT(*) AS count FROM vocabulary WHERE level='A1'").fetchone(), "count")
    a2 = scalar(execute(conn, "SELECT COUNT(*) AS count FROM vocabulary WHERE level='A2'").fetchone(), "count")
    attempts = scalar(execute(conn, "SELECT COUNT(*) AS count FROM attempts").fetchone(), "count")
    correct = scalar(execute(conn, "SELECT COALESCE(SUM(correct),0) AS count FROM attempts").fetchone(), "count")
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
    sql = """
        SELECT id, german, english, article, pronunciation, plural,
               example_de, example_en,
               CASE WHEN level IN ('A1', 'A2') THEN level ELSE topic END AS level,
               CASE WHEN level IN ('A1', 'A2') THEN topic ELSE level END AS topic
        FROM vocabulary
        WHERE 1=1
    """
    args = []
    if query:
        sql += " AND (german LIKE ? OR english LIKE ?)"
        args.extend([f"%{query}%", f"%{query}%"])
    if level:
        sql += " AND (CASE WHEN level IN ('A1', 'A2') THEN level ELSE topic END) = ?"
        args.append(level)
    if topic:
        sql += " AND (CASE WHEN level IN ('A1', 'A2') THEN topic ELSE level END) = ?"
        args.append(topic)
    sql += " ORDER BY id LIMIT 60"
    result = [dict(row) for row in execute(conn, sql, args).fetchall()]
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
    if execute(conn, "SELECT 1 FROM vocabulary WHERE id = ?", (vocab_id,)).fetchone() is None:
        conn.close()
        return jsonify(error="unknown vocabulary item"), 404
    execute(conn, "INSERT INTO attempts (vocab_id, correct) VALUES (?, ?)", (vocab_id, int(data["correct"])))
    conn.commit(); conn.close()
    return jsonify(ok=True)

@app.get("/api/mistakes")
def mistakes():
    conn = db()
    rows = execute(conn, """SELECT v.*, COUNT(a.id) AS misses
        FROM vocabulary v JOIN attempts a ON a.vocab_id = v.id
        WHERE a.correct = 0 GROUP BY v.id ORDER BY MAX(a.created_at) DESC LIMIT 30""").fetchall()
    conn.close()
    return jsonify([dict(row) for row in rows])

if __name__ == "__main__":
    seed_database()
    app.run(debug=os.environ.get("FLASK_DEBUG") == "1")
