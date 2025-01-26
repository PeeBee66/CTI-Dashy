# CTIDashy_Flask/app/resend.py
import os
import logging
import csv
from flask import render_template, jsonify, request
from app import app
from app.config import load_config

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def get_manifest_contents(manifest_dir):
    try:
        if not os.path.exists(manifest_dir):
            logger.warning(f"Directory not found: {manifest_dir}")
            return []
            
        files = []
        for file in os.listdir(manifest_dir):
            if file.startswith('CTImanifest_') and file.endswith('.csv'):
                file_path = os.path.join(manifest_dir, file)
                size_kb = os.path.getsize(file_path) / 1024
                files.append({
                    'name': file,
                    'size': f"{size_kb:.1f}"
                })
        return sorted(files, key=lambda x: x['name'])
    except Exception as e:
        logger.error(f"Error reading directory {manifest_dir}: {e}")
        return []

def read_manifest_file(file_path):
    try:
        results = []
        with open(file_path, 'r', encoding='utf-8') as f:
            reader = csv.reader(f)
            next(reader)  # Skip header
            for row in reader:
                if len(row) >= 7:
                    results.append({
                        'Filename': row[0] or '',
                        'CTIfeed': row[1] or '',
                        'MD5Hash': row[2] or '',
                        'DateTime': row[3] or '',
                        'FileSize': row[4] or '',
                        'FlowUUID': row[5] or '',
                        'Resend': row[6] or ''
                    })
        return results
    except Exception as e:
        logger.error(f"Error reading manifest {file_path}: {str(e)}")
        return []

@app.route('/resend')
def resend():
    config = load_config()
    if not config.get('resend_enabled', True):
        return render_template('feature_disabled.html', 
                             feature_name='Resend', 
                             active_tab='resend')
                             
    manifests = get_manifest_contents(config.get('resend_manifest_dir', ''))
    return render_template('resend.html', 
                         active_tab='resend',
                         manifests=manifests)

@app.route('/search_manifest', methods=['POST'])
def search_manifest():
    try:
        data = request.get_json()
        config = load_config()
        manifest_dir = config.get('resend_manifest_dir', '')
        
        if 'manifest_name' in data and data['manifest_name']:
            file_path = os.path.join(manifest_dir, data['manifest_name'])
            if os.path.exists(file_path):
                results = read_manifest_file(file_path)
                return jsonify({'results': results})
            return jsonify({'error': 'Manifest file not found'}), 404

        search_term = data.get('search_term', '').strip()
        if not search_term:
            return jsonify({'error': 'No search term provided'}), 400

        all_results = []
        manifest_files = get_manifest_contents(manifest_dir)
        for manifest in manifest_files:
            file_path = os.path.join(manifest_dir, manifest['name'])
            try:
                manifest_results = read_manifest_file(file_path)
                for row in manifest_results:
                    if any(search_term.lower() in str(value).lower() 
                          for value in row.values()):
                        row['ManifestFile'] = manifest['name']
                        all_results.append(row)
            except Exception as e:
                logger.error(f"Error processing {manifest['name']}: {str(e)}")

        return jsonify({'results': all_results})

    except Exception as e:
        logger.error(f"Search error: {str(e)}")
        return jsonify({'error': str(e)}), 500
    
@app.route('/initiate_resend', methods=['POST'])
def initiate_resend():
    try:
        config = load_config()
        data = request.get_json()
        
        if not data or not all(key in data for key in ['Filename', 'CTIfeed', 'DateTime']):
            return jsonify({'status': 'error', 'message': 'Missing required file information'}), 400
            
        source_base = config.get('feed_backup_dir', '').strip()
        target_base = config.get('resend_folder', '').strip()
        
        if not source_base or not target_base:
            return jsonify({'status': 'error', 'message': 'Feed backup or resend folders not configured'}), 400
            
        # Extract year from DateTime
        year = data['DateTime'].split()[3]  # Format: "Wed Jul 24 03:53:07 UTC 2024"
        feed_folder = data['CTIfeed']
        filename = data['Filename']
        
        # Construct source and target paths with year folder
        source_path = os.path.join(source_base, feed_folder, year, filename)
        target_folder = os.path.join(target_base, feed_folder)
        target_path = os.path.join(target_folder, filename)
        
        # Normalize paths for cross-platform compatibility
        source_path = os.path.normpath(source_path)
        target_path = os.path.normpath(target_path)
        
        # Create target directory if it doesn't exist
        os.makedirs(target_folder, exist_ok=True)
        
        if not os.path.exists(source_path):
            return jsonify({
                'status': 'error',
                'message': f'Source file not found: {source_path}'
            }), 404
            
        import shutil
        shutil.copy2(source_path, target_path)
        
        return jsonify({
            'status': 'success',
            'message': f'File successfully copied to resend folder'
        })
        
    except Exception as e:
        logger.error(f"Resend error: {str(e)}")
        return jsonify({'status': 'error', 'message': str(e)}), 500