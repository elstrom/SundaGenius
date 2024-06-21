import streamlit as st
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM, AutoProcessor, AutoModelForCTC
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
def load_model(mode_option):
    if mode_option == "Latin_to_Aksara":
        tokenizer = AutoTokenizer.from_pretrained("ElStrom/Latin_to_Aksara", token=HUGGINGFACE_TOKEN)
        model = AutoModelForSeq2SeqLM.from_pretrained("ElStrom/Latin_to_Aksara", token=HUGGINGFACE_TOKEN)
    else:
        tokenizer = AutoTokenizer.from_pretrained("ElStrom/Aksara_to_Latin", token=HUGGINGFACE_TOKEN)
        model = AutoModelForSeq2SeqLM.from_pretrained("ElStrom/Aksara_to_Latin", token=HUGGINGFACE_TOKEN)
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

    if 'nav' not in st.session_state:
        st.session_state.nav = "Penerjemah"

    if 'enter_pressed' not in st.session_state:
        st.session_state.enter_pressed = False

    def handle_enter_key():
        st.session_state.enter_pressed = True

    st.write(f"Current page: {st.session_state.page}")
    st.write(f"Current nav: {st.session_state.nav}")

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
                st.session_state.nav == "Penerjemah"
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
    
    # Sidebar menu
    st.sidebar.title("Menu")
    if st.sidebar.button("📚 Penerjemah"):
        st.session_state.page = "Penerjemah"
        st.session_state.nav = "Penerjemah"
    if st.sidebar.button("🎙️ Suara"):
        st.session_state.page = "Suara"
        st.session_state.nav = "Suara"
    if st.sidebar.button("📸 Gambar"):
        st.session_state.page = "Gambar"
        st.session_state.nav = "Gambar"

    # ===========================================================
    # =============== HALAMAN UTAMA TERJEMAH ====================
    # ===========================================================

    if st.session_state.page == "Penerjemah" and st.session_state.nav == "Penerjemah":
        col1, col2, col3 = st.columns([0.7, 0.2, 0.2])
        with col1:
            st.write('')
        with col2:
            st.page_link("pages/riwayat_penerjemahan.py", label="Riwayat", icon="📋")
        with col3:
            st.page_link("pages/profil.py", label="Profil", icon="👤")
        st.markdown("<h1 style='text-align: center; padding: 40px'>Mesin Penerjemahan</h1>", unsafe_allow_html=True)

        mode_option = st.selectbox("Pilih bahasa", ["Aksara To Latin", "Latin To Aksara"])
        input_text = st.text_area("Input teks", key="translation_input_text")

        if st.button("Submit"):
            if input_text:
                with st.spinner("Memproses..."):
                    tokenizer, model = load_model(mode_option)
                    translated_text = predict(input_text, tokenizer, model)
                    st.text_area("Output", translated_text, height=200, key="translation_output_text")

                    # Simpan ke database
                    conn = create_connection('translations.db')
                    c = conn.cursor()
                    user_id = st.session_state.user_id  # Gunakan ID pengguna dari session state
                    c.execute("INSERT INTO translations (input_text, output_text, mode_option, user_id) VALUES (?, ?, ?, ?)", 
                            (input_text, translated_text, mode_option, user_id))
                    conn.commit()
                    conn.close()
            else:
                st.warning("Mohon masukkan teks untuk diterjemahkan")

    # ===========================================================
    # ================== HALAMAN UTAMA SUARA ====================
    # ===========================================================

    elif st.session_state.page == "Suara" and st.session_state.nav == "Suara":
        col1, col2, col3 = st.columns([0.7, 0.2, 0.2])
        with col1:
            st.write('')
        with col2:
            st.page_link("pages/riwayat_suara.py", label="Riwayat", icon="📋")
        with col3:
            st.page_link("pages/profil.py", label="Profil", icon="👤")

        st.markdown("<h1 style='text-align: center; padding: 40px'>Mesin Deteksi Suara</h1>", unsafe_allow_html=True)
        mode_option = st.selectbox("Pilih bahasa", ["Speech To Text", "Text To Speech"], key="mode_option")

        if mode_option == "Speech To Text":
            # Tombol untuk upload audio dan submit
            audio_file = st.file_uploader("Pilih audio", type=["mp3", "wav"], label_visibility="collapsed")
            submit_button = st.button("Submit")

            # Proses audio jika diupload
            if audio_file:
                audio_bytes = audio_file.read()
                st.audio(audio_bytes, format="audio/wav")

                # Memproses audio untuk deteksi suara
                if submit_button:
                    # Model untuk STT
                    processor = AutoProcessor.from_pretrained("ElStrom/STT", token=HUGGINGFACE_TOKEN)
                    model_stt = AutoModelForCTC.from_pretrained("ElStrom/STT", token=HUGGINGFACE_TOKEN)

                    # Menggunakan soundfile untuk memuat file audio dari byte stream
                    audio_data, sample_rate = sf.read(io.BytesIO(audio_bytes))

                    inputs = processor(audio_data, sampling_rate=sample_rate, return_tensors="pt", padding=True)
                    with st.spinner("Memproses..."):
                        logits = model_stt(**inputs).logits
                        predicted_ids = torch.argmax(logits, dim=-1)
                        transcription = processor.batch_decode(predicted_ids)
                        output_latin = transcription[0]

                        # Menampilkan hasil prediksi di output_latin
                        st.session_state.latin = output_latin

                        # Memuat model untuk penerjemahan Latin ke Aksara
                        tokenizer, model_translation = load_model("Latin_to_Aksara")
                        
                        inputs_terjemahan = tokenizer(output_latin, return_tensors="pt", padding=True)
                        outputs_terjemahan = model_translation.generate(**inputs_terjemahan, max_new_tokens=50)
                        output_aksara = tokenizer.batch_decode(outputs_terjemahan, skip_special_tokens=True)[0]

                        # Menampilkan hasil terjemahan di output_aksara
                        st.session_state.aksara = output_aksara

            col1, col2 = st.columns(2)
            with col1:
                st.markdown("<h3 style='text-align: center;'>Output Latin</h3>", unsafe_allow_html=True)
                if "output_latin" not in st.session_state:
                    st.session_state.latin = ""
                st.text_area("Output Latin", st.session_state.latin, height=200, key="output_latin", label_visibility="collapsed")

            with col2:
                st.markdown("<h3 style='text-align: center;'>Output Aksara</h3>", unsafe_allow_html=True)
                if "output_aksara" not in st.session_state:
                    st.session_state.aksara = ""
                st.text_area("Output Aksara", st.session_state.aksara, height=200, key="output_aksara", label_visibility="collapsed")

        elif mode_option == "Text To Speech":
            st.session_state.page = "TextToSpeech"
            st.session_state.nav = "TextToSpeech"

    elif st.session_state.page == "TextToSpeech" and st.session_state.nav == "TextToSpeech":
        st.markdown("<h1 style='text-align: center; padding: 40px'>Text To Speech</h1>", unsafe_allow_html=True)

        teks_input = st.text_area("Masukkan teks di sini", height=200)

        submit_button = st.button("Submit")

        if submit_button and teks_input:
            # Model untuk TTS
            tokenizer = AutoTokenizer.from_pretrained("facebook/mms-tts-sun")
            model = VitsModel.from_pretrained("facebook/mms-tts-sun")

            inputs = tokenizer(teks_input, return_tensors="pt")

            with torch.no_grad():
                output = model(**inputs).waveform

            # Tampilkan audio yang dapat diputar oleh user
            st.audio(output.numpy(), format="audio/wav")

        if st.button("Kembali"):
            st.session_state.page = "Suara"
            st.session_state.nav = "Suara"
        
if __name__ == "__main__":
    main()
