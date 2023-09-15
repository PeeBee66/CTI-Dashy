import os
from flask import send_file, Blueprint, render_template, request, redirect, url_for
from flask_login import login_required
import configparser
import subprocess

settings_bp = Blueprint('settings', __name__, url_prefix='/settings')

# Path to the configuration file and directory
CONFIG_FILE_PATH = 'config/dashy.conf'
CONFIG_DIRECTORY = 'config'
DEFAULT_SETTINGS = {
    'api_search.py': {
        'ip_address': 'localhost',
        'api_key': '12345678',
        'Port': '4000'
    },
    'data_dupe.py': {
        'storage_folder': '/mnt/opencti/dev'
    },
    'folder_size.py': {
        'storage_folder': '/mnt/opencti/dev',
        'queued_folder': '/mnt/opencti/dev'
    },
    'hash_search.py': {
        'ip_address': 'localhost',
        'api_key': '12345678',
        'Port': '4000'
    },
    'manifest.py': {
        'low_side_folder': '/mnt/opencti/dev',
        'high_side_folder': '/mnt/opencti/dev',
        'system_type' : 'dev'

    },
    're_send.py': {
        'storage_folder': '/mnt/opencti/dev',
        'queued_folder': '/mnt/opencti/dev'
    },
    'user_mgmt.py': {
        'ip_address': 'localhost',
        'api_key': '12345678',
        'Port': '4000',
        'Connector_group_ID': '123456'
    }
}

def create_config_file():
    # Create the directory if it does not exist
    os.makedirs(CONFIG_DIRECTORY, exist_ok=True)

    # Create the configuration file with default settings
    config = configparser.ConfigParser()
    for app, app_settings in DEFAULT_SETTINGS.items():
        config[app] = app_settings
    with open(CONFIG_FILE_PATH, 'w') as configfile:
        #print(f"Created New Config (dashy.conf) File.")\
        config.write(configfile)

@settings_bp.route('/')
@login_required
def show_settings():
    # Check if the configuration file exists, if not, create it with default settings
    if not os.path.exists(CONFIG_FILE_PATH):
        create_config_file()

    # Read existing settings from the configuration file
    config = configparser.ConfigParser()
    config.read(CONFIG_FILE_PATH)

    return render_template('settings.html', config=config)


@settings_bp.route('/update', methods=['POST'])
@login_required
def update_settings():
    if request.method == 'POST':
        config = configparser.ConfigParser()
        config.read(CONFIG_FILE_PATH)
        for section in config.sections():
            for setting_key in config[section]:
                form_key = f"{section}_{setting_key}"
                form_value = request.form.get(form_key)
                if form_value is not None and form_value.strip():
                    config[section][setting_key] = form_value

        # Save the updated config to the file
        with open(CONFIG_FILE_PATH, 'w') as configfile:
            #print(f"Updated dashy.conf.")
            config.write(configfile, space_around_delimiters=True)

    return redirect(url_for('settings.show_settings'))


@settings_bp.route('/reboot', methods=['POST'])
@login_required
def reboot_app():
    script_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'restart.py')
    subprocess.run(['python3', script_path], check=True, shell=False)

    return "CTI Dashy is rebooting..."
