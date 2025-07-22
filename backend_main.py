from flask import Flask, request, jsonify
from flask_socketio import SocketIO, emit
from flask_cors import CORS
import time
import eventlet

eventlet.monkey_patch()  # Must be called before any standard library imports

app = Flask(__name__)

# === CORS Configuration ===
CORS(app, resources={r"/*": {"origins": "*"}})  # Use "*" for development. Change in production.

# === SocketIO Configuration ===
socketio = SocketIO(app, cors_allowed_origins="*", async_mode="eventlet")

# === In-memory event log (for optional debugging) ===
event_log = []

# === Routes ===

@app.route('/')
def home():
    return jsonify({"status": "ok", "message": "Arduino backend is running."})

@app.route('/event', methods=['POST'])
def receive_event():
    data = request.get_json()
    if not data or 'duration_ms' not in data or 'device_id' not in data:
        return jsonify({'error': 'Invalid data'}), 400

    event = {
        'device_id': data['device_id'],
        'duration_ms': data['duration_ms'],
        'timestamp': data.get('timestamp', time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()))
    }

    print(f"📥 Received event: {event}")
    event_log.append(event)
    socketio.emit('event_data', event, namespace='/ui')

    return jsonify({'status': 'received'}), 200

@app.route('/command', methods=['POST'])
def receive_command():
    data = request.get_json()
    if not data or 'command' not in data:
        return jsonify({'error': 'No command provided'}), 400

    command = data['command']
    print(f"🧭 Command received from Web UI: {command}")

    socketio.emit('command', {'command': command}, namespace='/device')

    return jsonify({'status': 'Command broadcast'}), 200

# === WebSocket Events ===

# From Devices
@socketio.on('connect', namespace='/device')
def device_connect():
    print("✅ Device connected")

@socketio.on('disconnect', namespace='/device')
def device_disconnect():
    print("🔌 Device disconnected")

# From UI
@socketio.on('connect', namespace='/ui')
def ui_connect():
    print("🖥️ UI connected")

@socketio.on('disconnect', namespace='/ui')
def ui_disconnect():
    print("❌ UI disconnected")

@socketio.on('control_command', namespace='/ui')
def control_command(data):
    print("🔁 Control command from UI (WebSocket):", data)
    socketio.emit('command', data, namespace='/device')

# === Start App ===
if __name__ == '__main__':
    print("🚀 Flask-SocketIO server starting on http://0.0.0.0:5000")
    socketio.run(app, host='0.0.0.0', port=5000)