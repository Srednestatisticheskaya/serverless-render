from flask import Flask, request, jsonify
import os
import sys

app = Flask(__name__)

# Попытка импорта psycopg2 с обработкой ошибок
try:
    import psycopg2
    from urllib.parse import urlparse
    PSYCOPG2_AVAILABLE = True
except ImportError as e:
    print(f"Psycopg2 import error: {e}")
    PSYCOPG2_AVAILABLE = False
    # Временное хранилище в памяти для демонстрации
    demo_messages = []

def get_db_connection():
    if not PSYCOPG2_AVAILABLE:
        return None
        
    DATABASE_URL = os.environ.get('DATABASE_URL')
    if DATABASE_URL:
        try:
            url = urlparse(DATABASE_URL)
            conn = psycopg2.connect(
                database=url.path[1:],
                user=url.username,
                password=url.password,
                host=url.hostname,
                port=url.port
            )
            return conn
        except Exception as e:
            print(f"Database connection error: {e}")
            return None
    return None

@app.route('/')
def hello():
    return "Hello, Serverless! 🚀\n", 200, {'Content-Type': 'text/plain'}

@app.route('/save', methods=['POST'])
def save_message():
    if not PSYCOPG2_AVAILABLE:
        # Демо-режим без базы данных
        data = request.get_json()
        message = data.get('message', '') if data else ''
        demo_messages.append({"id": len(demo_messages) + 1, "text": message})
        return jsonify({"status": "saved (demo mode)", "message": message})
    
    conn = get_db_connection()
    if not conn:
        return jsonify({"error": "DB not connected"}), 500

    data = request.get_json()
    message = data.get('message', '') if data else ''

    try:
        with conn.cursor() as cur:
            cur.execute("INSERT INTO messages (content) VALUES (%s)", (message,))
            conn.commit()
        conn.close()
        return jsonify({"status": "saved", "message": message})
    except Exception as e:
        conn.close()
        return jsonify({"error": str(e)}), 500

@app.route('/messages')
def get_messages():
    if not PSYCOPG2_AVAILABLE:
        return jsonify({"messages": demo_messages[-10:], "mode": "demo"})
    
    conn = get_db_connection()
    if not conn:
        return jsonify({"error": "DB not connected"}), 500

    try:
        with conn.cursor() as cur:
            cur.execute("SELECT id, content, created_at FROM messages ORDER BY id DESC LIMIT 10")
            rows = cur.fetchall()
        conn.close()

        messages = [{"id": r[0], "text": r[1], "time": str(r[2])} for r in rows]
        return jsonify(messages)
    except Exception as e:
        conn.close()
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
