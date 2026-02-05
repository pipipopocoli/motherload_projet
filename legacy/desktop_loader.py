import webview
import threading
import sys
import os
import time
import requests
from motherload_projet.server.main import start_server

# Configuration
HOST = "127.0.0.1"
PORT = 8000
URL = f"http://{HOST}:{PORT}"

def run_backend():
    """Start the FastAPI server in a separate thread."""
    start_server(host=HOST, port=PORT)

if __name__ == '__main__':
    # Start Backend
    t = threading.Thread(target=run_backend, daemon=True)
    t.start()

    # Create the window pointing to the Python Server (which serves the React App)
    webview.create_window(
        'Motherload Grand Librarium', 
        URL, 
        width=1400, 
        height=900, 
        background_color='#0f172a'
    )
    webview.start()
