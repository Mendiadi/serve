from flask import Flask, request, jsonify,render_template
import json
import os
import uuid
from flask import send_file
app = Flask(__name__)

# ---------- הגדרות ----------
DATA_FILE = "data.json"
CODES_FILE = "codes.json"
ADMIN_PASSWORD = "Ad3110$$"  # החלף בסיסמה משלך

# ---------- ניהול קבצים ----------
def load_json(file, default):
    if os.path.exists(file):
        with open(file, "r") as f:
            return json.load(f)
    return default

def save_json(file, data):
    with open(file, "w") as f:
        json.dump(data, f, indent=4)

users = load_json(DATA_FILE, {})
redemption_codes = load_json(CODES_FILE, {})
access_tokens = {}  # uid -> token (לא נשמר לקובץ – לשימוש זמני)

def generate_token():
    return str(uuid.uuid4())

def save_all():
    save_json(DATA_FILE, users)
    save_json(CODES_FILE, redemption_codes)

# ---------- API ------

@app.route("/generate_code", methods=["POST"])
def generate_code():
    data = request.get_json()
    password = data.get("password")

    if password != ADMIN_PASSWORD:
        return jsonify({"error": "Unauthorized"}), 401

    code = str(uuid.uuid4())
    redemption_codes[code] = True
    save_json(CODES_FILE, redemption_codes)
    return jsonify({"redemption_code": code})



@app.route("/get_tokens", methods=["GET"])
def get_tokens():
    uid = request.args.get("uid")
    if uid not in users:
        return jsonify({"error": "User not found"}), 404
    return jsonify({"uid": uid, "tokens": users[uid]["tokens"]})


@app.route("/update_tokens", methods=["POST"])
def update_tokens():
    data = request.get_json()
    uid = data.get("uid")
    amount = data.get("amount")

    if uid not in users:
        return jsonify({"error": "User not found"}), 404
    if not isinstance(amount, int):
        return jsonify({"error": "Invalid amount"}), 400

    users[uid]["tokens"] += amount
    save_json(DATA_FILE, users)
    return jsonify({"uid": uid, "tokens": users[uid]["tokens"]})


@app.route("/is_valid_user", methods=["GET"])
def is_valid_user():
    uid = request.args.get("uid")
    if uid not in users:
        return jsonify({"valid": False}), 404
    return jsonify({"uid": uid, "valid": users[uid]["valid"]})


import json, os, uuid



def load_json(file, default): ...
def save_json(file, data): ...
users = load_json(DATA_FILE, {})
redemption_codes = {}
access_tokens = {}

def generate_token(): return str(uuid.uuid4())
def save_all(): save_json(DATA_FILE, users); save_json(CODES_FILE, redemption_codes)

@app.route("/redeem_code_download", methods=["POST"])
def redeem_code_download():
    data = request.get_json()
    uid = data.get("uid")
    code = data.get("code")

    if not code:
        return jsonify({"error": "Missing uid or code"}), 400
    if code not in redemption_codes:
            return jsonify({"error": "code not correct"}), 400

    del redemption_codes[code]

    # נתיב לקובץ שאתה רוצה לשלוח
    file_path = "LeadMachine_setup_win.exe"
    if not os.path.exists(file_path):
        return jsonify({"error": "File not found"}), 500

    # שלח את הקובץ ישירות להורדה
    return app.redirect("https://mega.nz/file/tQQl2JjQ#2KupMJ2N0oS7lfLEGbj3yEvoHaocuM3mbi2cJlrq5mw")
    
@app.route("/login", methods=["POST"])
def login():
    data = request.get_json()
    uid = data.get("uid")
    password = data.get("password")

    user = users.get(uid)
    if not user or user.get("password") != password:
        return jsonify({"error": "Invalid credentials"}), 401

    token = generate_token()
    access_tokens[uid] = token
    return jsonify({"message": "Login successful", "uid": uid, "access_token": token})
@app.route("/")
def home():
    return render_template("index.html")
if __name__ == "__main__":
    app.run(debug=False,host="0.0.0.0",port=int(os.environ.get("PORT",5000)))
