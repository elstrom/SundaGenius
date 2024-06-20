import streamlit as st
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM
import sqlite3
import pandas as pd

# Token API Hugging Face
HUGGINGFACE_TOKEN = "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"

# Fungsi untuk memuat model berdasarkan pilihan bahasa
def load_model(language_option):
    if language_option == "Aksara_to_Latin":
        tokenizer = AutoTokenizer.from_pretrained("ElStrom/Aksara_to_Latin", use_auth_token=HUGGINGFACE_TOKEN)
        model = AutoModelForSeq2SeqLM.from_pretrained("ElStrom/Aksara_to_Latin", use_auth_token=HUGGINGFACE_TOKEN)
    else:
        tokenizer = AutoTokenizer.from_pretrained("ElStrom/Latin_to_Aksara", use_auth_token=HUGGINGFACE_TOKEN)
        model = AutoModelForSeq2SeqLM.from_pretrained("ElStrom/Latin_to_Aksara", use_auth_token=HUGGINGFACE_TOKEN)
    return tokenizer, model

# Fungsi untuk melakukan prediksi
def predict(input_text, tokenizer, model):
    inputs = tokenizer(input_text, return_tensors="pt")
    outputs = model.generate(**inputs, max_length=400, do_sample=True, top_k=30, top_p=0.95)
    translated_text = tokenizer.decode(outputs[0], skip_special_tokens=True)
    return translated_text

# Fungsi untuk menghubungkan ke database SQLite
def create_connection(db_file):
    conn = sqlite3.connect(db_file)
    return conn

# Fungsi untuk memuat halaman login
def load_login_page():
    st.title("Login")
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")
    if st.button("Login"):
        conn = create_connection("users.db")
        df = pd.read_sql_query("SELECT * FROM users WHERE username = ? AND password = ?", conn, params=(username, password))
        if not df.empty:
            st.session_state.user_id = df['id'][0]
            st.session_state.username = df['username'][0]
            st.success("Login berhasil")
            st.rerun()
        else:
            st.error("Username atau password salah")
    if st.button("Daftar"):
        st.session_state.page = "Daftar"
        st.rerun()

# Fungsi untuk memuat halaman daftar
def load_register_page():
    st.title("Daftar")
    username = st.text_input("Username")
    email = st.text_input("Email")
    phone = st.text_input("Nomor Telepon")
    password = st.text_input("Password", type="password")
    if st.button("Daftar"):
        conn = create_connection("users.db")
        c = conn.cursor()
        c.execute("INSERT INTO users (username, email, phone, password) VALUES (?, ?, ?, ?)", (username, email, phone, password))
        conn.commit()
        conn.close()
        st.success("Pendaftaran berhasil")
        st.session_state.page = "Login"
        st.rerun()
    if st.button("Kembali"):
        st.session_state.page = "Login"
        st.rerun()

# Fungsi utama Streamlit
def main():
    st.set_page_config(page_title="Mesin Penerjemahan", layout="wide")

    if 'user_id' not in st.session_state:
        st.session_state.user_id = None

    if 'page' not in st.session_state:
        st.session_state.page = "Login"

    # Halaman login
    if st.session_state.user_id is None:
        if st.session_state.page == "Login":
            load_login_page()
        elif st.session_state.page == "Daftar":
            load_register_page()
        return

    # Sidebar menu
    st.sidebar.title("Menu")
    menu = st.sidebar.radio("Pilih Halaman", ["Penerjemah", "Suara", "Gambar"])

    # Pengaturan halaman utama
    if menu == "Penerjemah":
        st.session_state.page = "Penerjemah"
    elif menu == "Suara":
        st.session_state.page = "Suara"
    elif menu == "Gambar":
        st.session_state.page = "Gambar"

    if st.session_state.page == "Penerjemah":
        cols = st.columns([1, 2, 1])
        with cols[0]:
            if st.button("📋"):
                st.session_state.page = "Riwayat"
                st.rerun()
        with cols[1]:
            st.title("Mesin Penerjemahan")
        with cols[2]:
            if st.button("👤"):
                st.session_state.page = "Akun Pengguna"
                st.rerun()

        language_option = st.selectbox("Pilih bahasa", ["Aksara_to_Latin", "Latin_to_Aksara"])
        input_text = st.text_area("Input teks")

        if st.button("Submit"):
            if input_text:
                with st.spinner("Memproses..."):
                    tokenizer, model = load_model(language_option)
                    translated_text = predict(input_text, tokenizer, model)
                    st.text_area("Output", translated_text, height=200)

                    # Simpan ke database
                    conn = create_connection('translations.db')
                    c = conn.cursor()
                    user_id = st.session_state.user_id  # Gunakan ID pengguna dari session state
                    c.execute("INSERT INTO translations (input_text, output_text, language_option, user_id) VALUES (?, ?, ?, ?)", 
                              (input_text, translated_text, language_option, user_id))
                    conn.commit()
                    conn.close()
            else:
                st.warning("Mohon masukkan teks untuk diterjemahkan")

    elif st.session_state.page == "Riwayat":
        st.title("Riwayat Penerjemahan")
        conn = create_connection("translations.db")
        user_id = st.session_state.user_id  # Gunakan ID pengguna dari session state
        df = pd.read_sql_query("SELECT id, input_text, output_text, language_option FROM translations WHERE user_id = ?", conn, params=(user_id,))
        st.dataframe(df.drop(columns=["id", "user_id"]))

        if st.button("Hapus Semua Riwayat"):
            c = conn.cursor()
            c.execute("DELETE FROM translations WHERE user_id = ?", (user_id,))
            conn.commit()
            st.rerun()

        selected_indices = st.multiselect("Pilih riwayat yang ingin dihapus", df.index)
        if st.button("Hapus Riwayat Terpilih"):
            c = conn.cursor()
            for i in selected_indices:
                c.execute("DELETE FROM translations WHERE id = ?", (df['id'][i],))
            conn.commit()
            st.rerun()

        if st.button("Kembali"):
            st.session_state.page = "Penerjemah"
            st.rerun()

    elif st.session_state.page == "Akun Pengguna":
        st.title("Profil Pengguna")
        conn = create_connection("users.db")
        user_id = st.session_state.user_id  # Gunakan ID pengguna dari session state
        df = pd.read_sql_query("SELECT username, email, phone, password FROM users WHERE id = ?", conn, params=(user_id,))
        if not df.empty:
            st.image("default_profile.png", width=150)
            st.write(f"Username: {df['username'][0]}")
            st.write(f"Email: {df['email'][0]}")
            st.write(f"Nomor Telepon: {df['phone'][0]}")
            password_hidden = st.checkbox("Tampilkan Password")
            if password_hidden:
                st.write(f"Password: {df['password'][0]}")
            else:
                st.write("Password: ******")
            if st.button("Edit Profil"):
                st.session_state.page = "Edit Profil"
                st.rerun()
        else:
            st.write("Pengguna tidak ditemukan.")

        if st.button("Kembali"):
            st.session_state.page = "Penerjemah"
            st.rerun()

    elif st.session_state.page == "Edit Profil":
        st.title("Edit Profil")
        conn = create_connection("users.db")
        user_id = st.session_state.user_id  # Gunakan ID pengguna dari session state
        df = pd.read_sql_query("SELECT username, email, phone, password FROM users WHERE id = ?", conn, params=(user_id,))
        if not df.empty:
            username = st.text_input("Username", value=df['username'][0])
            email = st.text_input("Email", value=df['email'][0])
            phone = st.text_input("Nomor Telepon", value=df['phone'][0])
            password = st.text_input("Password", value=df['password'][0], type="password")
            if st.button("Simpan"):
                c = conn.cursor()
                c.execute("UPDATE users SET username = ?, email = ?, phone = ?, password = ? WHERE id = ?", 
                          (username, email, phone, password, user_id))
                conn.commit()
                st.success("Profil berhasil diperbarui")
                st.session_state.page = "Akun Pengguna"
                st.rerun()
        else:
            st.write("Pengguna tidak ditemukan.")
        
        if st.button("Kembali"):
            st.session_state.page = "Akun Pengguna"
            st.rerun()

if __name__ == '__main__':
    main()
