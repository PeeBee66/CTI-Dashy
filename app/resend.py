import os
import logging
import csv
from datetime import datetime
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

def parse_date_from_datetime(dt_str):
    """Parse date object from datetime string for filtering - tries multiple formats"""
    if not dt_str:
        return None

    dt_str = dt_str.strip()

    # Try multiple date formats
    formats = [
        "%a %b %d %H:%M:%S UTC %Y",  # Wed Jan 29 14:23:45 UTC 2025
        "%Y-%m-%d %H:%M:%S",          # 2025-01-29 14:23:45
        "%Y-%m-%dT%H:%M:%S",          # 2025-01-29T14:23:45
        "%d/%m/%Y %H:%M:%S",          # 29/01/2025 14:23:45
        "%m/%d/%Y %H:%M:%S",          # 01/29/2025 14:23:45
    ]

    for fmt in formats:
        try:
            dt = datetime.strptime(dt_str, fmt)
            return dt.date()
        except ValueError:
            continue

    # If no format matched, log at debug level and return None
    logger.debug(f"Could not parse date from: {dt_str}")
    return None

def process_single_resend(file_data, config):
    """Process a single file resend operation - creates a .txt file with file metadata"""
    try:
        md5_hash = file_data.get('MD5Hash', '').strip()
        filename = file_data.get('Filename', '').strip()
        feed = file_data.get('CTIfeed', '').strip()

        logger.info(f"Processing: {filename}, MD5: {md5_hash[:20] if md5_hash else 'EMPTY'}...")

        if not md5_hash or not filename:
            return {
                'file': filename or 'Unknown',
                'status': 'error',
                'message': 'Missing MD5Hash or Filename'
            }

        resend_folder = config.get('resend_folder', '').strip()
        if not resend_folder:
            # Default to app/resend_queue
            resend_folder = os.path.join(os.path.dirname(__file__), 'resend_queue')

        os.makedirs(resend_folder, exist_ok=True)

        txt_filename = f"{md5_hash}.txt"
        txt_path = os.path.join(resend_folder, txt_filename)

        content = f"file name: {filename}\nCTIfeed: {feed}\nMD5Hash: {md5_hash}\n"

        with open(txt_path, 'w') as f:
            f.write(content)

        logger.info(f"Created resend request: {txt_path}")

        return {
            'file': filename,
            'status': 'success',
            'message': 'Resend request created',
            'txt_path': txt_path
        }

    except Exception as e:
        logger.error(f"Error processing {file_data.get('Filename', 'Unknown')}: {str(e)}")
        return {
            'file': file_data.get('Filename', 'Unknown'),
            'status': 'error',
            'message': str(e)
        }

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

@app.route('/refresh_resend_manifests', methods=['POST'])
def refresh_resend_manifests():
    try:
        config = load_config()
        if not config.get('resend_enabled', True):
            return jsonify({
                'status': 'error',
                'message': 'Resend feature is disabled'
            }), 403
            
        manifests = get_manifest_contents(config.get('resend_manifest_dir', ''))
        return jsonify({
            'status': 'success',
            'manifests': manifests
        })
        
    except Exception as e:
        logger.error(f"Refresh error: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

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

        if not data or not all(key in data for key in ['Filename', 'MD5Hash']):
            return jsonify({
                'status': 'error',
                'message': 'Missing required file information (Filename, MD5Hash)'
            }), 400

        result = process_single_resend(data, config)

        if result['status'] == 'success':
            return jsonify({
                'status': 'success',
                'message': result['message'],
                'details': {
                    'txt_path': result.get('txt_path', '')
                }
            })
        else:
            return jsonify({
                'status': 'error',
                'message': result['message']
            }), 500
        
    except Exception as e:
        logger.error(f"Resend error: {str(e)}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/filter_files', methods=['POST'])
def filter_files():
    """Filter manifest files by criteria (manifest names, date range, feed)"""
    try:
        config = load_config()
        if not config.get('resend_enabled', True):
            return jsonify({
                'status': 'error',
                'message': 'Resend feature is disabled'
            }), 403

        data = request.get_json()
        manifest_dir = config.get('resend_manifest_dir', '')

        manifest_names = data.get('manifest_files', [])
        date_from_str = data.get('date_from', '').strip()
        date_to_str = data.get('date_to', '').strip()
        feed_filter = data.get('feed_filter', '').strip()

        # Parse date filters
        date_from = None
        date_to = None
        if date_from_str:
            try:
                date_from = datetime.strptime(date_from_str, "%Y-%m-%d").date()
            except Exception as e:
                logger.error(f"Invalid date_from format: {date_from_str}")

        if date_to_str:
            try:
                date_to = datetime.strptime(date_to_str, "%Y-%m-%d").date()
            except Exception as e:
                logger.error(f"Invalid date_to format: {date_to_str}")

        # If no manifests specified, use all
        if not manifest_names:
            all_manifests = get_manifest_contents(manifest_dir)
            manifest_names = [m['name'] for m in all_manifests]

        # Read and filter files
        filtered_files = []
        for manifest_name in manifest_names:
            file_path = os.path.join(manifest_dir, manifest_name)
            if not os.path.exists(file_path):
                continue

            manifest_results = read_manifest_file(file_path)
            for row in manifest_results:
                # Apply feed filter
                if feed_filter and feed_filter.lower() not in row.get('CTIfeed', '').lower():
                    continue

                # Apply date filter
                if date_from or date_to:
                    file_date = parse_date_from_datetime(row.get('DateTime', ''))
                    if not file_date:
                        continue
                    if date_from and file_date < date_from:
                        continue
                    if date_to and file_date > date_to:
                        continue

                row['ManifestFile'] = manifest_name
                filtered_files.append(row)

        logger.info(f"Filtered {len(filtered_files)} files from {len(manifest_names)} manifests")
        return jsonify({
            'status': 'success',
            'files': filtered_files,
            'count': len(filtered_files)
        })

    except Exception as e:
        logger.error(f"Filter error: {str(e)}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/bulk_resend', methods=['POST'])
def bulk_resend():
    """Process multiple file resends in bulk"""
    try:
        config = load_config()
        if not config.get('resend_enabled', True):
            return jsonify({
                'status': 'error',
                'message': 'Resend feature is disabled'
            }), 403

        data = request.get_json()
        files = data.get('files', [])

        if not files:
            return jsonify({
                'status': 'error',
                'message': 'No files provided for bulk resend'
            }), 400

        logger.info(f"Processing bulk resend for {len(files)} files")
        logger.info(f"Files received: {[f.get('Filename', 'Unknown') for f in files]}")

        success_results = []
        failed_results = []

        for file_data in files:
            result = process_single_resend(file_data, config)

            if result['status'] == 'success':
                success_results.append(result)
            else:
                failed_results.append(result)

        logger.info(f"Bulk resend complete: {len(success_results)} succeeded, {len(failed_results)} failed")

        return jsonify({
            'status': 'success',
            'summary': {
                'total': len(files),
                'succeeded': len(success_results),
                'failed': len(failed_results)
            },
            'results': {
                'success': success_results,
                'failed': failed_results
            }
        })

    except Exception as e:
        logger.error(f"Bulk resend error: {str(e)}")
        return jsonify({'status': 'error', 'message': str(e)}), 500