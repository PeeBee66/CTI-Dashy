#!/usr/bin/env python3

import os
import signal
import time
import subprocess

def reboot_flask_app():
    try:
        # Find the Gunicorn process IDs
        gunicorn_process_ids = os.popen("pgrep -f 'gunicorn -b 0.0.0.0:5000'").read().splitlines()

        # Send a TERM signal to each Gunicorn process
        for pid in gunicorn_process_ids:
            os.kill(int(pid), signal.SIGTERM)

        print("Graceful shutdown signal sent to Gunicorn processes.")

        # Wait for a few seconds to allow the processes to shut down
        time.sleep(5)

        # Kill the remaining Gunicorn processes
        for pid in gunicorn_process_ids:
            os.kill(int(pid), signal.SIGKILL)

        print("Old Gunicorn processes killed.")

        # Restart the Gunicorn Flask app
        app_process = subprocess.Popen(["gunicorn", "-b", "0.0.0.0:5000", "app:app"])
        app_process.wait()  # Wait for the app to finish before proceeding
        print("Gunicorn Flask app restarted successfully.")
    except Exception as e:
        print("Error rebooting Gunicorn Flask app:", e)

reboot_flask_app()
