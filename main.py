from flask import Flask, render_template, request, jsonify
from routes.chat_routes import chat_bp
from routes.whatsapp_routes import whatsapp_bp
from routes.agent_routes import agent_bp
from routes.camp_routes import camp_bp
from routes.awareness_routes import awareness_bp

app = Flask(__name__)

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/emg')
def emergency():
    return render_template('emg.html')

@app.route('/triage')
def triage():
    return render_template('triage.html')

@app.route('/find-clinic')
@app.route('/admission')
def admission():
    return render_template('admission.html')

@app.route('/scheme-checker')
def scheme_checker():
    return render_template('scheme-checker.html')

@app.route('/agent')
def agent_page():
    return render_template('agent.html')

@app.route('/chat')
def chat_page():
    return render_template('chatbot.html')

@app.route('/camp-register')
def camp_register_page():
    return render_template('camp_register.html')

@app.route('/camps')
def camps_page():
    return render_template('camps.html')

@app.route('/government-activities')
def government_activities_page():
    return render_template('government-activities.html')
@app.route('/about')
def about_page():
    return render_template('about.html')

app.register_blueprint(chat_bp)
app.register_blueprint(whatsapp_bp)
app.register_blueprint(agent_bp)
app.register_blueprint(camp_bp)
app.register_blueprint(awareness_bp)

if __name__ == '__main__':
    app.run(debug=True, port=5000)