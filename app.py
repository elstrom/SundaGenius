import streamlit as st
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM
import sqlite3
import pandas as pd

# Token API Hugging Face
HUGGINGFACE_TOKEN = "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"

# Fungsi untuk memuat model berdasarkan pilihan bahasa
def load_model(language_option):
    if language_option == "Aksara_to_Latin":
        tokenizer = AutoTokenizer.from_pretrained("ElStrom/Aksara_to_Latin", token=HUGGINGFACE_TOKEN)
        model = AutoModelForSeq2SeqLM.from_pretrained("ElStrom/Aksara_to_Latin", token=HUGGINGFACE_TOKEN)
    else:
        tokenizer = AutoTokenizer.from_pretrained("ElStrom/Latin_to_Aksara", token=HUGGINGFACE_TOKEN)
        model = AutoModelForSeq2SeqLM.from_pretrained("ElStrom/Latin_to_Aksara", token=HUGGINGFACE_TOKEN)
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

# Fungsi utama Streamlit
def main():
    st.set_page_config(page_title="Mesin Penerjemahan", layout="wide")

    if 'user_id' not in st.session_state:
        st.session_state.user_id = None

    if 'page' not in st.session_state:
        st.session_state.page = "Login"

    if 'enter_pressed' not in st.session_state:
        st.session_state.enter_pressed = False

    def handle_enter_key():
        st.session_state.enter_pressed = True

    # Fungsi untuk memuat halaman login
    def load_login_page():
        st.title("Login")
        username = st.text_input("Username")
        password = st.text_input("Password", type="password", on_change=handle_enter_key)

        if st.button("Login") or st.session_state.enter_pressed:
            conn = create_connection("users.db")
            df = pd.read_sql_query("SELECT * FROM users WHERE username = ? AND password = ?", conn, params=(username, password))
            if not df.empty:
                st.session_state.user_id = df['id'][0]
                st.session_state.username = df['username'][0]
                st.success("Login berhasil")
                st.session_state.page = "Penerjemah"
                st.session_state.enter_pressed = False
                st.experimental_rerun()
            else:
                st.error("Username atau password salah")
                st.session_state.enter_pressed = False

        if st.button("Daftar"):
            st.session_state.page = "Daftar"
            st.experimental_rerun()

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
            st.experimental_rerun()
        if st.button("Kembali"):
            st.session_state.page = "Login"
            st.experimental_rerun()

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

    if menu == "Penerjemah":
        st.session_state.page = "Penerjemah"
    elif menu == "Suara":
        st.session_state.page = "Suara"
    elif menu == "Gambar":
        st.session_state.page = "Gambar"

    # Menangani tombol 📋 dan 👤
    if 'nav' not in st.session_state:
        st.session_state.nav = None

    if st.session_state.page == "Penerjemah" and st.session_state.nav is None:
        col1, col2, col3 = st.columns([1, 4, 1])
        with col1:
            st.button("📋", key="riwayat", on_click=lambda: st.session_state.update({"nav": "Riwayat"}))
        with col2:
            st.markdown("<h1 style='text-align: center;'>Mesin Penerjemahan</h1>", unsafe_allow_html=True)
        with col3:
            st.button("👤", key="profil", on_click=lambda: st.session_state.update({"nav": "Profil"}))

    # Menampilkan halaman berdasarkan pilihan
    if st.session_state.nav == "Riwayat":
        st.title("Riwayat Penerjemahan")
        conn = create_connection("translations.db")
        user_id = st.session_state.user_id  # Use the user ID from session state
        df = pd.read_sql_query("SELECT id, input_text, output_text, language_option FROM translations WHERE user_id = ?", conn, params=(user_id,))
        st.dataframe(df.drop(columns=["id"]))

        if st.button("Hapus Semua Riwayat"):
            c = conn.cursor()
            c.execute("DELETE FROM translations WHERE user_id = ?", (user_id,))
            conn.commit()
            st.experimental_rerun()

        selected_indices = st.multiselect("Pilih riwayat yang ingin dihapus", df.index)
        if st.button("Hapus Riwayat Terpilih"):
            if selected_indices:
                c = conn.cursor()
                selected_ids = df.loc[selected_indices, 'id'].tolist()
                c.executemany("DELETE FROM translations WHERE id = ?", [(i,) for i in selected_ids])
                conn.commit()
                st.experimental_rerun()

        st.button("Kembali", on_click=lambda: st.session_state.update({"nav": None}))

    elif st.session_state.nav == "Profil":
        st.title("Profil Pengguna")
        conn = create_connection("users.db")
        user_id = st.session_state.user_id  # Use the user ID from session state

        # Query untuk mendapatkan data pengguna berdasarkan user_id
        df = pd.read_sql_query("SELECT username, email, phone, password FROM users WHERE id = ?", conn, params=(user_id,))
        
        if not df.empty:
            st.image("default_profile.png", width=150)
            with st.form(key="profile_form"):
                username = st.text_input("Username", df['username'][0])
                email = st.text_input("Email", df['email'][0])
                phone = st.text_input("Nomor Telepon", df['phone'][0])
                password_hidden = st.checkbox("Tampilkan Password")
                if password_hidden:
                    password = st.text_input("Password", df['password'][0])
                else:
                    password = st.text_input("Password", "******", type="password")
                if st.form_submit_button("Simpan Perubahan"):
                    c = conn.cursor()
                    c.execute("UPDATE users SET username = ?, email = ?, phone = ?, password = ? WHERE id = ?",
                              (username, email, phone, password, user_id))
                    conn.commit()
                    st.success("Perubahan disimpan")
            
            if st.button("Keluar"):
                st.session_state.user_id = None
                st.session_state.page = "Login"
                st.experimental_rerun()
        else:
            st.write("Pengguna tidak ditemukan.")
        
        st.button("Kembali", on_click=lambda: st.session_state.update({"nav": None}))

    elif st.session_state.page == "Penerjemah" and st.session_state.nav is None:
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

if __name__ == '__main__':
    main()
