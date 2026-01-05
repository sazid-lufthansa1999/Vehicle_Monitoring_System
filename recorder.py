import cv2
import os
from collections import deque
import config

class ViolationRecorder:
    """Manages circular frame buffer and saves violation clips (pre and post buffer)"""
    
    def __init__(self, fps, width, height):
        self.fps = fps
        self.width = width
        self.height = height
        self.buffer_size = int(fps * config.PRE_VIOLATION_SECONDS)
        self.frame_buffer = deque(maxlen=self.buffer_size)
        
        # Active recording tasks: {violation_id: {"writer": vid_writer, "frames_left": int}}
        self.active_recordings = {}
        
        if not os.path.exists(config.VIOLATION_OUTPUT_DIR):
            os.makedirs(config.VIOLATION_OUTPUT_DIR)

    def add_frame(self, frame):
        """Add current frame to buffer and update active recordings"""
        # Store a copy to avoid pointer issues with modified frames
        self.frame_buffer.append(frame.copy())
        
        finished_tasks = []
        for v_id, task in self.active_recordings.items():
            task["writer"].write(frame)
            task["frames_left"] -= 1
            if task["frames_left"] <= 0:
                task["writer"].release()
                finished_tasks.append(v_id)
        
        for v_id in finished_tasks:
            del self.active_recordings[v_id]

    def start_recording(self, violation):
        """Initialize a new video file starting with the buffered pre-violation frames"""
        v_type = violation["type"]
        v_id = f"{v_type}_ID{violation['tracker_id']}_{violation['timestamp']}"
        filename = os.path.join(config.VIOLATION_OUTPUT_DIR, f"{v_id}.mp4")
        
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        writer = cv2.VideoWriter(filename, fourcc, self.fps, (self.width, self.height))
        
        # Write buffered frames (the "pre" 5 seconds)
        # Take a snapshot to avoid RuntimeError: deque mutated during iteration
        buffer_snapshot = list(self.frame_buffer)
        for buffered_frame in buffer_snapshot:
            writer.write(buffered_frame)
            
        # Register task for "post" 5 seconds
        self.active_recordings[v_id] = {
            "writer": writer,
            "frames_left": int(self.fps * config.POST_VIOLATION_SECONDS)
        }
        
        print(f"📁 Started saving violation clip: {filename}")
        return filename
