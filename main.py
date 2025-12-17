import threading
import queue
import cv2
import mediapipe as mp
import numpy as np
import sounddevice as sd
import psutil
import os
import time
import subprocess
from datetime import datetime
import logging
from fpdf import FPDF
import textwrap
import uuid
import signal
import sys
import random
import config as cfg

# Generate unique session ID
SESSION_ID = str(uuid.uuid4())[:8]

# Logging setup
os.makedirs("logs", exist_ok=True)
logging.basicConfig(
    filename="logs/guard_ai_logs.txt", 
    level=logging.INFO, 
    format=f"[{SESSION_ID}] %(asctime)s - %(message)s"
)

# Paths
log_file_path = "website_usage_logs.txt"
session_report_path = "logs/session_report.txt"

# Lip Detection Constants (from config)
UPPER_LIP = [13, 14]
LOWER_LIP = [17, 18]
LIP_MOVEMENT_THRESHOLD = cfg.LIP_MOVEMENT_THRESHOLD
SPEAKING_AUDIO_THRESHOLD = cfg.SPEAKING_AUDIO_THRESHOLD
BACKGROUND_NOISE_THRESHOLD = cfg.BACKGROUND_NOISE_THRESHOLD
AUDIO_DURATION = cfg.AUDIO_DURATION
FS = cfg.AUDIO_SAMPLE_RATE
MINIMUM_SPEAKING_DURATION = cfg.MINIMUM_SPEAKING_DURATION

# Gaze Tracking Constants (from config)
LEFT_EYE = [362, 385, 387, 263, 373, 380]
RIGHT_EYE = [33, 160, 158, 133, 153, 144]
LEFT_IRIS = [474, 475, 476, 477]
RIGHT_IRIS = [469, 470, 471, 472]
LOOK_AWAY_DURATION = cfg.LOOK_AWAY_DURATION
MINIMUM_LOOK_AWAY_DURATION = cfg.MINIMUM_LOOK_AWAY_DURATION

# Global Variables
audio_detected = False
background_noise_detected = False
frame_queue = queue.Queue()
multiple_persons_detected = False
session_start_time = datetime.now()
is_running = True

def signal_handler(sig, frame):
    global is_running
    print(f"\n[Signal Handler] Received signal {sig}. Stopping Guard AI...")
    logging.info(f"Received signal {sig}. Initiating graceful shutdown.")
    is_running = False

# Register signal handlers
signal.signal(signal.SIGTERM, signal_handler)
signal.signal(signal.SIGINT, signal_handler)

# Clear session report at startup for fresh session
def clear_session_report():
    if os.path.exists(session_report_path):
        with open(session_report_path, 'w') as f:
            f.write(f"# Guard AI Session Report - {SESSION_ID}\n")
            f.write(f"# Session Started: {session_start_time.strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        logging.info("Session report cleared for new session")
    else:
        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(session_report_path), exist_ok=True)
        with open(session_report_path, 'w') as f:
            f.write(f"# Guard AI Session Report - {SESSION_ID}\n")
            f.write(f"# Session Started: {session_start_time.strftime('%Y-%m-%d %H:%M:%S')}\n\n")

clear_session_report()

# Helper Functions
def log_event(message):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(log_file_path, "a") as f:
        f.write(f"[{SESSION_ID}] [{timestamp}] {message}\n")
    logging.info(message)

def log_session_event(event_type, start_time, details):
    with open(session_report_path, "a") as f:
        f.write(f"{event_type} | {start_time} | {details}\n")

def is_safari_open():
    for proc in psutil.process_iter(['pid', 'name']):
        if 'Safari' in proc.info['name']:
            return True
    return False

def get_safari_tabs():
    script = '''
    tell application "Safari"
        set windowList to windows
        set tabList to {}
        repeat with aWindow in windowList
            set tabList to tabList & (get name of tabs of aWindow)
        end repeat
        return tabList
    end tell
    '''
    try:
        result = subprocess.run(['osascript', '-e', script], capture_output=True, text=True)
        if result.returncode == 0:
            return result.stdout.strip().split(", ")
        else:
            return []
    except Exception as e:
        print(f"Error running AppleScript: {e}")
        log_event(f"Error running AppleScript: {e}")
        return []

def create_pdf_report(txt_path, pdf_path):
    """Generate a professional PDF report from session data"""
    pdf = FPDF()
    pdf.add_page()
    
    # Title
    pdf.set_font("Arial", 'B', size=20)
    pdf.set_text_color(0, 51, 102)  # Dark blue
    pdf.cell(0, 15, "Guard AI - Proctoring Report", ln=True, align='C')
    pdf.ln(3)
    
    # Session Info Box
    pdf.set_fill_color(240, 240, 240)  # Light gray background
    pdf.set_font("Arial", 'B', size=10)
    pdf.set_text_color(0, 0, 0)
    pdf.cell(0, 8, "Session Information", ln=True, fill=True)
    pdf.set_font("Arial", size=9)
    pdf.cell(0, 6, f"Session ID: {SESSION_ID}", ln=True)
    pdf.cell(0, 6, f"Session Start: {session_start_time.strftime('%Y-%m-%d %H:%M:%S')}", ln=True)
    pdf.cell(0, 6, f"Report Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", ln=True)
    pdf.ln(8)

    # Parse events from log file
    website_events = []
    speaking_events = []
    looking_events = []
    multiple_person_events = []

    try:
        with open(txt_path, "r", encoding="utf-8") as file:
            for line in file:
                line = line.strip()
                if not line:
                    continue

                # Parse different log formats
                if line.startswith("Website Activity"):
                    parts = line.split("|")
                    if len(parts) >= 2:
                        time_part = parts[1].strip()
                        details = parts[2].strip() if len(parts) > 2 else "N/A"
                        website_events.append({"time": time_part, "details": details})
                        
                elif line.startswith("Speaking"):
                    parts = line.split("|")
                    if len(parts) >= 3:
                        start = parts[1].strip()
                        end = parts[2].strip()
                        speaking_events.append({"start": start, "end": end})
                        
                elif line.startswith("Looking Away"):
                    parts = line.split("|")
                    if len(parts) >= 3:
                        start = parts[1].strip()
                        end = parts[2].strip()
                        looking_events.append({"start": start, "end": end})
                        
                elif line.startswith("Multiple Persons"):
                    parts = line.split("|")
                    if len(parts) >= 2:
                        time_part = parts[1].strip()
                        details = parts[2].strip() if len(parts) > 2 else "N/A"
                        multiple_person_events.append({"time": time_part, "details": details})

        # Summary Statistics
        pdf.set_font("Arial", 'B', size=14)
        pdf.set_text_color(0, 51, 102)
        pdf.cell(0, 10, "Summary Statistics", ln=True)
        pdf.set_text_color(0, 0, 0)
        pdf.set_font("Arial", size=10)
        
        pdf.cell(95, 7, f"Total Speaking Incidents: {len(speaking_events)}", border=1)
        pdf.cell(95, 7, f"Total Looking Away Incidents: {len(looking_events)}", border=1, ln=True)
        pdf.cell(95, 7, f"Total Website Checks: {len(website_events)}", border=1)
        pdf.cell(95, 7, f"Multiple Person Detections: {len(multiple_person_events)}", border=1, ln=True)
        pdf.ln(10)

        # Section: Speaking Events
        pdf.set_font("Arial", 'B', 14)
        pdf.set_text_color(0, 51, 102)
        pdf.cell(0, 10, "Speaking Events", ln=True)
        pdf.set_text_color(0, 0, 0)
        pdf.set_font("Arial", size=9)
        
        if speaking_events:
            # Show only first 50 events to avoid huge PDFs
            display_events = speaking_events[:50]
            pdf.set_font("Arial", 'B', size=9)
            pdf.cell(20, 6, "No.", border=1, align='C')
            pdf.cell(85, 6, "Start Time", border=1, align='C')
            pdf.cell(85, 6, "End Time", border=1, align='C', ln=True)
            pdf.set_font("Arial", size=8)
            
            for idx, event in enumerate(display_events, 1):
                pdf.cell(20, 6, str(idx), border=1, align='C')
                pdf.cell(85, 6, event['start'], border=1)
                pdf.cell(85, 6, event['end'], border=1, ln=True)
            
            if len(speaking_events) > 50:
                pdf.set_font("Arial", 'I', size=8)
                pdf.cell(0, 6, f"... and {len(speaking_events) - 50} more events (showing first 50)", ln=True)
        else:
            pdf.cell(0, 7, "No speaking events detected.", ln=True)
        
        pdf.ln(8)

        # Section: Looking Away Events
        pdf.set_font("Arial", 'B', 14)
        pdf.set_text_color(0, 51, 102)
        pdf.cell(0, 10, "Looking Away Events", ln=True)
        pdf.set_text_color(0, 0, 0)
        pdf.set_font("Arial", size=9)
        
        if looking_events:
            display_events = looking_events[:50]
            pdf.set_font("Arial", 'B', size=9)
            pdf.cell(20, 6, "No.", border=1, align='C')
            pdf.cell(85, 6, "Start Time", border=1, align='C')
            pdf.cell(85, 6, "End Time", border=1, align='C', ln=True)
            pdf.set_font("Arial", size=8)
            
            for idx, event in enumerate(display_events, 1):
                pdf.cell(20, 6, str(idx), border=1, align='C')
                pdf.cell(85, 6, event['start'], border=1)
                pdf.cell(85, 6, event['end'], border=1, ln=True)
            
            if len(looking_events) > 50:
                pdf.set_font("Arial", 'I', size=8)
                pdf.cell(0, 6, f"... and {len(looking_events) - 50} more events (showing first 50)", ln=True)
        else:
            pdf.cell(0, 7, "No looking away events detected.", ln=True)
        
        pdf.ln(8)

        # Section: Multiple Person Detection
        pdf.set_font("Arial", 'B', 14)
        pdf.set_text_color(0, 51, 102)
        pdf.cell(0, 10, "Multiple Person Detection", ln=True)
        pdf.set_text_color(0, 0, 0)
        pdf.set_font("Arial", size=9)
        
        if multiple_person_events:
            pdf.set_font("Arial", 'B', size=9)
            pdf.cell(20, 6, "No.", border=1, align='C')
            pdf.cell(60, 6, "Time", border=1, align='C')
            pdf.cell(110, 6, "Details", border=1, align='C', ln=True)
            pdf.set_font("Arial", size=8)
            
            for idx, event in enumerate(multiple_person_events, 1):
                pdf.cell(20, 6, str(idx), border=1, align='C')
                pdf.cell(60, 6, event['time'], border=1)
                pdf.cell(110, 6, event['details'][:50], border=1, ln=True)
        else:
            pdf.cell(0, 7, "No multiple person incidents detected.", ln=True)
        
        pdf.ln(8)

        # Section: Website Activity (show last 20)
        pdf.set_font("Arial", 'B', 14)
        pdf.set_text_color(0, 51, 102)
        pdf.cell(0, 10, "Website Activity (Last 20 Checks)", ln=True)
        pdf.set_text_color(0, 0, 0)
        pdf.set_font("Arial", size=9)
        
        if website_events:
            display_events = website_events[-20:]  # Show last 20
            pdf.set_font("Arial", 'B', size=9)
            pdf.cell(40, 6, "Time", border=1, align='C')
            pdf.cell(150, 6, "Websites/Tabs", border=1, align='C', ln=True)
            pdf.set_font("Arial", size=7)
            
            for event in display_events:
                pdf.cell(40, 6, event['time'][:15], border=1)
                # Truncate long tab names
                tabs = event['details'][:80] + "..." if len(event['details']) > 80 else event['details']
                pdf.cell(150, 6, tabs, border=1, ln=True)
        else:
            pdf.cell(0, 7, "No website activity recorded.", ln=True)

        # Footer
        pdf.ln(10)
        pdf.set_font("Arial", 'I', size=8)
        pdf.set_text_color(128, 128, 128)
        pdf.cell(0, 5, "This report was automatically generated by Guard AI Proctoring System", ln=True, align='C')
        pdf.cell(0, 5, f"For questions or concerns, please contact your exam administrator", ln=True, align='C')

        pdf.output(pdf_path)
        print(f"✅ Final report saved to {pdf_path}")
        logging.info(f"PDF report generated successfully: {pdf_path}")

    except Exception as e:
        print(f"❌ PDF creation error: {e}")
        logging.error(f"PDF generation failed: {e}")

# Lip Detection
def get_lip_distance(landmarks, upper_lip_idx, lower_lip_idx, frame_w, frame_h):
    upper_lip_points = np.array([(landmarks[i].x * frame_w, landmarks[i].y * frame_h) for i in upper_lip_idx])
    lower_lip_points = np.array([(landmarks[i].x * frame_w, landmarks[i].y * frame_h) for i in lower_lip_idx])
    return np.linalg.norm(np.mean(upper_lip_points, axis=0) - np.mean(lower_lip_points, axis=0))

def audio_listener():
    global audio_detected, background_noise_detected
    print("[Audio Listener] Started")
    logging.info("Audio listener thread started")
    
    try:
        devices = sd.query_devices()
        print(f"[Audio] Available devices: {len(devices)}")
        default_input = sd.query_devices(kind='input')
        if default_input:
            print(f"[Audio] Default input device: {default_input['name']}")
    except Exception as e:
        print(f"⚠️ Warning: Could not query audio devices: {e}")
        logging.warning(f"Audio device query failed: {e}")

    while is_running:
        try:
            # Record a small chunk of audio
            audio_data = sd.rec(int(AUDIO_DURATION * FS), samplerate=FS, channels=1, dtype='float64')
            sd.wait()
            volume_norm = np.linalg.norm(audio_data) * 10
            
            # Debug print to see what's happening
            if volume_norm > 0.001:
                print(f"\r[Audio Level]: {volume_norm:.4f} / {SPEAKING_AUDIO_THRESHOLD}", end="", flush=True)
            
            audio_detected = volume_norm > SPEAKING_AUDIO_THRESHOLD
            background_noise_detected = volume_norm > BACKGROUND_NOISE_THRESHOLD
        except Exception as e:
            if is_running:
                print(f"❌ Audio Error: {e}")
                logging.error(f"Audio error: {e}")
            time.sleep(0.5)

# Gaze Tracking
def get_iris_position(landmarks, eye_landmarks, iris_landmarks, frame):
    h, w, _ = frame.shape
    eye_points = np.array([(int(landmarks[i].x * w), int(landmarks[i].y * h)) for i in eye_landmarks])
    iris_points = np.array([(int(landmarks[i].x * w), int(landmarks[i].y * h)) for i in iris_landmarks])
    x_min, y_min = np.min(eye_points, axis=0)
    x_max, y_max = np.max(eye_points, axis=0)

    eye_region = frame[y_min:y_max, x_min:x_max]
    gray_eye = cv2.cvtColor(eye_region, cv2.COLOR_BGR2GRAY)
    _, threshold_eye = cv2.threshold(gray_eye, 50, 255, cv2.THRESH_BINARY_INV)

    contours, _ = cv2.findContours(threshold_eye, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
    if contours:
        contour = max(contours, key=cv2.contourArea)
        (x, y, w_eye, h_eye) = cv2.boundingRect(contour)
        cx = x + w_eye // 2
        cy = y + h_eye // 2
        if cx < eye_region.shape[1] // 3:
            return "Looking Left"
        elif cx > 2 * eye_region.shape[1] // 3:
            return "Looking Right"
        elif cy < eye_region.shape[0] // 3:
            return "Looking Up"
        elif cy > 2 * eye_region.shape[0] // 3:
            return "Looking Down"
        else:
            return "Looking Center"
    return "Looking Center"

# Combined Detection
def run_combined_detection():
    global multiple_persons_detected
    print(f"[Combined Detection] Started - Session ID: {SESSION_ID}")
    logging.info(f"Starting Guard AI monitoring session")
    
    iris_tracking_enabled = False
    
    try:
        # Try initializing with refine_landmarks=True for Iris Tracking
        face_mesh = mp.solutions.face_mesh.FaceMesh(
            static_image_mode=False,
            max_num_faces=2,
            refine_landmarks=True,
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5
        )
        iris_tracking_enabled = True
        print("✅ Face Mesh initialized successfully (Iris Tracking Enabled)")
        logging.info("Face Mesh initialized with Iris Tracking")
    except Exception as e:
        print(f"⚠️ Warning: High-precision tracking failed: {e}")
        logging.warning(f"Iris tracking initialization failed: {e}")
        
        try:
            # Fallback to standard tracking (No Iris)
            face_mesh = mp.solutions.face_mesh.FaceMesh(
                static_image_mode=False,
                max_num_faces=2,
                refine_landmarks=False,
                min_detection_confidence=0.5,
                min_tracking_confidence=0.5
            )
            iris_tracking_enabled = False
            print("✅ Face Mesh initialized in Standard Mode (No Iris Tracking)")
            logging.info("Face Mesh initialized in Standard Mode")
        except Exception as e2:
            print(f"❌ Error initializing face detection: {e2}")
            logging.error(f"Face detection initialization failed: {e2}")
            return
    
    threading.Thread(target=audio_listener, daemon=True).start()
    
    try:
        cap = cv2.VideoCapture(0)
        if not cap.isOpened():
            print("❌ Error: Cannot access camera. Please check permissions.")
            logging.error("Camera access denied or unavailable")
            return
    except Exception as e:
        print(f"❌ Error opening camera: {e}")
        logging.error(f"Camera error: {e}")
        return
    
    previous_distance = 0
    look_away_start = None
    look_away_start_time = None  # Track time.time() for duration calculation
    look_away_start_timestamp = None  # Track actual start time for logging
    speaking_start = None
    speaking_start_time = None  # Track time.time() for duration calculation
    speaking_start_timestamp = None  # Track actual start time for logging
    multiple_person_start = None

    while cap.isOpened() and is_running:
        ret, frame = cap.read()
        if not ret:
            break
        frame = cv2.flip(frame, 1)
        h, w, _ = frame.shape
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        result = face_mesh.process(rgb_frame)

        status = "Not Speaking"
        direction = "No face detected"
        warning = ""
        num_faces = 0

        if result.multi_face_landmarks:
            num_faces = len(result.multi_face_landmarks)
            
            # Check for multiple persons
            if num_faces > 1:
                multiple_persons_detected = True
                current_time = datetime.now().strftime("%H:%M:%S")
                if multiple_person_start is None:
                    multiple_person_start = current_time
                    log_session_event("Multiple Persons", current_time, f"{num_faces} faces detected")
                    logging.warning(f"Multiple persons detected: {num_faces} faces")
                warning = f"⚠️ WARNING: {num_faces} persons detected!"
            else:
                if multiple_person_start is not None:
                    multiple_person_start = None
                multiple_persons_detected = False

        if result.multi_face_landmarks:
            for landmarks in result.multi_face_landmarks:
                distance = get_lip_distance(landmarks.landmark, UPPER_LIP, LOWER_LIP, w, h)
                lip_moving = abs(distance - previous_distance) > LIP_MOVEMENT_THRESHOLD
                previous_distance = distance
                current_time = datetime.now().strftime("%H:%M:%S")

                if lip_moving and audio_detected:
                    status = "Speaking"
                    if speaking_start is None:
                        speaking_start = current_time
                        speaking_start_time = time.time()
                        speaking_start_timestamp = current_time
                else:
                    if speaking_start is not None:
                        # Only log if speaking duration >= MINIMUM_SPEAKING_DURATION
                        duration = time.time() - speaking_start_time
                        if duration >= MINIMUM_SPEAKING_DURATION:
                            log_session_event("Speaking", speaking_start_timestamp, current_time)
                            logging.info(f"Speaking event logged: {duration:.1f}s")
                        speaking_start = None
                        speaking_start_time = None
                        speaking_start_timestamp = None

                # Gaze Tracking (Only if Iris Tracking is enabled)
                if iris_tracking_enabled:
                    try:
                        left_eye_direction = get_iris_position(landmarks.landmark, LEFT_EYE, LEFT_IRIS, frame)
                        right_eye_direction = get_iris_position(landmarks.landmark, RIGHT_EYE, RIGHT_IRIS, frame)
                        direction = left_eye_direction if left_eye_direction == right_eye_direction else "Looking Away"
                    except Exception as e:
                        direction = "Gaze Error"
                else:
                    direction = "Gaze Unavailable"

        if direction != "Looking Center":
            if look_away_start is None:
                look_away_start = datetime.now().strftime("%H:%M:%S")
                look_away_start_time = time.time()  # Record start time for duration
                look_away_start_timestamp = look_away_start
            elif (time.time() - look_away_start_time) > LOOK_AWAY_DURATION:
                warning = "⚠ Please focus on screen!"
        else:
            if look_away_start is not None:
                # Only log if looking away duration >= MINIMUM_LOOK_AWAY_DURATION
                duration = time.time() - look_away_start_time
                if duration >= MINIMUM_LOOK_AWAY_DURATION:
                    end_time_away = datetime.now().strftime("%H:%M:%S")
                    log_session_event("Looking Away", look_away_start_timestamp, end_time_away)
                    logging.info(f"Looking away event logged: {duration:.1f}s")
            look_away_start = None
            look_away_start_time = None
            look_away_start_timestamp = None

        # Display warnings
        cv2.putText(frame, f"Lip Status: {status}", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
        cv2.putText(frame, f"Gaze Direction: {direction}", (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 0, 0), 2)
        cv2.putText(frame, f"Faces Detected: {num_faces}", (10, 90), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 0), 2)
        if warning:
            cv2.putText(frame, warning, (10, 120), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 2)

        if not frame_queue.full():
            frame_queue.put(frame)

    cap.release()

# Website Monitor
def run_website_monitor():
    print("[Website Monitor] Started")
    log_event("🚨 Guard AI Monitoring Started!")

    while is_running:
        if is_safari_open():
            log_event("Safari is open.")
            open_tabs = get_safari_tabs()
            log_event(f"Open tabs in Safari: {open_tabs}")
            log_session_event("Website Activity", str(datetime.now().strftime("%H:%M:%S")), "Tabs: " + ", ".join(open_tabs))
        else:
            log_event("Safari is not open.")
            log_session_event("Website Activity", str(datetime.now().strftime("%H:%M:%S")), "Safari is not open.")
        time.sleep(5)

# Demo Mode Event Generator
def run_demo_mode():
    if not cfg.DEMO_MODE:
        return
    print("[Demo Mode] Started")
    while is_running:
        time.sleep(random.randint(10, 20))
        if not is_running: break
        
        event_type = random.choice(["Speaking", "Looking Away", "Multiple Persons"])
        current_time = datetime.now().strftime("%H:%M:%S")
        
        if event_type == "Speaking":
            end_time = (datetime.now() + timedelta(seconds=random.randint(2, 5))).strftime("%H:%M:%S")
            log_session_event("Speaking", current_time, end_time)
            logging.info(f"[DEMO] Generated Speaking event at {current_time}")
        elif event_type == "Looking Away":
            end_time = (datetime.now() + timedelta(seconds=random.randint(3, 7))).strftime("%H:%M:%S")
            log_session_event("Looking Away", current_time, end_time)
            logging.info(f"[DEMO] Generated Looking Away event at {current_time}")
        elif event_type == "Multiple Persons":
            log_session_event("Multiple Persons", current_time, "2 faces detected (Simulated)")
            logging.info(f"[DEMO] Generated Multiple Persons event at {current_time}")

# Main
if __name__ == "__main__":
    from datetime import timedelta
    combined_thread = threading.Thread(target=run_combined_detection, daemon=True)
    website_thread = threading.Thread(target=run_website_monitor, daemon=True)
    demo_thread = threading.Thread(target=run_demo_mode, daemon=True)

    combined_thread.start()
    website_thread.start()
    if cfg.DEMO_MODE:
        demo_thread.start()

    print("All features are running. Press Ctrl+C to stop.")
    try:
        while is_running:
            if not frame_queue.empty():
                frame = frame_queue.get()
                cv2.imshow("Guard-AI", frame)
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    is_running = False
                    break
            time.sleep(0.01)
    except KeyboardInterrupt:
        print("\nExiting Guard-AI...")
    finally:
        print("\nSaving Final Report...")
        # Generate report with fixed filename for Flask download endpoint
        session_pdf_path = "logs/final_report.pdf"
        create_pdf_report(session_report_path, session_pdf_path)
        print(f"Report saved as: {session_pdf_path}")
        cv2.destroyAllWindows()