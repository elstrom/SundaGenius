import streamlit as st
import sqlite3
import pandas as pd
import subprocess
from datetime import datetime

def create_connection(db_file):
    conn = sqlite3.connect(db_file)
    return conn

# Fungsi untuk melakukan commit ke GitHub
def git_commit(file_path):
    try:
        today = datetime.today().strftime('%Y-%m-%d')
        commit_message = today
        subprocess.run(["git", "add", file_path], check=True)
        subprocess.run(["git", "commit", "-m", commit_message], check=True)
        subprocess.run(["git", "push"], check=True)
    except subprocess.CalledProcessError as e:
        st.error(f"Error during git operation: {e}")

def main():
    st.page_link("app.py", label=":blue[Kembali]", icon="🔙")
    st.title("Riwayat Suara")
    conn = create_connection("audio.db")
    user_id = st.session_state.user_id
    df = pd.read_sql_query("SELECT id, latin, aksara, mode_option FROM audio WHERE user_id = ?", conn, params=(user_id,))
    st.dataframe(df.drop(columns=["id"]))
    if st.button("Hapus Semua Riwayat"):
            c = conn.cursor()
            c.execute("DELETE FROM audio WHERE user_id = ?", (user_id,))
            conn.commit()
            conn.close()

            # Commit to GitHub
            git_commit("audio.db")

            st.rerun()

    selected_indices = st.multiselect("Pilih riwayat yang ingin dihapus", df.index)
    if st.button("Hapus Riwayat Terpilih"):
            if selected_indices:
                c = conn.cursor()
                selected_ids = df.loc[selected_indices, 'id'].tolist()
                c.executemany("DELETE FROM audio WHERE id = ?", [(i,) for i in selected_ids])
                conn.commit()
                conn.close()

                # Commit to GitHub
                git_commit("audio.db")

                st.rerun()        

if __name__ == "__main__":
    main()
