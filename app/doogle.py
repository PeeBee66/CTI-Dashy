# CTIDashy_Flask/app/doogle.py
import os
import sys
import logging
import requests
from urllib.parse import urljoin
from flask import jsonify, request
from app import app
from app.config import load_config

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@app.route('/search')
def search():
    query = request.args.get('q', '').strip()
    if not query:
        return jsonify({'error': 'No search query provided'}), 400
    
    try:
        config = load_config()
        opencti_url = config.get('opencti_url', '').strip()
        api_key = config.get('opencti_api', '').strip()
        
        if not opencti_url or not api_key:
            return jsonify({'error': 'OpenCTI configuration missing'}), 400

        if not opencti_url.startswith(('http://', 'https://')):
            opencti_url = 'http://' + opencti_url
        
        graphql_endpoint = urljoin(opencti_url.rstrip('/') + '/', 'graphql')

        query_string = """
        query Search($search: String) {
            stixCoreObjects(search: $search, first: 20) {
                edges {
                    node {
                        id
                        entity_type
                        standard_id
                        created_at
                        updated_at
                        createdBy {
                            name
                        }
                        objectMarking {
                            definition
                            x_opencti_color
                        }
                        objectLabel {
                            value
                            color
                        }
                        ... on Report {
                            name
                            description
                            report_types
                            published
                        }
                        ... on Organization {
                            name
                            description
                        }
                        ... on Indicator {
                            name
                            pattern
                            valid_from
                            valid_until
                        }
                    }
                }
            }
        }
        """
        
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {api_key}'
        }
        
        response = requests.post(
            graphql_endpoint,
            json={'query': query_string, 'variables': {'search': query}},
            headers=headers,
            verify=False,
            timeout=30
        )
        
        try:
            data = response.json()
        except ValueError:
            return jsonify({'error': 'Invalid JSON response'}), 500

        if data is None:
            return jsonify({'error': 'Empty response'}), 500
            
        if 'errors' in data:
            error_msg = data.get('errors', [{}])[0].get('message', 'Unknown GraphQL error')
            return jsonify({'error': f'GraphQL error: {error_msg}'}), 400

        stix_objects = data.get('data', {}).get('stixCoreObjects', {})
        if stix_objects is None:
            return jsonify({'results': []})

        edges = stix_objects.get('edges', [])
        if not edges:
            return jsonify({'results': []})

        results = []
        for edge in edges:
            if not edge:
                continue
                
            node = edge.get('node')
            if not node:
                continue
            
            created_by = node.get('createdBy') or {}
            result = {
                'id': node.get('id'),
                'type': node.get('entity_type'),
                'created': node.get('created_at'),
                'updated': node.get('updated_at'),
                'author': created_by.get('name'),
                'markings': [m.get('definition') for m in node.get('objectMarking', []) if m and m.get('definition')],
                'labels': [l.get('value') for l in node.get('objectLabel', []) if l and l.get('value')],
                'name': node.get('name', 'Unnamed Item'),
                'description': node.get('description', '')
            }
            results.append(result)
        
        return jsonify({'results': results})
            
    except requests.exceptions.SSLError as e:
        return jsonify({'error': 'SSL verification failed'}), 500
        
    except requests.exceptions.Timeout as e:
        return jsonify({'error': 'Request timed out'}), 504
        
    except requests.exceptions.ConnectionError as e:
        return jsonify({'error': 'Failed to connect to OpenCTI server'}), 503
        
    except Exception as e:
        return jsonify({'error': 'An unexpected error occurred'}), 500