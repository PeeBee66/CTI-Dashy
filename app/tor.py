# app/tor.py
import os
import csv
import logging
import sys
from datetime import datetime
from flask import render_template, jsonify, send_from_directory

# Add the parent directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app
from app.config import load_config

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def read_tor_csv():
    try:
        # Get the latest CSV file from directory
        config = load_config()
        tor_dir = config.get('tor_csv_dir', '')
        
        if not tor_dir or not os.path.exists(tor_dir):
            return []
            
        # Get most recent CSV file
        files = [f for f in os.listdir(tor_dir) if f.endswith('.csv')]
        if not files:
            return []
            
        latest_file = max(files, key=lambda x: os.path.getctime(os.path.join(tor_dir, x)))
        file_path = os.path.join(tor_dir, latest_file)
        
        nodes = []
        with open(file_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                nodes.append({
                    'ip': row.get('IP', ''),
                    'is_exit': row.get('IsExit', '').lower() == 'exitnode',
                    'name': row.get('Name', 'Unnamed'),
                    'onion_port': row.get('OnionPort', ''),
                    'dir_port': row.get('DirPort', ''),
                    'flags': row.get('Flags', '').split(','),
                    'uptime': int(row.get('Uptime', 0)),
                    'version': row.get('Version', ''),
                    'contact': row.get('Contact', ''),
                    'collection_date': row.get('CollectionDate', '')
                })
        return nodes
    except Exception as e:
        logger.error(f"Error reading Tor CSV: {str(e)}")
        return []

@app.route('/tor')
def tor():
    config = load_config()
    if not config.get('tor_enabled', True):
        return render_template('feature_disabled.html',
                             feature_name='Tor',
                             active_tab='tor')
    
    nodes = read_tor_csv()
    return render_template('tor.html',
                         active_tab='tor',
                         nodes=nodes)

@app.route('/tor/nodes.csv')
def serve_tor_csv():
    config = load_config()
    tor_csv_dir = config.get('tor_csv_dir', '')
    
    if not tor_csv_dir or not os.path.exists(tor_csv_dir):
        return "Tor CSV directory not configured or not found", 404
    
    # Get the latest CSV file
    csv_files = [f for f in os.listdir(tor_csv_dir) if f.endswith('.csv')]
    if not csv_files:
        return "No CSV file available", 404
        
    latest_csv = max(csv_files, key=lambda x: os.path.getctime(os.path.join(tor_csv_dir, x)))
    file_path = os.path.join(tor_csv_dir, latest_csv)
    
    # Read and return the CSV content with text/plain content type
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        return content, 200, {'Content-Type': 'text/plain; charset=utf-8'}
    except Exception as e:
        return f"Error reading CSV file: {str(e)}", 500

@app.route('/refresh_tor_nodes', methods=['POST'])
def refresh_tor_nodes():
    try:
        config = load_config()
        if not config.get('tor_enabled', True):
            return jsonify({
                'status': 'error',
                'message': 'Tor feature is disabled'
            }), 403
            
        nodes = read_tor_csv()
        return jsonify({
            'status': 'success',
            'nodes': nodes
        })
        
    except Exception as e:
        logger.error(f"Refresh error: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

def get_file_info(file_path):
    """Get file information including size and modification time"""
    try:
        stats = os.stat(file_path)
        return {
            'size': stats.st_size,
            'modified': datetime.fromtimestamp(stats.st_mtime).strftime('%Y-%m-%d %H:%M:%S')
        }
    except Exception as e:
        logger.error(f"Error getting file info: {str(e)}")
        return None

@app.route('/tor/status')
def tor_status():
    """Get status of Tor CSV file and monitoring"""
    try:
        config = load_config()
        tor_csv_dir = config.get('tor_csv_dir', '')
        
        if not tor_csv_dir or not os.path.exists(tor_csv_dir):
            return jsonify({
                'status': 'error',
                'message': 'Tor CSV directory not configured or not found'
            }), 404
        
        csv_files = [f for f in os.listdir(tor_csv_dir) if f.endswith('.csv')]
        if not csv_files:
            return jsonify({
                'status': 'warning',
                'message': 'No CSV files found'
            })
            
        latest_csv = max(csv_files, key=lambda x: os.path.getctime(os.path.join(tor_csv_dir, x)))
        file_path = os.path.join(tor_csv_dir, latest_csv)
        file_info = get_file_info(file_path)
        
        return jsonify({
            'status': 'success',
            'data': {
                'filename': latest_csv,
                'file_info': file_info,
                'csv_url': f"/tor/nodes.csv",
                'enabled': config.get('tor_enabled', True)
            }
        })
        
    except Exception as e:
        logger.error(f"Status check error: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500