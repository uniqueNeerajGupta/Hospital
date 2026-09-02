from flask import Flask, render_template, request, jsonify
from services.triage_engine import assess_symptoms

app = Flask(__name__)

@app.route('/')
def home():
    return render_template('index.html')

if __name__ == '__main__':
    app.run(debug=True, port=5000)
