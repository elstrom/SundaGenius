import streamlit as st
import sqlite3
import pandas as pd

def create_connection(db_file):
    conn = sqlite3.connect(db_file)
    return conn

def validate_phone(phone):
    return phone.isdigit()

def validate_password(password):
    return len(password) >= 8 and any(char.isupper() for char in password) and any(char.isdigit() or not char.isalnum() for char in password)

def main():
    st.write(f"Current page: {st.session_state.page}")
    if st.button("🔙 :violet[Kembali]"):
        st.switch_page("app.py")
    
    st.title("Profil Pengguna")
    conn = create_connection("users.db")
    
    user_id = st.session_state.user_id  # Gunakan ID pengguna dari session state

    # Pastikan user_id adalah integer
    try:
        user_id = int(user_id)
    except ValueError:
        st.write("User ID tidak valid")
        return  # Keluar jika user_id tidak valid

    # Query untuk mendapatkan data pengguna berdasarkan user_id
    query = "SELECT username, email, phone, password FROM users WHERE id = ?"
    df = pd.read_sql_query(query, conn, params=(user_id,))

    if not df.empty:
        st.image("https://upload.wikimedia.org/wikipedia/commons/7/7c/Profile_avatar_placeholder_large.png", width=150)  # Ganti dengan URL gambar profil online
        username = st.text_input("Username", df['username'][0], disabled=True, key="profile_username")
        email = st.text_input("Email", df['email'][0], disabled=True, key="profile_email")
        phone = st.text_input("Nomor Telepon", df['phone'][0], disabled=True, key="profile_phone")
        password_hidden = st.checkbox("Tampilkan Password", key="profile_password_checkbox", disabled=True)
        if password_hidden:
            password = st.text_input("Password", df['password'][0], disabled=True, key="profile_password")
        else:
            password = st.text_input("Password", "******", type="password", disabled=True, key="profile_password_hidden")

        if st.button("Edit Profil"):
            st.session_state.edit_mode = True

        if 'edit_mode' in st.session_state and st.session_state.edit_mode:
            username = st.text_input("Username", df['username'][0], key="edit_profile_username")
            email = st.text_input("Email", df['email'][0], key="edit_profile_email")
            phone = st.text_input("Nomor Telepon", df['phone'][0], key="edit_profile_phone")
            password_hidden = st.checkbox("Tampilkan Password", key="edit_profile_password_checkbox")
            if password_hidden:
                password = st.text_input("Password", df['password'][0], key="edit_profile_password")
            else:
                password = st.text_input("Password", "******", type="password", key="edit_profile_password_hidden")
            
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
                    st.success("Perubahan disimpan")
                    st.session_state.edit_mode = False

        if st.button("Keluar"):
            st.session_state.user_id = None
            st.session_state.page = "Login"
            st.rerun()
    else:
        st.write("Pengguna tidak ditemukan.")

if __name__ == "__main__":
    main()