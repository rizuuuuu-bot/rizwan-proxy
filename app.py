import os
import subprocess

# --- Configuration ---
# Render humein batayega ke kis port par chalna hai
# Agar nahin batata to hum 10000 istemal karenge
PORT_TO_USE = os.environ.get("PORT", 10000)

# Secret hum Render ke Environment se lenge
SECRET_TO_USE = os.environ.get("SECRET")

# --- Validation ---
if not SECRET_TO_USE:
    print("FATAL ERROR: Aap ne 'SECRET' environment variable set nahin kiya.")
    # Program ko band kar do
    exit(1)

# --- Start the Proxy ---
# Yeh woh command hai jo humara proxy server start karegi
command_to_run = [
    "python",
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
