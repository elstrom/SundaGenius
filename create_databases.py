import sqlite3

# Membuat database untuk riwayat terjemahan
conn = sqlite3.connect('translations.db')
c = conn.cursor()
c.execute('''CREATE TABLE translations
             (id INTEGER PRIMARY KEY, input_text TEXT, output_text TEXT, language_option TEXT, user_id INTEGER)''')
conn.commit()
conn.close()

# Membuat database untuk pengguna
conn = sqlite3.connect('users.db')
c = conn.cursor()
c.execute('''CREATE TABLE users
             (id INTEGER PRIMARY KEY, username TEXT, email TEXT, phone TEXT, password TEXT)''')
conn.commit()
conn.close()
