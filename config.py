# Guard AI Configuration
# Customize detection thresholds and monitoring parameters

# Lip Detection Settings
LIP_MOVEMENT_THRESHOLD = 5.0  # Increased to reduce false positives
SPEAKING_AUDIO_THRESHOLD = 0.02  # Lowered for better sensitivity (was 0.03)
BACKGROUND_NOISE_THRESHOLD = 0.15  # Increased
AUDIO_DURATION = 0.3  # Duration of audio samples (seconds)
AUDIO_SAMPLE_RATE = 48000  # Changed to 48000Hz (Native for Mac) to fix PortAudio errors
MINIMUM_SPEAKING_DURATION = 0.5  # Reduced to 0.5s to capture short phrases

# Gaze Tracking Settings
LOOK_AWAY_DURATION = 5  # Seconds before warning for looking away
MINIMUM_LOOK_AWAY_DURATION = 2.0  # Seconds before logging
GAZE_WARNING_ENABLED = True  # Show warning when looking away

# Website Monitoring Settings
WEBSITE_CHECK_INTERVAL = 5  # Check website activity every N seconds
MONITOR_BROWSER = "Safari"  # Browser to monitor (Safari, Chrome, etc.)

# Multiple Person Detection
MULTIPLE_PERSON_WARNING = True  # Warn if multiple faces detected
MAX_ALLOWED_FACES = 1  # Maximum number of faces allowed

# Report Settings
REPORT_TITLE = "Guard AI - Proctoring Report"
REPORT_INCLUDE_TIMESTAMPS = True
REPORT_INCLUDE_SUMMARY = True

# Camera Settings
CAMERA_INDEX = 0  # Default camera (0 = built-in webcam)
CAMERA_FLIP = True  # Flip camera horizontally

# Logging Settings
LOG_DIRECTORY = "logs"
ENABLE_DETAILED_LOGGING = True

# Demo Mode
DEMO_MODE = False  # Set to True to generate random events for testing
