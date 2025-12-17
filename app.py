from flask import Flask, render_template, request, jsonify, send_file, Response
import subprocess
import os
import signal
import time

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
        if process is None:
            # Use the python from the venv explicitly
            venv_python = os.path.join(os.getcwd(), "venv", "bin", "python")
            process = subprocess.Popen([venv_python, "main.py"], cwd=os.getcwd())
            return jsonify({"status": "success", "message": "Guard AI started successfully!"})
        else:
            return jsonify({"status": "error", "message": "Guard AI is already running!"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)})

@app.route("/stop-guard-ai", methods=["POST"])
def stop_guard_ai():
    global process
    try:
        if process is not None:
            # Send SIGTERM to allow graceful shutdown and report generation
            process.terminate()
            try:
                # Wait up to 5 seconds for the process to finish report generation
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                # If it doesn't stop, force kill it
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
    app.run(debug=True, port=5000)