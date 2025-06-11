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
