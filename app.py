from flask import Flask, request, jsonify, render_template
from transformers import pipeline

app = Flask(__name__)

# Load the model
pipe = pipeline("text2text-generation", model="ElStrom/Aksara_to_Latin")

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/predict', methods=['POST'])
def predict():
    data = request.json
    input_text = data['text']
    result = pipe(input_text)
    translated_text = result[0]['generated_text']
    return jsonify({'translation': translated_text})

if __name__ == '__main__':
    app.run(debug=True)
