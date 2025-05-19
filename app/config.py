import json
import os
import platform

CONFIG_FILE = os.path.join(os.path.dirname(__file__), 'settings', 'config.json')

def normalize_path(path):
    if not path:
        return ''
    
    # Convert backslashes to forward slashes
    normalized = path.replace('\\', '/')
    
    # Handle drive letters for Windows paths
    if ':' in normalized:
        # Remove drive letter and colon for Linux compatibility
        normalized = '/' + '/'.join(normalized.split(':')[1:])
    
    # Remove any double slashes
    while '//' in normalized:
        normalized = normalized.replace('//', '/')
    
    # Convert to OS-specific format
    return os.path.normpath(normalized)

# app/config.py
def load_config():
    default_config = {
        'opencti_url': '',
        'opencti_api': '',
        'resend_manifest_dir': '',
        'low_side_manifest_dir': '',
        'high_side_manifest_dir': '',
        'feed_backup_dir': '',
        'resend_folder': '',
        'manifest_enabled': True,
        'resend_enabled': True,
        'tor_enabled': True,  # Add this line
        'tor_csv_dir': '',    # Add this line
        'tor_refresh_interval': 5  # Add this line
    }
    
    # Rest of the function remains the same
    
    os.makedirs(os.path.dirname(CONFIG_FILE), exist_ok=True)
    
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, 'r') as f:
            config = json.load(f)
            
            # Normalize path fields
            path_fields = [
                'resend_manifest_dir',
                'low_side_manifest_dir',
                'high_side_manifest_dir',
                'feed_backup_dir',
                'resend_folder'
            ]
            
            for field in path_fields:
                if field in config:
                    config[field] = normalize_path(config[field])
            
            # Merge with default config
            return {**default_config, **config}
    else:
        save_config(default_config)
        return default_config

def save_config(config_data):
    # Save paths in a platform-independent format (forward slashes)
    path_fields = [
        'resend_manifest_dir',
        'low_side_manifest_dir',
        'high_side_manifest_dir',
        'feed_backup_dir',
        'resend_folder'
    ]
    
    save_data = config_data.copy()
    for field in path_fields:
        if field in save_data and save_data[field]:
            save_data[field] = save_data[field].replace('\\', '/')
    
    with open(CONFIG_FILE, 'w') as f:
        json.dump(save_data, f, indent=4)