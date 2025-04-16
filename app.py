from flask import Flask, jsonify, render_template
from helper.process_manager import ProcessManager
#from scripts.telegram_fetch import fetch_telegram_messages

app = Flask(__name__, template_folder="templates")

# Initialize process manager
process_manager = ProcessManager()

# Start telegram fetch script (runs every 5 minutes)
#process_manager.start_process("telegram_fetch", fetch_telegram_messages, schedule_minutes=5)

@app.route("/")
def index():
    return render_template("index.html", message="TradingV1 Live on Heroku!")

@app.route("/api/status")
def status_api():
    return jsonify({"status": "success", "processes": process_manager.get_status()})

@app.route("/api/signals")
def signals_api():
    # Placeholder for mobile app
    return jsonify({"status": "success", "signals": [{"id": 1, "channel": "-1001573131967", "text": "Buy BTC"}]})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)