from fastapi import FastAPI, Response, UploadFile, File, HTTPException, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, FileResponse
from fastapi.staticfiles import StaticFiles
import cv2
import os
import json
import asyncio
from typing import List, Dict
from vehicle_tracker import VehicleMonitoringSystem
import config

import motor.motor_asyncio
import firebase_admin
from firebase_admin import auth, credentials
from dotenv import load_dotenv

load_dotenv()

# Initialize MongoDB
MONGODB_URL = os.getenv("MONGODB_URL", "mongodb://localhost:27017")
db_client = motor.motor_asyncio.AsyncIOMotorClient(MONGODB_URL)
db = db_client.vehicle_monitoring

# Initialize Firebase Admin
fb_app = None
try:
    cert_path = os.getenv("FIREBASE_SERVICE_ACCOUNT_PATH")
    if cert_path and os.path.exists(cert_path):
        cred = credentials.Certificate(cert_path)
        fb_app = firebase_admin.initialize_app(cred)
        print("🛡️ Firebase Admin initialized")
    else:
        print("⚠️ Firebase Service Account not found. Auth will be bypassed.")
except Exception as e:
    print(f"❌ Firebase Init Error: {e}")

app = FastAPI(title="AI Vehicle Monitoring API")

# Enable CORS with strict origins for credentials support
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:5174", "http://localhost:5175", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global monitoring system instance
monitoring_system = None

# Global event loop for async callbacks
main_loop = None

async def verify_token(request: Request):
    if not fb_app: return {"uid": "mock_user"} # Bypass if not configured
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        print("🛑 Missing Authorization Header")
        raise HTTPException(status_code=401, detail="Missing or invalid token")
    token = auth_header.split(" ")[1]
    try:
        decoded_token = auth.verify_id_token(token)
        return decoded_token
    except Exception as e:
        print(f"🛑 Auth Error: {e}")
        raise HTTPException(status_code=401, detail="Authorization failed")

async def save_violation_to_db(violation):
    try:
        # Avoid numpy types in DB
        v_doc = numpy_cast(violation.copy())
        await db.violations.insert_one(v_doc)
        print(f"💾 Violation saved to MongoDB: {v_doc.get('type')}")
    except Exception as e:
        print(f"❌ DB Save Error: {e}")

def get_ms():
    global monitoring_system, main_loop
    if monitoring_system is None:
        monitoring_system = VehicleMonitoringSystem()
        
        # Link callback using the captured main loop
        if main_loop is None:
            try:
                main_loop = asyncio.get_event_loop()
            except RuntimeError:
                # If we are in a thread without a loop, we can't easily capture it here
                # But the first call to get_ms usually happens in the main thread or on startup
                pass
        
        def sync_callback(v):
            if main_loop and main_loop.is_running():
                asyncio.run_coroutine_threadsafe(save_violation_to_db(v), main_loop)
            else:
                print("⚠️ Main loop not available for DB save")
        
        monitoring_system.on_violation_callback = sync_callback
        monitoring_system.start()
    return monitoring_system

def stop_ms():
    global monitoring_system
    if monitoring_system:
        monitoring_system.stop()
        monitoring_system = None

@app.get("/health")
def health():
    return {"status": "ok"}

def gen_frames():
    ms = get_ms()
    import time
    try:
        while True:
            frame = ms.get_latest_frame()
            if frame is None:
                time.sleep(0.1)
                continue
                
            ret, buffer = cv2.imencode('.jpg', frame)
            if not ret:
                time.sleep(0.01)
                continue
                
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + buffer.tobytes() + b'\r\n')
            # Limit to ~30 FPS for the stream itself to save bandwidth
            time.sleep(1/30)
    except Exception as e:
        print(f"📢 Stream client disconnected: {e}")
    finally:
        print("🔌 Stream connection closed.")

@app.get("/video_feed")
def video_feed():
    return StreamingResponse(gen_frames(), media_type="multipart/x-mixed-replace; boundary=frame")

def numpy_cast(obj):
    if isinstance(obj, (list, tuple)):
        return [numpy_cast(x) for x in obj]
    if isinstance(obj, dict):
        return {k: numpy_cast(v) for k, v in obj.items()}
    if hasattr(obj, 'item') and callable(getattr(obj, 'item')):
        return obj.item()
    return obj

@app.get("/stats")
async def stats(token_data: dict = Depends(verify_token)):
    try:
        ms = get_ms()
        with ms.lock:
            recent = list(ms.recent_violations)
            data = {
                "in_count": int(ms.in_count),
                "out_count": int(ms.out_count),
                "total_violations": int(ms.total_violations),
                "recent_violations": numpy_cast(recent)
            }
        return data
    except Exception as e:
        print(f"❌ Error in /stats: {e}")
        return {"error": str(e)}

@app.get("/violations")
async def list_violations(token_data: dict = Depends(verify_token)):
    # First try fetching from MongoDB
    try:
        cursor = db.violations.find().sort("timestamp", -1).limit(50)
        violations = await cursor.to_list(length=50)
        if violations:
            # Convert ObjectId to string for JSON
            for v in violations:
                v["_id"] = str(v["_id"])
            return violations
    except Exception as e:
        print(f"⚠️ DB Fetch Error, falling back to disk: {e}")

    # Fallback to local files if DB is empty or fails
    v_dir = config.VIOLATION_OUTPUT_DIR
    if not os.path.exists(v_dir):
        return []
    files = [f for f in os.listdir(v_dir) if f.endswith('.mp4')]
    files.sort(key=lambda x: os.path.getmtime(os.path.join(v_dir, x)), reverse=True)
    
    violation_data = []
    for f in files:
        parts = f.replace('.mp4', '').split('_')
        if len(parts) >= 3:
            violation_data.append({
                "filename": f,
                "type": parts[0],
                "id": parts[2] if len(parts) > 2 else "unk",
                "time": f"{parts[-2]} {parts[-1]}"
            })
    return numpy_cast(violation_data)

@app.get("/video/violation/{filename}")
def serve_violation(filename: str):
    file_path = os.path.join(config.VIOLATION_OUTPUT_DIR, filename)
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Video not found")
    return FileResponse(file_path)

@app.post("/switch_camera")
async def switch_camera(data: Dict[str, str], token_data: dict = Depends(verify_token)):
    global monitoring_system
    source = data.get('source')
    if source:
        print(f"🔄 Switching camera source to: {source}")
        stop_ms() # Stop current worker
        config.SOURCE_VIDEO_PATH = source
        get_ms() # Force restart with new source
        return {"status": "success", "new_source": source}
    return {"status": "error", "message": "Source not provided"}

@app.post("/upload")
async def upload_file(file: UploadFile = File(...), token_data: dict = Depends(verify_token)):
    global monitoring_system
    upload_dir = "uploads"
    if not os.path.exists(upload_dir):
        os.makedirs(upload_dir)
    
    file_path = os.path.join(upload_dir, file.filename)
    with open(file_path, "wb") as f:
        f.write(await file.read())
    
    print(f"📂 File uploaded: {file.filename} -> {file_path}")
    config.SOURCE_VIDEO_PATH = file_path
    stop_ms() # Stop current worker
    get_ms() # Force restart with new source
    return {"status": "success", "filename": file.filename, "path": file_path}

@app.on_event("startup")
async def startup_event():
    global main_loop
    main_loop = asyncio.get_running_loop()
    print("🚀 Server starting - Event loop captured")
    # Warm up monitoring system
    get_ms()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8005)
