import os
import logging
import csv
import shutil
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

def extract_year_from_datetime(dt_str):
    try:
        dt = datetime.strptime(dt_str.strip(), "%a %b %d %H:%M:%S UTC %Y")
        return str(dt.year)
    except Exception as e:
        logger.error(f"Error extracting year from {dt_str}: {str(e)}")
        return None

def parse_date_from_datetime(dt_str):
    """Parse date object from datetime string for filtering"""
    try:
        dt = datetime.strptime(dt_str.strip(), "%a %b %d %H:%M:%S UTC %Y")
        return dt.date()
    except Exception as e:
        logger.error(f"Error parsing date from {dt_str}: {str(e)}")
        return None

def process_single_resend(file_data, config):
    """Process a single file resend operation"""
    try:
        if not all(key in file_data for key in ['Filename', 'CTIfeed', 'DateTime']):
            return {
                'file': file_data.get('Filename', 'Unknown'),
                'status': 'error',
                'message': 'Missing required file information'
            }

        source_base = config.get('feed_backup_dir', '').strip()
        target_base = config.get('resend_folder', '').strip()

        if not source_base or not target_base:
            return {
                'file': file_data['Filename'],
                'status': 'error',
                'message': 'Feed backup or resend folders not configured'
            }

        year = extract_year_from_datetime(file_data['DateTime'])
        if not year:
            return {
                'file': file_data['Filename'],
                'status': 'error',
                'message': 'Could not determine year from DateTime'
            }

        feed_folder = file_data['CTIfeed']
        filename = file_data['Filename']

        source_path = os.path.join(source_base, feed_folder, year, filename)
        target_folder = os.path.join(target_base, feed_folder)
        target_path = os.path.join(target_folder, filename)

        if not os.path.exists(source_path):
            return {
                'file': filename,
                'status': 'error',
                'message': f'Source file not found: {source_path}'
            }

        os.makedirs(target_folder, mode=0o777, exist_ok=True)

        success, message = verify_file_transfer(source_path, target_path)

        if not success:
            return {
                'file': filename,
                'status': 'error',
                'message': f'Transfer verification failed: {message}'
            }

        return {
            'file': filename,
            'status': 'success',
            'message': 'File transferred successfully',
            'source_path': source_path,
            'target_path': target_path
        }

    except Exception as e:
        logger.error(f"Error processing {file_data.get('Filename', 'Unknown')}: {str(e)}")
        return {
            'file': file_data.get('Filename', 'Unknown'),
            'status': 'error',
            'message': str(e)
        }

def verify_file_transfer(source_path, target_path):
    """Verify file transfer by comparing file sizes, existence and permissions"""
    try:
        if not os.path.exists(source_path):
            return False, "Source file not found"
            
        target_dir = os.path.dirname(target_path)
        if not os.path.exists(target_dir):
            try:
                os.makedirs(target_dir, mode=0o777, exist_ok=True)
            except Exception as e:
                return False, f"Cannot create target directory: {str(e)}"
                
        if not os.access(target_dir, os.W_OK):
            return False, f"Target directory not writable: {target_dir}"
            
        try:
            shutil.copy2(source_path, target_path)
        except Exception as e:
            return False, f"Copy failed: {str(e)}"
            
        if not os.path.exists(target_path):
            return False, "Target file not created after copy attempt"
            
        source_size = os.path.getsize(source_path)
        target_size = os.path.getsize(target_path)
        
        if source_size != target_size:
            os.remove(target_path)
            return False, f"Size mismatch: Source={source_size}, Target={target_size}"
            
        source_perms = os.stat(source_path).st_mode
        target_perms = os.stat(target_path).st_mode
        if source_perms != target_perms:
            try:
                os.chmod(target_path, source_perms)
            except Exception as e:
                return False, f"Could not set target permissions: {str(e)}"
                
        return True, "File transfer verified successfully"
        
    except Exception as e:
        return False, f"Verification error: {str(e)}"

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
        
        if not data or not all(key in data for key in ['Filename', 'CTIfeed', 'DateTime']):
            return jsonify({
                'status': 'error', 
                'message': 'Missing required file information'
            }), 400
            
        source_base = config.get('feed_backup_dir', '').strip()
        target_base = config.get('resend_folder', '').strip()
        
        if not source_base or not target_base:
            return jsonify({
                'status': 'error',
                'message': 'Feed backup or resend folders not configured'
            }), 400

        year = extract_year_from_datetime(data['DateTime'])
        if not year:
            return jsonify({
                'status': 'error',
                'message': 'Could not determine year from DateTime'
            }), 400
            
        feed_folder = data['CTIfeed']
        filename = data['Filename']
        
        source_path = os.path.join(source_base, feed_folder, year, filename)
        target_folder = os.path.join(target_base, feed_folder)
        target_path = os.path.join(target_folder, filename)
        
        if not os.path.exists(source_path):
            return jsonify({
                'status': 'error',
                'message': f'Source file not found: {source_path}'
            }), 404
            
        os.makedirs(target_folder, mode=0o777, exist_ok=True)
        
        success, message = verify_file_transfer(source_path, target_path)
        
        if not success:
            return jsonify({
                'status': 'error',
                'message': f'Transfer verification failed: {message}'
            }), 500
            
        if not os.path.exists(target_path):
            return jsonify({
                'status': 'error',
                'message': 'File appears missing after successful transfer'
            }), 500
            
        return jsonify({
            'status': 'success',
            'message': f'File successfully copied from {source_path} to {target_path}',
            'details': {
                'source_path': source_path,
                'target_path': target_path,
                'verification': message
            }
        })
        
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