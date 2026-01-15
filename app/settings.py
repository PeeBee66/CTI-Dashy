# CTIDashy_Flask/app/settings.py
from flask import render_template, request, jsonify
from app import app
from app.config import load_config, save_config
import requests
from urllib.parse import urljoin

@app.route('/settings')
def settings():
    config = load_config()
    return render_template('settings.html', 
                         config=config, 
                         active_tab='settings')

@app.route('/update_settings', methods=['POST'])
def update_settings():
    try:
        config_data = {
            'opencti_url': request.form.get('opencti_url', ''),
            'opencti_api': request.form.get('opencti_api', ''),
            'low_side_manifest_dir': request.form.get('low_side_manifest_dir', ''),
            'high_side_manifest_dir': request.form.get('high_side_manifest_dir', ''),
            'resend_manifest_dir': request.form.get('resend_manifest_dir', ''),
            'feed_backup_dir': request.form.get('feed_backup_dir', ''),
            'resend_folder': request.form.get('resend_folder', ''),
            'manifest_enabled': request.form.get('manifest_enabled') == 'on',
            'resend_enabled': request.form.get('resend_enabled') == 'on'
        }
        save_config(config_data)
        return jsonify({'status': 'success', 'message': 'Settings saved successfully'})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/test_opencti', methods=['POST'])
def test_opencti():
    url = request.form.get('opencti_url', '').strip()
    api_key = request.form.get('opencti_api', '').strip()
    
    if not url or not api_key:
        return jsonify({'status': 'error', 'message': 'URL and API key are required'})

    # Ensure URL has proper structure
    if not url.startswith(('http://', 'https://')):
        url = 'http://' + url

    # Ensure URL ends with /graphql
    graphql_endpoint = urljoin(url.rstrip('/') + '/', 'graphql')

    query = """
    query {
        about {
            version
        }
    }
    """
    
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {api_key}'
    }
    
    try:
        response = requests.post(
            graphql_endpoint,
            json={'query': query},
            headers=headers,
            timeout=10,
            verify=False  # Add this if dealing with self-signed certs
        )
        
        response.raise_for_status()
        data = response.json()
        
        if 'errors' in data:
            return jsonify({'status': 'error', 'message': data['errors'][0].get('message', 'Unknown GraphQL error')})
            
        return jsonify({
            'status': 'success', 
            'message': f"Connected successfully! OpenCTI version: {data['data']['about']['version']}"
        })
            
    except requests.exceptions.RequestException as e:
        return jsonify({'status': 'error', 'message': f'Connection failed: {str(e)}'})