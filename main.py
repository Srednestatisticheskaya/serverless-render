from flask import Flask, request, jsonify

app = Flask(__name__)

@app.route('/')
def hello():
    return "Hello, Serverless! \n", 200, {'Content-Type': 'text/plain'}

@app.route('/echo', methods=['POST'])
def echo():
    data = request.get_json()
    return jsonify({
        "status": "received",
        "you_sent": data,
        "length": len(str(data)) if data else 0
    })

# Простые эндпоинты без базы данных
messages = []

@app.route('/save', methods=['POST'])
def save_message():
    data = request.get_json()
    message = data.get('message', '') if data else ''
    
    messages.append({
        "id": len(messages) + 1,
        "text": message,
        "time": "2024-01-01T00:00:00"  # фиктивное время
    })
    
    return jsonify({"status": "saved", "message": message})

@app.route('/messages')
def get_messages():
    return jsonify(messages[-10:])  # последние 10 сообщений

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
