import streamlit as st
import sqlite3
import pandas as pd
import subprocess
from datetime import datetime

def create_connection(db_file):
    conn = sqlite3.connect(db_file)
    return conn

def validate_phone(phone):
    return phone.isdigit()

def validate_password(password):
    return len(password) >= 8 and any(char.isupper() for char in password) and any(char.isdigit() or not char.isalnum() for char in password)

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
    st.title("Profil Pengguna")
    conn = create_connection("users.db")
    
    user_id = st.session_state.get('user_id', None)  # Gunakan ID pengguna dari session state

    # Pastikan user_id adalah string
    user_id = str(user_id) if user_id else None
    
    # Pastikan user_id adalah integer
    try:
        user_id = int(user_id)
    except (ValueError, TypeError):
        st.write("User ID tidak valid")
        if st.button("🔑 :blue[Login]"):
            st.switch_page("app.py")
        return  # Keluar jika user_id tidak valid

    st.write(f"Current page: {st.session_state.page}")
    if st.button("🔙 :violet[Kembali]"):
        st.switch_page("app.py")
    
    # Query untuk mendapatkan data pengguna berdasarkan user_id
    query = "SELECT username, email, phone, password FROM users WHERE id = ?"
    df = pd.read_sql_query(query, conn, params=(user_id,))

    if not df.empty:
        st.image("https://upload.wikimedia.org/wikipedia/commons/7/7c/Profile_avatar_placeholder_large.png", width=150)  # Ganti dengan URL gambar profil online
        username = st.text_input("Username", df['username'][0], disabled=True, key="profile_username")
        email = st.text_input("Email", df['email'][0], disabled=True, key="profile_email")
        phone = st.text_input("Nomor Telepon", df['phone'][0], disabled=True, key="profile_phone")
        password = st.text_input("Password", df['password'][0], type="password", disabled=True, key="profile_password")

        if st.button("Edit Profil"):
            st.session_state.edit_mode = True

        if 'edit_mode' in st.session_state and st.session_state.edit_mode:
            username = st.text_input("Username", df['username'][0], key="edit_profile_username")
            email = st.text_input("Email", df['email'][0], key="edit_profile_email")
            phone = st.text_input("Nomor Telepon", df['phone'][0], key="edit_profile_phone")
            password = st.text_input("Password", df['password'][0], type="password", key="edit_profile_password")
            
            if st.button("Konfirmasi"):
                if not validate_phone(phone):
                    st.error("Nomor telepon harus berupa angka.")
                elif not validate_password(password):
                    st.error("Password harus berisi minimal 8 karakter, termasuk satu huruf besar, dan satu nomor atau simbol.")
                else:
                    c = conn.cursor()
                    c.execute("UPDATE users SET username = ?, email = ?, phone = ?, password = ? WHERE id = ?",
                              (username, email, phone, password, user_id))
                    conn.commit()
                    conn.close()

                    # Commit to GitHub
                    git_commit("users.db")

                    st.success("Perubahan disimpan")
                    st.session_state.edit_mode = False
                    st.rerun()

        if st.button("Keluar"):
            st.session_state.user_id = None
            st.session_state.page = "Login"
            st.experimental_rerun()
    else:
        st.write("Pengguna tidak ditemukan.")

if __name__ == "__main__":
    main()
