from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
import sqlite3
from datetime import datetime

app = Flask(__name__)
CORS(app)

DB_FILE = 'rfid_access.db'

def check_card_in_db(card_uid):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT * FROM authorized_cards WHERE card_uid = ?", (card_uid,))
    result = c.fetchone()
    conn.close()
    return result is not None
    
def log_entry(card_uid, status):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("INSERT INTO entry_logs (card_uid, timestamp, status) VALUES (?, ?, ?)",
              (card_uid, timestamp, status))
    conn.commit()
    conn.close()

@app.route('/check_card', methods=['POST'])
def check_card():
    data = request.get_json()
    card_uid = data.get('card_uid', '').upper()

    if not card_uid:
        return jsonify({'error': 'Missing card UID'}), 400

    authorized = check_card_in_db(card_uid)
    status = "granted" if authorized else "denied"
    log_entry(card_uid, status)

    return jsonify({'granted': authorized})

@app.route('/')
def index():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT card_uid, timestamp, status FROM entry_logs ORDER BY timestamp DESC LIMIT 20")
    logs = c.fetchall()
    conn.close()
    return render_template("index.html", logs=logs)

@app.route('/cards', methods=['GET', 'POST', 'DELETE'])
def manage_cards():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()

    if request.method == 'GET':
        c.execute("SELECT card_uid FROM authorized_cards ORDER BY card_uid ASC")
        cards = [row[0] for row in c.fetchall()]
        conn.close()
        return jsonify(cards)

    elif request.method == 'POST':
        card_uid = request.get_json().get('card_uid', '').upper()
        c.execute("INSERT OR IGNORE INTO authorized_cards (card_uid) VALUES (?)", (card_uid,))
        conn.commit()
        conn.close()
        return jsonify({'success': True})

    elif request.method == 'DELETE':
        card_uid = request.get_json().get('card_uid', '').upper()
        c.execute("DELETE FROM authorized_cards WHERE card_uid = ?", (card_uid,))
        conn.commit()
        conn.close()
        return jsonify({'success': True})

@app.route('/logs', methods=['GET'])
def get_logs():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT card_uid, timestamp, status FROM entry_logs ORDER BY timestamp DESC LIMIT 20")
    logs = c.fetchall()
    conn.close()
    return jsonify(logs)

@app.route('/door_state', methods=['GET'])
def get_door_state():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT timestamp, state FROM door_state_log ORDER BY timestamp DESC LIMIT 20")
    rows = c.fetchall()
    conn.close()
    return jsonify(rows[::-1])  # return oldest to newest


@app.route('/door_state', methods=['POST'])
def post_door_state():
    data = request.get_json()
    state = data.get('state', '').lower()
    if state not in ['open', 'closed']:
        return jsonify({'error': 'Invalid state'}), 400

    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("INSERT INTO door_state_log (state, timestamp) VALUES (?, ?)", (state, timestamp))
    conn.commit()
    conn.close()

    return jsonify({'success': True})



if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
