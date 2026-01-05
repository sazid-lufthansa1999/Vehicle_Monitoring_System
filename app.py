from flask import Flask, render_template, Response, jsonify, request, session, redirect, url_for, send_from_directory
import cv2
import os
import time
from vehicle_tracker import VehicleMonitoringSystem
import config

app = Flask(__name__)
app.secret_key = "antigravity_secret_key" # In production, use a secure key

# Mock Database for Role-Based Access
USERS = {
    "admin": {"password": "password123", "role": "admin"},
    "operator": {"password": "op123", "role": "operator"}
}

UPLOAD_FOLDER = 'uploads'
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Global monitoring system instance
monitoring_system = None

def get_monitoring_system():
    global monitoring_system
    if monitoring_system is None:
        monitoring_system = VehicleMonitoringSystem()
    return monitoring_system

@app.route('/upload', methods=['POST'])
def upload_file():
    global monitoring_system
    if 'file' not in request.files:
        return jsonify({"status": "error", "message": "No file part"}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({"status": "error", "message": "No selected file"}), 400
    
    if file:
        filename = file.filename
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(file_path)
        
        # Update config and reset system
        config.SOURCE_VIDEO_PATH = file_path
        monitoring_system = None # Reset to re-initialize with uploaded file
        
        return jsonify({"status": "success", "filename": filename, "path": file_path})

@app.before_request
def require_login():
    allowed_routes = ['login', 'static']
    if 'user' not in session and request.endpoint not in allowed_routes:
        return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        if username in USERS and USERS[username]['password'] == password:
            session['user'] = username
            session['role'] = USERS[username]['role']
            return redirect(url_for('index'))
        return render_template('login.html', error="Invalid credentials")
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('user', None)
    return redirect(url_for('login'))

@app.route('/')
def index():
    return render_template('index.html', user=session.get('user'), role=session.get('role'))

def gen_frames():
    ms = get_monitoring_system()
    for frame in ms.generate_frames():
        ret, buffer = cv2.imencode('.jpg', frame)
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + buffer.tobytes() + b'\r\n')

@app.route('/video_feed')
def video_feed():
    return Response(gen_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/stats')
def stats():
    ms = get_monitoring_system()
    return jsonify({
        "in_count": ms.in_count,
        "out_count": ms.out_count,
        "total_violations": ms.total_violations,
        "recent_violations": list(ms.recent_violations)
    })

@app.route('/violations')
def list_violations():
    v_dir = config.VIOLATION_OUTPUT_DIR
    if not os.path.exists(v_dir):
        return jsonify([])
    files = [f for f in os.listdir(v_dir) if f.endswith('.mp4')]
    # Sort by creation time (newest first)
    files.sort(key=lambda x: os.path.getmtime(os.path.join(v_dir, x)), reverse=True)
    
    violation_data = []
    for f in files:
        parts = f.replace('.mp4', '').split('_')
        # Format: TYPE_ID_DATE_TIME.mp4
        if len(parts) >= 3:
            violation_data.append({
                "filename": f,
                "type": parts[0],
                "id": parts[2] if len(parts) > 2 else "unk",
                "time": f"{parts[-2]} {parts[-1]}"
            })
    return jsonify(violation_data)

@app.route('/video/violation/<filename>')
def serve_violation(filename):
    return send_from_directory(config.VIOLATION_OUTPUT_DIR, filename)

@app.route('/switch_camera', methods=['POST'])
def switch_camera():
    global monitoring_system
    source = request.json.get('source')
    if source:
        config.SOURCE_VIDEO_PATH = source
        monitoring_system = None # Reset to re-initialize with new source
        return jsonify({"status": "success", "new_source": source})
    return jsonify({"status": "error"}), 400

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)
