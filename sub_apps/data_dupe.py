from flask import flash, jsonify, Blueprint, render_template, request, redirect, url_for, current_app, send_file
from flask_login import login_required
import os
import hashlib
import configparser
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import shutil

data_dupe_bp = Blueprint('data_dupe', __name__, url_prefix='/data_dupe')

config = configparser.ConfigParser()

backup_folder = '/mnt/opencti/dev'

if os.path.exists('config/dashy.conf'):
    config.read('config/dashy.conf')
    backup_folder = config.get('data_dupe.py', 'storage_folder', fallback=backup_folder)

folder_data = {}


class DuplicateFileHandler(FileSystemEventHandler):
    def __init__(self, app):
        self.app = app

    def on_created(self, event):
        if not event.is_directory:
            file_path = event.src_path
            folder_path = os.path.dirname(file_path)
            print(f"New file created: {file_path} in folder: {folder_path}")

            if folder_path not in folder_data:
                folder_data[folder_path] = []

            # Collect file information
            file_info = {
                "file_name": os.path.basename(file_path),
                "file_size": os.path.getsize(file_path),
                # Calculate MD5 hash and other relevant data
                # ...
            }
            folder_data[folder_path].append(file_info)

            try:
                # Implement duplication checking logic here
                pass
            except Exception as e:
                print(f"Error during duplication checking: {e}")


@data_dupe_bp.route('/start', methods=['POST'])
@login_required
def start_duplication_check():
    folder_data.clear()
    # Display the loading screen while scanning is in progress
    return render_template('loading.html')


@data_dupe_bp.route('/start-scanning')
@login_required
def start_scanning():
    for root, _, files in os.walk(backup_folder):
        for file_name in files:
            file_path = os.path.join(root, file_name)

            folder_path = os.path.dirname(file_path)

            if folder_path not in folder_data:
                folder_data[folder_path] = []

            file_size = os.path.getsize(file_path)
            md5_hash = calculate_md5_hash(file_path)
            status, duplicated_files = check_duplication(folder_path, md5_hash)  # Implement this function

            folder_data[folder_path].append({
                "file_name": file_name,
                "file_size": file_size,
                "md5_hash": md5_hash,
                "status": status,
                "duplicated_files": duplicated_files
            })

    return redirect(url_for('data_dupe.data_dupe'))


def check_duplication(folder_path, md5_hash):
    status = "Unique"
    duplicated_files = []

    if folder_path in folder_data:
        for file_info in folder_data[folder_path]:
            if file_info["md5_hash"] == md5_hash:
                status = "Duplicate"
                duplicated_files.append(file_info["file_name"])

    return status, duplicated_files


@data_dupe_bp.route('/')
@login_required
def data_dupe():
    return render_template('data_dupe.html', folder_data=folder_data)


def calculate_md5_hash(file_path):
    hash_md5 = hashlib.md5()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()

@data_dupe_bp.route('/delete', methods=['POST'])
@login_required
def delete_file():
    try:
        file_path = request.form['file_path']
        print(f"Deleting file: {file_path}")  # Print for debugging
        os.remove(file_path)

        flash("File deleted successfully", 'success')
        folder_data.clear()

        return render_template('loading.html')

    except OSError as e:
        flash(f"Error deleting file: {e}", 'error')

    return redirect(url_for('data_dupe.data_dupe'))

def loading_screen():
    return render_template('loading.html')
