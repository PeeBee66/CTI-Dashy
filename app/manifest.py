import os
import logging
import pandas as pd
from flask import render_template, jsonify, request
from app import app
from app.config import load_config

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def get_manifest_files(directory):
    try:
        if not os.path.exists(directory):
            logger.warning(f"Directory not found: {directory}")
            return []
            
        files = []
        for file in os.listdir(directory):
            if file.startswith('CTImanifest_') and file.endswith('.csv'):
                file_path = os.path.join(directory, file)
                size_kb = os.path.getsize(file_path) / 1024
                files.append({
                    'name': file,
                    'size': f"{size_kb:.1f}"
                })
        return sorted(files, key=lambda x: x['name'])
    except Exception as e:
        logger.error(f"Error reading directory {directory}: {e}")
        return []

def read_manifest_file(file_path):
    try:
        df = pd.read_csv(file_path)
        if 'MD5Hash' in df.columns:
            df['MD5Hash'] = df['MD5Hash'].str.lower()
        df = df.where(pd.notnull(df), None)
        return df
    except Exception as e:
        logger.error(f"Error reading {file_path}: {str(e)}")
        return None

def compare_manifests(source_file, target_file):
    try:
        source_df = read_manifest_file(source_file)
        target_df = read_manifest_file(target_file)
        
        if source_df is None or target_df is None:
            raise ValueError("Failed to read manifest files")
            
        missing_df = source_df[~source_df['MD5Hash'].isin(target_df['MD5Hash'])]
        differences = missing_df.to_dict('records')
        logger.info(f"Found {len(differences)} differences")
        
        clean_differences = []
        for diff in differences:
            clean_diff = {k: ('' if pd.isna(v) else v) for k, v in diff.items()}
            clean_differences.append(clean_diff)
            
        return clean_differences
        
    except Exception as e:
        logger.error(f"Error comparing manifests: {str(e)}")
        raise

def compare_all_manifests(system1_dir, system2_dir):
    try:
        system1_files = get_manifest_files(system1_dir)
        results = []
        
        for file in system1_files:
            source_file = os.path.join(system1_dir, file['name'])
            target_file = os.path.join(system2_dir, file['name'])
            
            if not os.path.exists(target_file):
                results.append({
                    'manifest': file['name'],
                    'differences': [],
                    'error': 'Target file not found on system2'
                })
                continue
                
            try:
                differences = compare_manifests(source_file, target_file)
                results.append({
                    'manifest': file['name'],
                    'differences': differences,
                    'error': None
                })
            except Exception as e:
                results.append({
                    'manifest': file['name'],
                    'differences': [],
                    'error': str(e)
                })
                
        return results
    except Exception as e:
        logger.error(f"Error in compare_all_manifests: {str(e)}")
        raise

@app.route('/manifest')
def manifest():
    config = load_config()
    if not config.get('manifest_enabled', True):
        return render_template('feature_disabled.html',
                             feature_name='Manifest',
                             active_tab='manifest')
    
    system1_dir = config.get('system1_manifest_dir', '')
    system2_dir = config.get('system2_manifest_dir', '')
    
    return render_template('manifest.html',
                         active_tab='manifest',
                         system1_files=get_manifest_files(system1_dir),
                         system2_files=get_manifest_files(system2_dir))

@app.route('/refresh_manifest_files', methods=['POST'])
def refresh_manifest_files():
    try:
        config = load_config()
        if not config.get('manifest_enabled', True):
            return jsonify({
                'status': 'error',
                'message': 'Manifest feature is disabled'
            }), 403
            
        system1_dir = config.get('system1_manifest_dir', '')
        system2_dir = config.get('system2_manifest_dir', '')
        
        return jsonify({
            'status': 'success',
            'system1_files': get_manifest_files(system1_dir),
            'system2_files': get_manifest_files(system2_dir)
        })
        
    except Exception as e:
        logger.error(f"Refresh error: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@app.route('/compare_manifests', methods=['POST'])
def compare_manifests_endpoint():
    try:
        config = load_config()
        if not config.get('manifest_enabled', True):
            return jsonify({
                'status': 'error',
                'message': 'Manifest feature is disabled'
            }), 403
            
        data = request.get_json()
        if not data or 'source_file' not in data or 'target_file' not in data:
            return jsonify({'status': 'error', 'message': 'Missing file selection'}), 400
            
        source_file = os.path.join(config['system1_manifest_dir'], data['source_file'])
        target_file = os.path.join(config['system2_manifest_dir'], data['target_file'])
        
        differences = compare_manifests(source_file, target_file)
        return jsonify({'status': 'success', 'differences': differences})
        
    except Exception as e:
        logger.error(f"Comparison error: {str(e)}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/compare_all_manifests', methods=['POST'])
def compare_all_manifests_endpoint():
    try:
        config = load_config()
        if not config.get('manifest_enabled', True):
            return jsonify({
                'status': 'error',
                'message': 'Manifest feature is disabled'
            }), 403
            
        system1_dir = config.get('system1_manifest_dir', '')
        system2_dir = config.get('system2_manifest_dir', '')
        
        results = compare_all_manifests(system1_dir, system2_dir)
        return jsonify({'status': 'success', 'results': results})
        
    except Exception as e:
        logger.error(f"Compare all error: {str(e)}")
        return jsonify({'status': 'error', 'message': str(e)}), 500