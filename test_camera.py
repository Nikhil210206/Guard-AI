import cv2
import sys

print("Testing Camera Access...")
try:
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("❌ Error: Could not open camera (Index 0).")
        print("  - Check permissions in System Settings > Privacy & Security > Camera")
        print("  - Check if another app is using the camera")
    else:
        print("✅ Camera opened successfully!")
        ret, frame = cap.read()
        if ret:
            print(f"✅ Captured frame: {frame.shape}")
            cv2.imwrite("camera_test.jpg", frame)
            print("✅ Saved test image to camera_test.jpg")
        else:
            print("❌ Error: Could not read frame from camera.")
        cap.release()
except Exception as e:
    print(f"❌ Exception during camera test: {e}")
