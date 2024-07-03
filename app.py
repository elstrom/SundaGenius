import streamlit as st
from transformers import AutoTokenizer, AutoModelForVision2Seq, AutoModelForSeq2SeqLM, AutoProcessor, AutoModelForCTC, VitsModel
import sqlite3
import librosa
import pandas as pd
import torch
import soundfile as sf
import io
import re

import numpy as np
import subprocess
import logging
from datetime import datetime

# Token API Hugging Face
HUGGINGFACE_TOKEN = "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"

# Fungsi untuk memuat model berdasarkan pilihan bahasa
@st.cache_resource
def load_model(language_option):
    if language_option == "Latin_to_Aksara":
        tokenizer_PLTA = AutoTokenizer.from_pretrained("ElStrom/Latin_to_Aksara", token=HUGGINGFACE_TOKEN)
        model_PLTA = AutoModelForSeq2SeqLM.from_pretrained("ElStrom/Latin_to_Aksara", token=HUGGINGFACE_TOKEN)
        return tokenizer_PLTA, model_PLTA
    else:
        tokenizer_PATL = AutoTokenizer.from_pretrained("ElStrom/Aksara_to_Latin", token=HUGGINGFACE_TOKEN)
        model_PATL = AutoModelForSeq2SeqLM.from_pretrained("ElStrom/Aksara_to_Latin", token=HUGGINGFACE_TOKEN)
        return tokenizer_PATL, model_PATL

# Fungsi untuk melakukan prediksi
def predict(input_text, tokenizer, model):
    try:
        inputs = tokenizer(input_text, return_tensors="pt")
        outputs = model.generate(**inputs, max_length=400, do_sample=True, top_k=30, top_p=0.95)
        translated_text = tokenizer.decode(outputs[0], skip_special_tokens=True)
        return translated_text
    finally:
        # Bersihkan cache setelah penggunaan model dan tokenizer
        del tokenizer
        del model
        torch.cuda.empty_cache()

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


def git_commit(file_path):
    try:
        # Inisialisasi repository Git
        subprocess.run(["git", "init"], check=True)
        
        # Konfigurasi detail pengguna
        subprocess.run(["git", "config", "user.name", "ramdan"], check=True)
        subprocess.run(["git", "config", "user.email", "danram162@gmail.com"], check=True)
        
        # Tambahkan remote origin jika belum ada
        result_remote = subprocess.run(["git", "remote"], capture_output=True, text=True)
        if "origin" not in result_remote.stdout:
            subprocess.run(["git", "remote", "add", "origin", "https://github.com/elstrom/SundaGenius"], check=True)
        else:
            subprocess.run(["git", "remote", "set-url", "origin", "https://github.com/elstrom/SundaGenius"], check=True)

        # Tambahkan file, commit, dan push perubahan
        today = datetime.today().strftime('%Y-%m-%d')
        commit_message = today
        result_add = subprocess.run(["git", "add", file_path], check=True, capture_output=True, text=True)
        st.write(result_add.stdout)
        result_commit = subprocess.run(["git", "commit", "-m", commit_message], check=True, capture_output=True, text=True)
        st.write(result_commit.stdout)
        result_push = subprocess.run(["git", "push", "-u", "origin", "main"], check=True, capture_output=True, text=True)
        st.write(result_push.stdout)
    except subprocess.CalledProcessError as e:
        logging.error(f"Error during git operation: {e.stderr}")
        st.error(f"Error during git operation: {e.stderr}")

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

    if 'submit_penerjemah' not in st.session_state:
        st.session_state.submit_penerjemah = False

    def handle_submit_button():
        st.session_state.submit_penerjemah = True

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
                
                # Commit to GitHub
                git_commit("users.db")

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

        if st.button("Submit", on_click=handle_submit_button) or st.session_state.submit_penerjemah:
            st.session_state.submit_penerjemah = False
            if input_text:
                # Add whitespace in front of the input text if language_option is "Aksara_to_Latin"
                if language_option == "Aksara_to_Latin":
                    input_text = " " + input_text

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
                    
                    # Commit to GitHub
                    git_commit("translations.db")
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
        processor_stt = AutoProcessor.from_pretrained("ElStrom/STT", token=HUGGINGFACE_TOKEN)
        model_stt = AutoModelForCTC.from_pretrained("ElStrom/STT", token=HUGGINGFACE_TOKEN)
        return processor_stt, model_stt

    @st.cache_resource
    def load_tts_model():
        tokenizer_tts = AutoTokenizer.from_pretrained("facebook/mms-tts-sun", token=HUGGINGFACE_TOKEN)
        model_tts = VitsModel.from_pretrained("facebook/mms-tts-sun", token=HUGGINGFACE_TOKEN)
        return tokenizer_tts, model_tts

    # Konten halaman utama
    if st.session_state.page == "Suara" and st.session_state.nav == "Suara":
        col1, col2, col3 = st.columns([0.7, 0.2, 0.2])
        with col1:
            st.write('')
        with col2:
            st.page_link("pages/riwayat_suara.py", label="Riwayat", icon="📋")
        with col3:
            st.page_link("pages/profil.py", label="Profil", icon="👤")

        st.markdown("<h1 style='text-align: center; padding: 40px'>Mesin Deteksi Suara</h1>", unsafe_allow_html=True)

        # Gunakan radio button untuk pemilihan tab
        tab_choice = st.radio("Pilih Tab", ["Speech To Text", "Text To Speech"], index=0 if st.session_state.active_tab == "Speech To Text" else 1, key="tab_radio")

        # Update session state pada perubahan tab
        if tab_choice != st.session_state.active_tab:
            st.session_state.active_tab = tab_choice
            st.rerun()  # Memicu rerun untuk memperbarui konten segera

        # Konten untuk tab "Speech To Text"
        if st.session_state.active_tab == "Speech To Text":
            # Upload file audio dan tombol submit
            audio_file = st.file_uploader("Pilih audio", type=["mp3", "wav"], label_visibility="collapsed")
            submit_button = st.button("Submit", key="submit_stt")

            # Proses file audio yang diunggah
            if audio_file:
                audio_bytes = audio_file.read()
                
                try:
                    # Coba membaca file audio untuk memastikan validitasnya
                    audio_data, original_sample_rate = sf.read(io.BytesIO(audio_bytes))
                    st.audio(audio_bytes, format="audio/wav")
                except Exception as e:
                    st.error(f"Error reading audio file: {e}")
                    audio_data, original_sample_rate = None, None

                if audio_data is not None:
                    # Resample audio ke 16000 Hz dan pastikan mono
                    audio_data_mono = librosa.to_mono(audio_data.T) if len(audio_data.shape) > 1 else audio_data
                    audio_data_16k = librosa.resample(audio_data_mono, orig_sr=original_sample_rate, target_sr=16000)

                    # Pemrosesan Speech-to-Text
                    if submit_button:
                        st.session_state.processing = True  # Set processing state to True
                        processor_stt, model_stt = load_stt_model()

                        try:
                            inputs = processor_stt(audio_data_16k, sampling_rate=16000, return_tensors="pt", padding=True)
                            with st.spinner("Memproses..."):
                                logits = model_stt(**inputs).logits
                                predicted_ids = torch.argmax(logits, dim=-1)
                                transcription = processor_stt.batch_decode(predicted_ids)
                                output_latin = transcription[0]

                                st.session_state.latin = output_latin

                                tokenizer_PLTA, model_PLTA = load_model("Latin_to_Aksara")
                                inputs_terjemahan = tokenizer_PLTA(output_latin, return_tensors="pt", padding=True)
                                outputs_terjemahan = model_PLTA.generate(**inputs_terjemahan, max_new_tokens=50)
                                output_aksara = tokenizer_PLTA.batch_decode(outputs_terjemahan, skip_special_tokens=True)[0]

                                st.session_state.aksara = output_aksara

                                conn = create_connection('audio.db')
                                c = conn.cursor()
                                user_id = st.session_state.user_id
                                c.execute("INSERT INTO audio (user_id, latin, aksara, mode_option) VALUES (?, ?, ?, ?)",
                                        (user_id, output_latin, output_aksara, "Speech To Text"))
                                conn.commit()
                                conn.close()

                                # Commit to GitHub
                                git_commit("audio.db")
                        finally:
                            del processor_stt
                            del model_stt
                            torch.cuda.empty_cache()

                        st.session_state.processing = False  # Set processing state to False
                        
                        # Bersihkan cache Streamlit setelah pemrosesan selesai
                        st.cache_data.clear()

            col1, col2 = st.columns(2)
            with col1:
                st.markdown("<h3 style='text-align: center;'>Output Latin</h3>", unsafe_allow_html=True)
                if "latin" not in st.session_state:
                    st.session_state.latin = ""
                st.text_area("Output Latin", st.session_state.latin, height=200, key="output_latin", label_visibility="collapsed")

            with col2:
                st.markdown("<h3 style='text-align: center;'>Output Aksara</h3>", unsafe_allow_html=True)
                if "aksara" not in st.session_state:
                    st.session_state.aksara = ""
                st.text_area("Output Aksara", st.session_state.aksara, height=200, key="output_aksara", label_visibility="collapsed")

        # Konten untuk tab "Text To Speech"
        elif st.session_state.active_tab == "Text To Speech":
            st.markdown("<h1 style='text-align: center; padding: 40px'>Text To Speech</h1>", unsafe_allow_html=True)

            if "teks_input" not in st.session_state:
                st.session_state.teks_input = ""

            teks_input = st.text_area("Masukkan teks di sini", st.session_state.teks_input, height=200)

            submit_button_tts = st.button("Submit", key="submit_tts")

            if submit_button_tts and teks_input:
                st.session_state.processing = True  # Set processing state to True
                tokenizer_tts, model_tts = load_tts_model()

                try:
                    inputs = tokenizer_tts(teks_input, return_tensors="pt")

                    with torch.no_grad():
                        output_waveform = model_tts(**inputs).waveform
                        output_waveform_np = output_waveform.numpy()

                    st.audio(output_waveform_np, format="audio/wav", sample_rate=16000)
                finally:
                    del tokenizer_tts
                    del model_tts
                    torch.cuda.empty_cache()

                # Perbarui text area dengan teks input setelah pemrosesan
                st.session_state.teks_input = teks_input

                conn = create_connection('audio.db')
                c = conn.cursor()
                user_id = st.session_state.user_id
                c.execute("INSERT INTO audio (user_id, latin, aksara, mode_option) VALUES (?, ?, ?, ?)",
                        (user_id, teks_input, "-", "Text To Speech"))
                conn.commit()
                conn.close()

                # Commit to GitHub
                git_commit("audio.db")
                
                st.session_state.processing = False  # Set processing state to False

                # Bersihkan cache Streamlit setelah pemrosesan selesai
                st.cache_data.clear()

    # ===========================================================
    # ================= HALAMAN UTAMA GAMBAR ====================
    # ===========================================================

    if st.session_state.page == "Gambar" and st.session_state.nav == "Gambar":
        col1, col2, col3 = st.columns([0.7, 0.2, 0.2])
        with col1:
            st.write('')
        with col2:
            st.page_link("pages/riwayat_gambar.py", label="Riwayat", icon="📋")
        with col3:
            st.page_link("pages/profil.py", label="Profil", icon="👤")

        st.markdown("<h1 style='text-align: center; padding: 40px'>Mesin Deteksi Gambar</h1>", unsafe_allow_html=True)
        
        # Kontainer untuk menampilkan gambar yang di-upload
        image_container = st.container()

        col1, col2, col3 = st.columns([0.3, 0.1, 0.1])
        with col1:
            pict_file = st.file_uploader("Pilih gambar", type=["png", "jpg"], label_visibility="collapsed")
        with col2:
            button_pict = st.button("Submit", key="pict")
        with col3:
            st.write("")

        # Tampilkan gambar yang di-upload
        if pict_file:
            with image_container:
                st.image(pict_file, caption="Gambar yang di-upload", use_column_width=True)

        if pict_file and button_pict:
            from PIL import Image

            # Baca gambar yang di-upload
            gambar = Image.open(pict_file)

            # Pastikan gambar dalam mode RGB
            if gambar.mode != "RGB":
                gambar = gambar.convert("RGB")

            @st.cache_resource
            def load_image_model():
                processor_gambar = AutoProcessor.from_pretrained("ElStrom/Teks", token=HUGGINGFACE_TOKEN)
                model_gambar = AutoModelForVision2Seq.from_pretrained("ElStrom/Teks", token=HUGGINGFACE_TOKEN)
                return processor_gambar, model_gambar
            
            processor_gambar, model_gambar = load_image_model()

            try:
                # Memproses gambar dan melakukan prediksi
                pixel_values = processor_gambar(gambar, return_tensors="pt").pixel_values
                generated_ids = model_gambar.generate(pixel_values)
                generated_text = processor_gambar.batch_decode(generated_ids, skip_special_tokens=True)[0]

                st.session_state.latin_gambar = generated_text

                # Prediksi dari Latin ke Aksara
                tokenizer_PLTA, model_PLTA = load_model("Latin_to_Aksara")
                inputs_translation = tokenizer_PLTA(generated_text, return_tensors="pt")
                outputs_translation = model_PLTA.generate(**inputs_translation, max_new_tokens=50)
                translated_text = tokenizer_PLTA.batch_decode(outputs_translation, skip_special_tokens=True)[0]

                st.session_state.aksara_gambar = translated_text

                # Menyimpan hasil ke database
                conn = create_connection('image.db')
                c = conn.cursor()
                user_id = st.session_state.user_id
                c.execute("INSERT INTO images (user_id, latin, aksara) VALUES (?, ?, ?)",
                        (user_id, generated_text, translated_text))
                conn.commit()
                conn.close()

                # Commit to GitHub
                git_commit("image.db")
            finally:
                del processor_gambar
                del model_gambar
                torch.cuda.empty_cache()

        col1, col2 = st.columns(2)
        with col1:
            st.markdown("<h3 style='text-align: center;'>Output Latin</h3>", unsafe_allow_html=True)
            if "latin_gambar" not in st.session_state:
                st.session_state.latin_gambar = ""
            st.text_area("Output Latin", st.session_state.latin_gambar, height=200, key="output_latin_gambar", label_visibility="collapsed")

        with col2:
            st.markdown("<h3 style='text-align: center;'>Output Aksara</h3>", unsafe_allow_html=True)
            if "aksara_gambar" not in st.session_state:
                st.session_state.aksara_gambar = ""
            st.text_area("Output Aksara", st.session_state.aksara_gambar, height=200, key="output_aksara_gambar", label_visibility="collapsed")

if __name__ == "__main__":
    main()
