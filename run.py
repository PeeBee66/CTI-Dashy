from app import app
import os

def get_version():
    try:
        version_file = os.path.join(os.path.dirname(__file__), 'version.txt')
        with open(version_file, 'r') as f:
            first_line = f.readline().strip()
            version = first_line.split(' ')[0]  # Get version number from first line
            return version
    except FileNotFoundError:
        return "0.0.0"

# Make version available to all templates
@app.context_processor
def inject_version():
    return dict(version=get_version())

if __name__ == '__main__':
    print(f"Starting CTIDashy Flask App - Version: {get_version()}")
    app.run(host='0.0.0.0', port=5000, debug=True)