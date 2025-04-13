from flask import Flask, jsonify

app = Flask(__name__)

@app.route("/")
def index():
    return "<h1>TradingV1 Test</h1><p>Live on Heroku! Try <a href='/api/test'>/api/test</a>.</p>"

@app.route("/api/test")
def test_api():
    return jsonify({"status": "success", "message": "TradingV1 test is up!", "channel_id": "-1001573131967"})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)