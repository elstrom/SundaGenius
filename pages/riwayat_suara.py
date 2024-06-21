import streamlit as st
import sqlite3
import pandas as pd

def create_connection(db_file):
    conn = sqlite3.connect(db_file)
    return conn

def main():
    st.page_link("app.py", label=":blue[Kembali]", icon="🔙")
    st.title("Riwayat Suara")
    conn = create_connection("audio.db")
    user_id = st.session_state.user_id
    df = pd.read_sql_query("SELECT id, audio_file, detected_text FROM audio WHERE user_id = ?", conn, params=(user_id,))
    st.dataframe(df.drop(columns=["id"]))
    if st.button("Hapus Semua Riwayat"):
          c = conn.cursor()
          c.execute("DELETE FROM audio WHERE user_id = ?", (user_id,))
          conn.commit()
          st.rerun()

    selected_indices = st.multiselect("Pilih riwayat yang ingin dihapus", df.index)
    if st.button("Hapus Riwayat Terpilih"):
            if selected_indices:
                c = conn.cursor()
                selected_ids = df.loc[selected_indices, 'id'].tolist()
                c.executemany("DELETE FROM audio WHERE id = ?", [(i,) for i in selected_ids])
                conn.commit()
                st.rerun()        

if __name__ == "__main__":
    main()