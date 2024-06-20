import sqlite3
import pandas as pd

# Fungsi untuk menghubungkan ke database SQLite
def create_connection(db_file):
    conn = sqlite3.connect(db_file)
    return conn

# Fungsi untuk menampilkan semua data dari tabel users
def show_all_users():
    conn = create_connection("users.db")
    df = pd.read_sql_query("SELECT * FROM users", conn)
    conn.close()
    return df

# Tampilkan semua data dari tabel users
if __name__ == '__main__':
    df_users = show_all_users()
    print(df_users)
