import cv2
import os

def extract_frames(video_path, output_folder, interval_seconds=1):
    # Create output directory if it doesn't exist
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)
        print(f"Created folder: {output_folder}")

    # Open the video file
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        print("Error: Could not open video file.")
        return

    # Get video properties
    fps = cap.get(cv2.CAP_PROP_FPS)
    if fps == 0:
        print("Error: Could not determine FPS.")
        return

    frame_interval = int(fps * interval_seconds)
    frame_count = 0
    saved_count = 0

    print(f"Starting extraction from: {video_path}")
    print(f"Extracting 1 frame every {interval_seconds} second(s) (every {frame_interval} frames at {fps:.2f} FPS)")

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        if frame_count % frame_interval == 0:
            frame_name = f"frame_{saved_count:04d}.jpg"
            save_path = os.path.join(output_folder, frame_name)
            cv2.imwrite(save_path, frame)
            saved_count += 1
            if saved_count % 10 == 0:
                print(f"Saved {saved_count} frames...")

        frame_count += 1

    cap.release()
    print(f"Extraction complete. Total frames saved: {saved_count}")

if __name__ == "__main__":
    video_file = "stock-footage--november-gazipur-bangladesh-evening-traffic-flow-on-bangladeshi-street-with-buses-and.mp4"
    output_dir = "frames1"
    extract_frames(video_file, output_dir)
