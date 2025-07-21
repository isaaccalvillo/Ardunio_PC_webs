from flask import Flask, request, jsonify
from flask_socketio import SocketIO, emit
import time
import eventlet
eventlet.monkey_patch()  # Patch stdlib for async support with eventlet

app = Flask(__name__)
# Explicitly specify async_mode='eventlet'
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='eventlet')  # Allow all origins for dev

# In-memory event log
event_log = []

# === Endpoint: Receive event from Arduino-PC ===
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

    # Log and emit
    print(f"Received event: {event}")
    event_log.append(event)
    socketio.emit('event_data', event, namespace='/ui')

    return jsonify({'status': 'received'}), 200

# === New Endpoint: Receive command from Web UI ===
@app.route('/command', methods=['POST'])
def receive_command():
    data = request.get_json()
    if not data or 'command' not in data:
        return jsonify({'error': 'No command provided'}), 400

    command = data['command']
    print(f"Command received from Web UI: {command}")

    # Broadcast command to all connected device clients
    socketio.emit('command', {'command': command}, namespace='/device')

    return jsonify({'status': 'Command broadcast'}), 200

# === WebSocket Handlers ===
# From Devices
@socketio.on('connect', namespace='/device')
def device_connect():
    print("📟 Device connected")

@socketio.on('disconnect', namespace='/device')
def device_disconnect():
    print("📟 Device disconnected")

# From UI
@socketio.on('connect', namespace='/ui')
def ui_connect():
    print("🖥️ UI connected")

@socketio.on('disconnect', namespace='/ui')
def ui_disconnect():
    print("🖥️ UI disconnected")

@socketio.on('control_command', namespace='/ui')
def control_command(data):
    print("Control command from UI (WebSocket):", data)
    socketio.emit('command', data, namespace='/device')

# === Run App ===
if __name__ == '__main__':
    print("🚀 Flask-SocketIO server starting on http://0.0.0.0:5000")
    # Use eventlet's WSGI server through socketio.run()
    socketio.run(app, host='0.0.0.0', port=5000)