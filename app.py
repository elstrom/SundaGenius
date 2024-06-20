import streamlit as st
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM
from flask import Flask, request, jsonify
from threading import Thread

# Login menggunakan token
import huggingface_hub
huggingface_hub.login(token="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")

# Load model directly
tokenizer = AutoTokenizer.from_pretrained("ElStrom/Aksara_to_Latin")
model = AutoModelForSeq2SeqLM.from_pretrained("ElStrom/Aksara_to_Latin")

# Buat aplikasi Flask untuk menangani permintaan dari HTML
app = Flask(__name__)

@app.route('/predict', methods=['POST'])
def predict():
    input_text = request.json['text']

    # Tokenisasi teks input
    inputs = tokenizer(input_text, return_tensors="pt")

    # Inference menggunakan model
    outputs = model.generate(**inputs)
    
    # Decode hasil dari model
    translated_text = tokenizer.decode(outputs[0], skip_special_tokens=True)

    # Mengembalikan hasil sebagai JSON
    return jsonify({'translation': translated_text})

# Jalankan aplikasi Flask di thread terpisah
def run_flask():
    app.run(debug=False, threaded=True)  # Gunakan threaded=True

# Fungsi untuk menampilkan antarmuka pengguna menggunakan HTML statis di Streamlit
def main():
    st.set_page_config(page_title="Mesin Penerjemahan")

    # Membaca dan menampilkan HTML
    with open('index.html', 'r', encoding='utf-8') as f:
        html_content = f.read()
    st.html(html_content)

if __name__ == '__main__':
    # Mulai thread Flask
    flask_thread = Thread(target=run_flask)
    flask_thread.start()

    # Jalankan aplikasi Streamlit
    main()
