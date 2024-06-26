import sqlite3

def create_audio_db():
    conn = sqlite3.connect("audio.db")
    c = conn.cursor()

    # Create table
    c.execute('''CREATE TABLE audio (
                 id INTEGER PRIMARY KEY,
                 user_id INTEGER,
                 latin TEXT,
                 aksara TEXT,
                 mode_option TEXT
                 )''')

    conn.commit()
    conn.close()

if __name__ == "__main__":
    create_audio_db()
