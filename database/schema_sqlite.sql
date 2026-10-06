CREATE TABLE IF NOT EXISTS vocabulary (
    id INTEGER PRIMARY KEY,
    german TEXT NOT NULL,
    english TEXT NOT NULL,
    article TEXT,
    pronunciation TEXT NOT NULL,
    plural TEXT,
    level TEXT NOT NULL,
    topic TEXT NOT NULL,
    example_de TEXT NOT NULL,
    example_en TEXT NOT NULL,
    UNIQUE (german, level, topic)
);
CREATE TABLE IF NOT EXISTS attempts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    vocab_id INTEGER REFERENCES vocabulary(id) ON DELETE CASCADE,
    correct INTEGER NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_vocabulary_level_topic ON vocabulary(level, topic);
CREATE INDEX IF NOT EXISTS idx_attempts_vocab ON attempts(vocab_id);
