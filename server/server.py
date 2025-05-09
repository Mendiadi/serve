from flask import Flask, request, jsonify
import json
import os
import uuid

app = Flask(__name__)

# ---------- הגדרות ----------
DATA_FILE = "data.json"
CODES_FILE = "codes.json"
ADMIN_PASSWORD = "my_secret_password"  # החלף בסיסמה משלך

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

# ---------- API ----------

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


@app.route("/register_with_code", methods=["POST"])
def register_with_code():
    data = request.get_json()
    uid = data.get("uid")
    code = data.get("code")

    if not uid or not code:
        return jsonify({"error": "Missing uid or code"}), 400

    if uid in users:
        return jsonify({"error": "User already exists"}), 400

    if code not in redemption_codes:
        return jsonify({"error": "Invalid or used code"}), 400

    # צור משתמש חדש
    users[uid] = {"tokens": 0, "valid": True}
    del redemption_codes[code]

    token = generate_token()
    access_tokens[uid] = token

    save_all()
    return jsonify({"message": "User registered", "uid": uid, "access_token": token})


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


if __name__ == "__main__":
    app.run(debug=False,port="0.0.0.0")
