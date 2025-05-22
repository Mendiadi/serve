from flask import Flask, request, jsonify, render_template
import os
import json
import uuid
from datetime import datetime
from pymongo import MongoClient

# MongoDB Connection
MONGO_URI = "mongodb+srv://itsshokobo:btNjtK4xgwnGSeNf@cluster0.gsohlmo.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
client = MongoClient(MONGO_URI)
db = client['flask_codes_db']
redemption_collection = db['redemption_codes']
used_collection = db['used_codes']

app = Flask(__name__)
def load_redemption_codes():
    return {doc["code"]: True for doc in redemption_collection.find()}

def load_used_codes():
    return {doc["code"]: True for doc in used_collection.find()}

def save_redemption_code(code):
    redemption_collection.insert_one({"code": code})

def delete_redemption_code(code):
    redemption_collection.delete_one({"code": code})

def save_used_code(code):
    used_collection.insert_one({"code": code})

def delete_used_code(code):
    used_collection.delete_one({"code": code})
try:
    redemption_codes = load_redemption_codes()
    used_codes = load_used_codes()
except Exception as e:
    print(f"❌ Failed to load codes from MongoDB: {e}")
    redemption_codes = {}
    used_codes = {}



# ---------- קבצים ----------
CODES_FILE = "codes.json"
USED_CODES_FILE = "used_codes.json"
ACCESS_LOG_FILE = "access.log"
ADMIN_PASSWORD = "Ad3110$$"
# ---------- קודים חסומים ----------
blocked_codes = set()

# ---------- טוען קבצים ----------
def load_json(file, default):
    if os.path.exists(file):
        with open(file, "r") as f:
            return json.load(f)
    return default

def save_json(file, data):
    with open(file, "w") as f:
        json.dump(data, f, indent=4)

def log_access(ip, code, action, status):
    timestamp = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
    with open(ACCESS_LOG_FILE, "a") as f:
        f.write(f"[{timestamp}] IP: {ip} | Code: {code} | Action: {action} | Status: {status}\n")

# ---------- נתונים בזיכרון ----------
redemption_codes = load_json(CODES_FILE, {})  # קודים פעילים
used_codes = load_json(USED_CODES_FILE, {})  # קודים שמומשו
code_access_log = {}  # קוד -> סט של כתובות IP
print(used_codes)
print(redemption_codes)

# ---------- IP ----------
def get_client_ip():
    return request.headers.get('X-Forwarded-For', request.remote_addr)

def track_code_usage(code, action):
    ip = get_client_ip()
    
    if code in blocked_codes:
        log_access(ip, code, action, "BLOCKED")
        return False

    if code not in code_access_log:
        code_access_log[code] = set()
    code_access_log[code].add(ip)

    if len(code_access_log[code]) > 2:
        blocked_codes.add(code)
        log_access(ip, code, action, "BLOCKED")
        return False

    log_access(ip, code, action, "OK")
    return True

# ---------- יצירת קוד ----------
@app.route("/generate_code", methods=["POST"])
def generate_code():
    data = request.get_json()
    password = data.get("password")

    if password != ADMIN_PASSWORD:
        return jsonify({"error": "Unauthorized"}), 401

    code = str(uuid.uuid4())
    redemption_codes[code] = True
    save_redemption_code(code)
    return jsonify({"redemption_code": code})


# ---------- בדיקת קוד ----------
@app.route("/is_code_valid", methods=["GET"])
def is_code_valid():
    code = request.args.get("code")
    if code in blocked_codes:
        log_access(get_client_ip(), code, "check", "BLOCKED")
        return jsonify({"valid": False, "blocked": True}), 403

    if not code:
        return jsonify({"error": "Missing code"}), 400

    ip = get_client_ip()

    if code in used_codes:
        log_access(ip, code, "check", "USED")
        return jsonify({"valid": False, "used": True}), 200  # תוקן ל־200

    if code not in redemption_codes:
        log_access(ip, code, "check", "INVALID")
        return jsonify({"valid": False, "used": False}), 404

    if not track_code_usage(code, "check"):
        return jsonify({"error": "Code blocked due to suspicious activity"}), 403

    return jsonify({"valid": True, "used": False}), 200


# ---------- מימוש קוד ----------
@app.route("/redeem_code", methods=["POST"])
def redeem_code():
    data = request.get_json()
    code = data.get("code")

    if not code:
        return jsonify({"error": "Missing code"}), 400
    if code not in redemption_codes:
        log_access(get_client_ip(), code, "redeem", "INVALID")
        return jsonify({"error": "Invalid or already used code"}), 400

    if not track_code_usage(code, "redeem"):
        return jsonify({"error": "Code blocked due to suspicious activity"}), 403

    del redemption_codes[code]
    used_codes[code] = True
    delete_redemption_code(code)
    save_used_code(code)
    log_access(get_client_ip(), code, "redeem", "SUCCESS")
    return jsonify({"message": "Code redeemed successfully"})


# ---------- מחיקת קוד מומש (אדמין) ----------
@app.route("/admin/delete_code", methods=["POST"])
def admin_delete_code():
    data = request.get_json()
    password = data.get("password")
    code = data.get("code")

    if password != ADMIN_PASSWORD:
        return jsonify({"error": "Unauthorized"}), 401

    if code in redemption_codes:
        del redemption_codes[code]
        delete_redemption_code(code)
    if code in used_codes:
        del used_codes[code]
        delete_used_code(code)

    log_access("ADMIN", code, "delete", "DELETED")
    return jsonify({"message": "Code deleted"})


# ---------- דף הבית ----------
@app.route("/")
def home():
    return render_template("index.html")

# ---------- הרצת השרת ----------
if __name__ == "__main__":
    app.run(debug=False, host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
