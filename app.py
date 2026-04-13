from flask import Flask, render_template, request, jsonify
import sqlite3
import os
from datetime import datetime
import pytz
from num import get_number_details

app = Flask(__name__)

# Vercel filesystem is read-only. Use /tmp for SQLite if running on Vercel.
if os.environ.get('VERCEL'):
    DB_PATH = '/tmp/searches.db'
else:
    DATA_DIR = os.path.dirname(os.path.abspath(__file__))
    DB_PATH = os.path.join(DATA_DIR, 'searches.db')

def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS searches (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        phone TEXT,
        result TEXT,
        ip TEXT,
        timestamp TEXT
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS stats (
        id INTEGER PRIMARY KEY,
        total_searches INTEGER DEFAULT 0
    )''')
    c.execute("INSERT OR IGNORE INTO stats (id, total_searches) VALUES (1, 0)")
    conn.commit()
    conn.close()

# Initialize DB on startup
init_db()

def save_search(phone, result, ip):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("INSERT INTO searches (phone, result, ip, timestamp) VALUES (?, ?, ?, ?)",
              (phone, result, ip, datetime.now(pytz.timezone('Asia/Kolkata')).strftime('%Y-%m-%d %H:%M:%S')))
    c.execute("UPDATE stats SET total_searches = total_searches + 1 WHERE id = 1")
    conn.commit()
    conn.close()

def get_history():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT phone, timestamp FROM searches ORDER BY id DESC LIMIT 50")
    data = c.fetchall()
    conn.close()
    return data

def get_stats():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT total_searches FROM stats WHERE id = 1")
    row = c.fetchone()
    total = row[0] if row else 0
    c.execute("SELECT COUNT(DISTINCT phone) FROM searches")
    unique = c.fetchone()[0]
    conn.close()
    return total, unique

@app.route('/')
def index():
    history = get_history()
    total, unique = get_stats()
    return render_template('index.html', history=history, total=total, unique=unique)

@app.route('/search')
def search():
    phone = request.args.get('phone', '').strip()
    if not phone:
        total, unique = get_stats()
        return render_template('index.html', error="Please enter phone number", history=get_history(), total=total, unique=unique)
    try:
        result = get_number_details(phone)
        save_search(phone, result, request.remote_addr)
        total, unique = get_stats()
        return render_template('index.html', result=result, phone=phone, history=get_history(), total=total, unique=unique)
    except Exception as e:
        total, unique = get_stats()
        return render_template('index.html', error=f"Error: {str(e)}", history=get_history(), total=total, unique=unique)

@app.route('/history')
def history_page():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT phone, timestamp FROM searches ORDER BY id DESC LIMIT 100")
    data = c.fetchall()
    conn.close()
    return render_template('history.html', history=data)

@app.route('/stats')
def stats_page():
    total, unique = get_stats()
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT date(timestamp), COUNT(*) FROM searches GROUP BY date(timestamp) ORDER BY date(timestamp) DESC LIMIT 7")
    daily = c.fetchall()
    conn.close()
    return render_template('stats.html', total=total, unique=unique, daily=daily)

@app.route('/api/lookup')
def api_lookup():
    phone = request.args.get('phone', '')
    if not phone:
        return jsonify({"success": False, "error": "Phone required"})
    try:
        result = get_number_details(phone)
        return jsonify({"success": True, "result": result})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})

if __name__ == '__main__':
    init_db()
    # Port 3000 is required for AI Studio preview
    app.run(host='0.0.0.0', port=3000)
