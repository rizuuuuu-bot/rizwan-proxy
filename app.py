import os
import subprocess
import sys  # <-- Hum ne yeh nayi library add ki hai

# --- Configuration ---
# Render humein batayega ke kis port par chalna hai
PORT_TO_USE = os.environ.get("PORT", 10000)

# Secret hum Render ke Environment se lenge
SECRET_TO_USE = os.environ.get("SECRET")

# --- Validation ---
if not SECRET_TO_USE:
    print("FATAL ERROR: Aap ne 'SECRET' environment variable set nahin kiya.")
    # Program ko band kar do
    exit(1)

# --- Start the Proxy ---
# Hum ab "sys.executable" istemal kar rahe hain taake sahi Python use ho
command_to_run = [
    sys.executable,  # <-- Hum ne "python" ki jagah yeh likha hai
    "-m",
    "mtprotoproxy",
    "--port",
    str(PORT_TO_USE),
    "--secret",
    SECRET_TO_USE
]

print(f"Proxy server shuru ho raha hai port {PORT_TO_USE} par...")
# Command ko run karo
subprocess.call(command_to_run)
