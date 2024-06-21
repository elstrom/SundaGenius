import streamlit as st
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM
import sqlite3
import pandas as pd
import torch
import librosa
import io
import soundfile as sf
import re

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

# Fungsi validasi nomor telepon
def validate_phone(phone):
    return phone.isdigit()

# Fungsi validasi password
def validate_password(password):
    if (len(password) >= 8 and
            re.search(r'[A-Z]', password) and
            re.search(r'\d', password) or re.search(r'\W', password)):
        return True
    return False

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

    # ===========================================================
    # ========================= HALAMAN AWAL ====================
    # ===========================================================

    # Fungsi untuk memuat halaman login
    def load_login_page():
        st.title("Login")
        username = st.text_input("Username", key="login_username")
        password = st.text_input("Password", type="password", on_change=handle_enter_key, key="login_password")

        if st.button("Login") or st.session_state.enter_pressed:
            conn = create_connection("users.db")
            df = pd.read_sql_query("SELECT * FROM users WHERE username = ? AND password = ?", conn, params=(username, password))
            if not df.empty:
                st.session_state.user_id = df['id'][0]
                st.session_state.username = df['username'][0]
                st.success("Login berhasil")
                st.session_state.page = "Penerjemah"
                st.session_state.enter_pressed = False
                st.rerun()
            else:
                st.error("Username atau password salah")
                st.session_state.enter_pressed = False

        if st.button("Daftar"):
            st.session_state.page = "Daftar"
            st.rerun()

    # Fungsi untuk memuat halaman daftar
    def load_register_page():
        st.title("Daftar")
        username = st.text_input("Username", key="register_username")
        email = st.text_input("Email", key="register_email")
        phone = st.text_input("Nomor Telepon", key="register_phone")
        password = st.text_input("Password", type="password", key="register_password")
        password_error = None

        if st.button("Daftar"):
            if not validate_phone(phone):
                st.error("Nomor telepon harus berupa angka.")
            elif not validate_password(password):
                st.error("Password harus berisi minimal 8 karakter, termasuk satu huruf besar, dan satu nomor atau simbol.")
            else:
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

    # Halaman login
    if st.session_state.user_id is None:
        if st.session_state.page == "Login":
            load_login_page()
        elif st.session_state.page == "Daftar":
            load_register_page()
        return

    # ===========================================================
    # =============== HALAMAN UTAMA TERJEMAH ====================
    # ===========================================================

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
            st.rerun()

        selected_indices = st.multiselect("Pilih riwayat yang ingin dihapus", df.index)
        if st.button("Hapus Riwayat Terpilih"):
            if selected_indices:
                c = conn.cursor()
                selected_ids = df.loc[selected_indices, 'id'].tolist()
                c.executemany("DELETE FROM translations WHERE id = ?", [(i,) for i in selected_ids])
                conn.commit()
                st.rerun()

        st.button("Kembali", on_click=lambda: st.session_state.update({"nav": None}))

    elif st.session_state.nav == "Profil":
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

        st.button("Kembali", on_click=lambda: st.session_state.update({"nav": None}))

    elif st.session_state.page == "Penerjemah" and st.session_state.nav is None:
        language_option = st.selectbox("Pilih bahasa", ["Aksara_to_Latin", "Latin_to_Aksara"])
        input_text = st.text_area("Input teks", key="translation_input_text")

        if st.button("Submit"):
            if input_text:
                with st.spinner("Memproses..."):
                    tokenizer, model = load_model(language_option)
                    translated_text = predict(input_text, tokenizer, model)
                    st.text_area("Output", translated_text, height=200, key="translation_output_text")

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

    # ===========================================================
    # ================== HALAMAN UTAMA SUARA ====================
    # ===========================================================

    elif st.session_state.page == "Suara":
        col1, col2, col3 = st.columns([1, 4, 1])
        with col1:
            st.button("📋", key="riwayat_suara", on_click=lambda: st.session_state.update({"nav": "Riwayat_suara"}))
        with col2:
            st.markdown("<h1 style='text-align: center; padding-top: 0;'>Mesin Deteksi Suara</h1>", unsafe_allow_html=True)
        with col3:
            st.button("👤", key="profil", on_click=lambda: st.session_state.update({"nav": "Profil"}))

        # Tombol untuk upload audio dan submit dalam satu baris
        col1, col2 = st.columns([3, 1])
        with col1:
            audio_file = st.file_uploader("Pilih audio", type=["mp3", "wav"], label_visibility="collapsed")
        with col2:
            submit_button = st.button("Submit")

        # Proses audio jika diupload
        if audio_file:
            audio_bytes = audio_file.read()
            st.audio(audio_bytes, format="audio/wav")

            # Memproses audio untuk deteksi suara
            if submit_button:
                from transformers import AutoProcessor, AutoModelForCTC
                processor = AutoProcessor.from_pretrained("ElStrom/STT", token=HUGGINGFACE_TOKEN)
                model = AutoModelForCTC.from_pretrained("ElStrom/STT", token=HUGGINGFACE_TOKEN)

                # Menggunakan soundfile untuk memuat file audio dari byte stream
                audio_data, sample_rate = sf.read(io.BytesIO(audio_bytes))

                inputs = processor(audio_data, sampling_rate=sample_rate, return_tensors="pt", padding=True)
                with st.spinner("Memproses..."):
                    logits = model(**inputs).logits
                    predicted_ids = torch.argmax(logits, dim=-1)
                    transcription = processor.batch_decode(predicted_ids)
                    output_latin = transcription[0]

                    # Menampilkan hasil prediksi di output_latin
                    st.session_state.output_latin = output_latin

                    # Model untuk menerjemahkan dari Latin ke Aksara
                    model_terjemahan = AutoModelForSeq2SeqLM.from_pretrained("ElStrom/Latin_to_Aksara", token=HUGGINGFACE_TOKEN)
                    tokenizer_terjemahan = AutoTokenizer.from_pretrained("ElStrom/Latin_to_Aksara", token=HUGGINGFACE_TOKEN)

                    inputs_terjemahan = tokenizer_terjemahan(output_latin, return_tensors="pt", padding=True)
                    outputs_terjemahan = model_terjemahan.generate(**inputs_terjemahan)
                    output_aksara = tokenizer_terjemahan.batch_decode(outputs_terjemahan, skip_special_tokens=True)[0]

                    # Menampilkan hasil terjemahan di output_aksara
                    st.session_state.output_aksara = output_aksara

        col1, col2 = st.columns(2)
        with col1:
            st.markdown("<h3 style='text-align: center;'>Output Latin</h3>", unsafe_allow_html=True)
            st.text_area("Output Latin", st.session_state.get("output_latin", ""), height=200, key="output_latin", label_visibility="collapsed")

        with col2:
            st.markdown("<h3 style='text-align: center;'>Output Aksara</h3>", unsafe_allow_html=True)
            st.text_area("Output Aksara", st.session_state.get("output_aksara", ""), height=200, key="output_aksara", label_visibility="collapsed")

        st.button("Kembali", on_click=lambda: st.session_state.update({"nav": None}))

    elif st.session_state.nav == "Riwayat_suara":
        st.session_state.page = None  # Menghilangkan halaman sebelumnya
        st.title("Riwayat Deteksi Suara")
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

        st.button("Kembali", on_click=lambda: st.session_state.update({"nav": None}))
        
if __name__ == "__main__":
    main()
