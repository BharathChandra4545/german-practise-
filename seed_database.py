"""Idempotently seed topics, vocabulary, and listening questions."""
from database import connect, is_postgres, placeholder_sql
from content import A1_TOPICS, A2_TOPICS, SEEDS


def execute(connection, sql, params=()):
    return connection.execute(placeholder_sql(sql), params)


def seed():
    from init_db import main as init_db
    lock_connection = None
    if is_postgres():
        lock_connection = connect()
        execute(lock_connection, "SELECT pg_advisory_lock(?)", (917204,))
    init_db()
    connection = connect()
    try:
        topics = [(name, "A1") for name in A1_TOPICS] + [(name, "A2") for name in A2_TOPICS]
        for name, level in topics:
            if is_postgres():
                execute(connection, """
                    INSERT INTO topics (name, level) VALUES (?, ?)
                    ON CONFLICT (name, level) DO NOTHING
                """, (name, level))

        rows = []
        for topic_index, (level, topic) in enumerate(topics):
            for item in range(50):
                seed = SEEDS[(topic_index * 50 + item) % len(SEEDS)]
                german, english, article, pronunciation, plural, example_de, example_en = seed
                suffix = "" if item == 0 else f" · {item + 1}"
                rows.append((german + suffix, english, article, pronunciation, plural,
                             level, topic, example_de, example_en))

        for row in rows:
            sql = """
                INSERT INTO vocabulary
                    (german, english, article, pronunciation, plural, level, topic, example_de, example_en)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT (german, level, topic) DO NOTHING
            """
            if not is_postgres():
                sql = sql.replace("INSERT INTO", "INSERT OR IGNORE INTO")
                sql = sql.replace("ON CONFLICT (german, level, topic) DO NOTHING", "")
            execute(connection, sql, row)

        if is_postgres():
            for row in rows:
                execute(connection, """
                    INSERT INTO words
                        (german, english, article, pronunciation, plural, level, topic, example_de, example_en)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ON CONFLICT (german, level, topic) DO NOTHING
                """, row)

            for level, topic in topics:
                execute(connection, """
                    INSERT INTO listening_questions
                        (level, topic, german, english, option_a, option_b, option_c, option_d, correct_option)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ON CONFLICT (level, german) DO NOTHING
                """, (level, topic, "Ich gehe zur Schule.", "I go to school.",
                      "I go to school.", "I go to work.", "I go home.", "I go to the station.", "A"))
        connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()
        if lock_connection is not None:
            lock_connection.close()
    print("Seed complete: 2,000 vocabulary rows, 40 topics, listening questions.")


if __name__ == "__main__":
    seed()
