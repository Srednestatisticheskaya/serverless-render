from flask import Flask, request, jsonify
import psycopg
import os

app = Flask(__name__)

def get_db_connection():
    """Создает новое соединение с базой данных"""
    DATABASE_URL = os.environ.get('DATABASE_URL')
    if not DATABASE_URL:
        print("DATABASE_URL not found in environment variables")
        return None
    
    try:
        conn = psycopg.connect(DATABASE_URL)
        print("Database connection successful")
        return conn
    except Exception as e:
        print(f"Database connection error: {e}")
        return None

def init_db():
    """Инициализация базы данных"""
    conn = get_db_connection()
    if conn:
        try:
            with conn.cursor() as cur:
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS messages (
                        id SERIAL PRIMARY KEY,
                        content TEXT NOT NULL,
                        created_at TIMESTAMP DEFAULT NOW()
                    )
                """)
                conn.commit()
                print("Table created or already exists")
        except Exception as e:
            print(f"Database initialization error: {e}")
        finally:
            conn.close()

# Инициализируем базу при старте
init_db()

@app.route('/')
def home():
    return jsonify({"message": "Serverless Render Flask App", "status": "running"})

@app.route('/save', methods=['POST'])
def save_message():
    data = request.get_json()
    if not data:
        return jsonify({"error": "No JSON data provided"}), 400
        
    message = data.get('message', '')
    if not message:
        return jsonify({"error": "Message is required"}), 400

    conn = get_db_connection()
    if not conn:
        return jsonify({"error": "Database connection failed"}), 500

    try:
        with conn.cursor() as cur:
            cur.execute("INSERT INTO messages (content) VALUES (%s) RETURNING id", (message,))
            message_id = cur.fetchone()[0]
            conn.commit()
        return jsonify({"status": "saved", "id": message_id, "message": message})
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        conn.close()

@app.route('/messages')
def get_messages():
    conn = get_db_connection()
    if not conn:
        return jsonify({"error": "Database connection failed"}), 500

    try:
        with conn.cursor() as cur:
            cur.execute("SELECT id, content, created_at FROM messages ORDER BY id DESC LIMIT 10")
            rows = cur.fetchall()

        messages = [{"id": r[0], "text": r[1], "time": r[2].isoformat()} for r in rows]
        return jsonify({"messages": messages, "count": len(messages)})
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        conn.close()

@app.route('/health')
def health_check():
    """Проверка здоровья приложения и базы данных"""
    try:
        conn = get_db_connection()
        if conn:
            with conn.cursor() as cur:
                cur.execute("SELECT 1")
                db_status = "connected"
            conn.close()
        else:
            db_status = "not_connected"
        
        return jsonify({
            "status": "healthy", 
            "database": db_status,
            "app": "running"
        })
    except Exception as e:
        return jsonify({
            "status": "unhealthy", 
            "database": "error", 
            "error": str(e)
        }), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
