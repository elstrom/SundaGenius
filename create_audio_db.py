import sqlite3

def create_audio_db():
    conn = sqlite3.connect("audio.db")
    c = conn.cursor()

    # Create table
    c.execute('''CREATE TABLE IF NOT EXISTS audio (
                 id INTEGER PRIMARY KEY,
                 user_id INTEGER,
                 audio_file TEXT,
                 detected_text TEXT
                 )''')

    conn.commit()
    conn.close()

if __name__ == "__main__":
    create_audio_db()
