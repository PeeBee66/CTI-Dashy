# CTIDashy_Flask/run.py
from app import app

# Read version from version.txt
def get_version():
    try:
        with open("version.txt", "r") as f:
            return f.read().strip()
    except FileNotFoundError:
        return "unknown"

VERSION = get_version()

if __name__ == '__main__':
    print(f"Starting CTIDashy Flask App - Version: {VERSION}")
    app.run(host='0.0.0.0', port=5000, debug=True)
