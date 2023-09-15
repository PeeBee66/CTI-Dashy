from flask import jsonify, Blueprint, render_template, request, redirect, url_for, current_app, send_file
from flask_login import login_required
import os
import configparser
from markupsafe import Markup
from datetime import datetime


folder_size_bp = Blueprint('folder_size', __name__, url_prefix='/folder_size')

config = configparser.ConfigParser()


# Set default values in case the config file is not found
pull_folder = '/mnt/opencti/dev'
put_folder = '/mnt/opencti/dev'

if os.path.exists('config/dashy.conf'):
    config.read('config/dashy.conf')
    pull_folder = config.get('folder_size.py', 'queued_folder', fallback=pull_folder)
    put_folder = config.get('folder_size.py', 'storage_folder', fallback=put_folder)


@folder_size_bp.route('/')
@login_required
def folder_size():


    storage_stats = get_folder_stats(config.get('folder_size.py', 'storage_folder', fallback=put_folder))
    queued_stats = get_folder_stats(config.get('folder_size.py', 'queued_folder', fallback=pull_folder))

    return render_template('folder_size.html', storage_stats=storage_stats, queued_stats=queued_stats, pull_folder=pull_folder, put_folder=put_folder)



def get_folder_stats(path):
    folders = []
    try:
        for folder_name in os.listdir(path):
            folder_path = os.path.join(path, folder_name)
            if os.path.isdir(folder_path):
                file_count, total_size, last_file, last_file_date = get_folder_info(folder_path)
                folders.append({
                    'name': folder_name,
                    'file_count': file_count,
                    'total_size': get_formatted_size(total_size),
                    'last_file': last_file,
                    'last_file_date': last_file_date.strftime('%Y-%m-%d %H:%M:%S') if last_file_date else 'N/A'
                })
            else:
                folders.append({
                    'name': folder_name,
                    'error': None
                })
    except FileNotFoundError:
        folders.append({
            'name': os.path.basename(path),
            'error': Markup('<span style="color: red;">Folder not found</span>')
        })
    return folders



def get_folder_info(path):
    file_count = 0
    total_size = 0
    last_file = None
    last_file_date = None  # Initialize last file date

    for root, dirs, files in os.walk(path):
        file_count += len(files)
        for file in files:
            file_path = os.path.join(root, file)
            total_size += os.path.getsize(file_path)
            file_mtime = os.path.getmtime(file_path)

            if last_file is None or file_mtime > os.path.getmtime(os.path.join(root, last_file)):
                last_file = file
                last_file_date = datetime.fromtimestamp(file_mtime)

    return file_count, total_size, last_file, last_file_date  # Return last file date as well


def get_formatted_size(size):
    # Convert bytes to megabytes (MB) or gigabytes (GB)
    if size < 1024:
        return f"{size} bytes"
    elif size < 1024 * 1024:
        return f"{size / 1024:.2f} KB"
    elif size < 1024 * 1024 * 1024:
        return f"{size / (1024 * 1024):.2f} MB"
    else:
        return f"{size / (1024 * 1024 * 1024):.2f} GB"

