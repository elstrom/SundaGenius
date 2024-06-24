import streamlit as st
from transformers import AutoTokenizer, AutoModelForVision2Seq, AutoModelForSeq2SeqLM, AutoProcessor, AutoModelForCTC, VitsModel
import sqlite3
import librosa
import pandas as pd
import torch
import soundfile as sf
import io
import re
from PIL import Image

import numpy as np

# Token API Hugging Face
HUGGINGFACE_TOKEN = "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"

# Fungsi untuk memuat model berdasarkan pilihan bahasa
@st.cache_resource
def load_model(language_option):
    if language_option == "Latin_to_Aksara":
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

        language_option = st.selectbox("Pilih bahasa", ["Latin_to_Aksara", "Aksara_to_Latin"])
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

    # Inisialisasi session state untuk tab yang aktif
    if 'active_tab' not in st.session_state:
        st.session_state.active_tab = "Speech To Text"

    # Inisialisasi session state untuk state pemrosesan
    if 'processing' not in st.session_state:
        st.session_state.processing = False

    # Fungsi untuk memuat model dan tokenizer dengan caching
    @st.cache_resource
    def load_stt_model():
        processor = AutoProcessor.from_pretrained("ElStrom/STT", token=HUGGINGFACE_TOKEN)
        model_stt = AutoModelForCTC.from_pretrained("ElStrom/STT", token=HUGGINGFACE_TOKEN)
        return processor, model_stt

    @st.cache_resource
    def load_translation_model():
        tokenizer = AutoTokenizer.from_pretrained("ElStrom/Latin_to_Aksara", token=HUGGINGFACE_TOKEN)
        model_translation = AutoModelForSeq2SeqLM.from_pretrained("ElStrom/Latin_to_Aksara", token=HUGGINGFACE_TOKEN)
        return tokenizer, model_translation

    @st.cache_resource
    def load_tts_model():
        tokenizer = AutoTokenizer.from_pretrained("facebook/mms-tts-sun", token=HUGGINGFACE_TOKEN)
        model_tts = VitsModel.from_pretrained("facebook/mms-tts-sun", token=HUGGINGFACE_TOKEN)
        return tokenizer, model_tts

    # Fungsi untuk mengubah ucapan ke teks
    def speech_to_text(audio):
        processor, model_stt = load_stt_model()
        inputs = processor(audio, sampling_rate=16000, return_tensors="pt", padding=True)
        with torch.no_grad():
            logits = model_stt(**inputs).logits
        predicted_ids = torch.argmax(logits, dim=-1)
        transcription = processor.batch_decode(predicted_ids)[0]
        return transcription.lower()

    # Fungsi untuk menerjemahkan teks
    def translate_text(text):
        tokenizer, model_translation = load_translation_model()
        inputs = tokenizer(text, return_tensors="pt")
        outputs = model_translation.generate(**inputs, max_length=400, do_sample=True, top_k=30, top_p=0.95)
        translated_text = tokenizer.decode(outputs[0], skip_special_tokens=True)
        return translated_text

    # Fungsi untuk mengubah teks ke ucapan
    def text_to_speech(text):
        tokenizer, model_tts = load_tts_model()
        inputs = tokenizer(text, return_tensors="pt", padding=True)
        with torch.no_grad():
            spectrogram = model_tts.generate_speech(inputs["input_ids"], speaker="female", noise_scale=0.3)
        return spectrogram

    # Konversi sample rate
    def convert_sample_rate(audio, orig_sr, target_sr):
        audio = librosa.resample(audio, orig_sr=orig_sr, target_sr=target_sr)
        return audio

    # Halaman Suara
    if st.session_state.page == "Suara" and st.session_state.nav == "Suara":
        st.title("Konversi Suara ke Teks dan Teks ke Suara")
        tabs = ["Speech To Text", "Text To Speech"]
        active_tab = st.radio("Pilih Tab", tabs, index=tabs.index(st.session_state.active_tab))

        if active_tab == "Speech To Text":
            st.session_state.active_tab = "Speech To Text"
            audio_file = st.file_uploader("Upload file audio", type=["wav", "mp3", "m4a"])
            if st.button("Submit"):
                if audio_file:
                    with st.spinner("Memproses..."):
                        audio, sr = librosa.load(audio_file, sr=None)
                        audio = convert_sample_rate(audio, sr, 16000)
                        transcription = speech_to_text(audio)
                        st.success("Transkripsi Selesai")
                        st.text_area("Hasil Transkripsi", transcription, height=200)
                        translation = translate_text(transcription)
                        st.text_area("Hasil Terjemahan", translation, height=200)
                        st.session_state.processing = False
                else:
                    st.warning("Mohon upload file audio")

        elif active_tab == "Text To Speech":
            st.session_state.active_tab = "Text To Speech"
            input_text = st.text_area("Masukkan Teks")
            if st.button("Submit"):
                if input_text:
                    with st.spinner("Memproses..."):
                        audio_output = text_to_speech(input_text)
                        st.audio(audio_output, format="audio/wav")
                        st.session_state.processing = False
                else:
                    st.warning("Mohon masukkan teks")

    # ===========================================================
    # ================== HALAMAN UTAMA GAMBAR ====================
    # ===========================================================

    if st.session_state.page == "Gambar" and st.session_state.nav == "Gambar":
        st.title("Konversi Gambar ke Teks dan Teks ke Gambar")

        # Fungsi untuk memuat model dan processor
        @st.cache_resource
        def load_image_model():
            processor = AutoProcessor.from_pretrained("ElStrom/vision-encoder", token=HUGGINGFACE_TOKEN)
            model = AutoModelForVision2Seq.from_pretrained("ElStrom/vision-encoder", token=HUGGINGFACE_TOKEN)
            return processor, model

        # Fungsi untuk mengubah gambar ke teks
        def image_to_text(image):
            processor, model = load_image_model()
            image = image.resize((224, 224))
            inputs = processor(images=image, return_tensors="pt")
            with torch.no_grad():
                outputs = model.generate(**inputs)
            text = processor.decode(outputs[0], skip_special_tokens=True)
            return text

        # Fungsi untuk mengubah teks ke gambar
        def text_to_image(text):
            processor, model = load_image_model()
            inputs = processor(text, return_tensors="pt")
            with torch.no_grad():
                outputs = model.generate(**inputs)
            generated_image = processor.decode(outputs[0], skip_special_tokens=True)
            return generated_image

        option = st.selectbox("Pilih Konversi", ["Gambar ke Teks", "Teks ke Gambar"])

        if option == "Gambar ke Teks":
            image_file = st.file_uploader("Upload file gambar", type=["jpg", "jpeg", "png"])
            if st.button("Submit"):
                if image_file:
                    with st.spinner("Memproses..."):
                        image = Image.open(image_file)
                        text_output = image_to_text(image)
                        st.text_area("Hasil", text_output, height=200)
                else:
                    st.warning("Mohon upload file gambar")
        else:
            input_text = st.text_area("Masukkan Teks")
            if st.button("Submit"):
                if input_text:
                    with st.spinner("Memproses..."):
                        image_output = text_to_image(input_text)
                        st.image(image_output, caption="Gambar Hasil Konversi")
                else:
                    st.warning("Mohon masukkan teks")

    # Tombol Logout di sidebar
    if st.sidebar.button("Logout"):
        st.session_state.user_id = None
        st.session_state.page = "Login"
        st.sidebar.success("Logout berhasil")
        st.rerun()

if __name__ == "__main__":
    main()
