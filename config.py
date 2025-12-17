# Guard AI Configuration
# Customize detection thresholds and monitoring parameters

# Lip Detection Settings
LIP_MOVEMENT_THRESHOLD = 2.5  # Minimum lip movement to detect (pixels)
SPEAKING_AUDIO_THRESHOLD = 0.01  # Minimum audio level for speaking detection
BACKGROUND_NOISE_THRESHOLD = 0.08  # Audio threshold for background noise
AUDIO_DURATION = 0.3  # Duration of audio samples (seconds)
AUDIO_SAMPLE_RATE = 44100  # Audio sampling rate (Hz)

# Gaze Tracking Settings
LOOK_AWAY_DURATION = 5  # Seconds before warning for looking away
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
