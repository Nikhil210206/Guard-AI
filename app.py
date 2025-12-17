from flask import Flask, render_template, request, jsonify, send_file, Response
import multiprocessing
import os
import signal
import time
import main  # Import the main module

app = Flask(__name__, static_folder="Frontend", template_folder="Frontend", static_url_path="")
process = None  

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/features")
def features():
    return render_template("feature.html")

@app.route("/start-guard-ai", methods=["POST"])
def start_guard_ai():
    global process
    try:
        if process is None or not process.is_alive():
            # Start the detection process using multiprocessing
            process = multiprocessing.Process(target=main.start_detection_process)
            process.start()
            return jsonify({"status": "success", "message": "Guard AI started successfully!"})
        else:
            return jsonify({"status": "error", "message": "Guard AI is already running!"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)})

@app.route("/stop-guard-ai", methods=["POST"])
def stop_guard_ai():
    global process
    try:
        if process is not None and process.is_alive():
            # Terminate the process
            process.terminate()
            process.join(timeout=5)
            if process.is_alive():
                process.kill()
            
            process = None
            return jsonify({"status": "success", "message": "Guard AI stopped successfully!"})
        else:
            return jsonify({"status": "error", "message": "Guard AI is not running!"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)})

@app.route("/download-report", methods=["GET"])
def download_report():
    report_path = "logs/final_report.pdf"
    if os.path.exists(report_path):
        return send_file(report_path, as_attachment=True)
    else:
        return jsonify({"status": "error", "message": "Report not found!"})

@app.route("/stream-logs")
def stream_logs():
    def generate_logs():
        log_file = "logs/guard_ai_logs.txt"
        if not os.path.exists(log_file):
            yield "data: Waiting for logs...\n\n"
            return

        with open(log_file, "r") as f:
            # Seek to end of file
            f.seek(0, 2)
            while True:
                line = f.readline()
                if line:
                    yield f"data: {line}\n\n"
                else:
                    time.sleep(0.5)

    return Response(generate_logs(), mimetype="text/event-stream")

if __name__ == "__main__":
    multiprocessing.freeze_support()  # Required for PyInstaller
    app.run(debug=False, port=5000)  # Debug=False for production/packaged app