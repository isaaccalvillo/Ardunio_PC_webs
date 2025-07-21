from flask import Flask, request, jsonify
from flask_socketio import SocketIO, emit
import time

app = Flask(__name__)
#cors_allowed_origins = ["*"]  # Allow all origins for CORS this should be changed when moving to production to add only the desired domain
socketio = SocketIO(app, cors_allowed_origins="*")

# In-memory log (optional)
event_log = []

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

    # Optionally store
    event_log.append(event)

    # Broadcast to connected UIs
    socketio.emit('event_data', event, namespace='/ui')

    return jsonify({'status': 'received'}), 200

# WebSocket: from devices
@socketio.on('connect', namespace='/device')
def device_connect():
    print("Device connected")

@socketio.on('disconnect', namespace='/device')
def device_disconnect():
    print("Device disconnected")

# WebSocket: from UI
@socketio.on('connect', namespace='/ui')
def ui_connect():
    print("UI connected")

@socketio.on('disconnect', namespace='/ui')
def ui_disconnect():
    print("UI disconnected")

# UI sends control command to devices
@socketio.on('control_command', namespace='/ui')
def control_command(data):
    print("Control command from UI:", data)
    # Forward to devices
    socketio.emit('command', data, namespace='/device')

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=5000)
