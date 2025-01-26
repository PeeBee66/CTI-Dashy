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
    
    config = load_config()
    opencti_url = config.get('opencti_url', '').strip()
    api_key = config.get('opencti_api', '').strip()
    
    if not opencti_url or not api_key:
        return jsonify({'error': 'OpenCTI configuration missing'}), 400

    if not opencti_url.startswith(('http://', 'https://')):
        opencti_url = 'http://' + opencti_url
    
    graphql_endpoint = urljoin(opencti_url.rstrip('/') + '/', 'graphql')
    logger.info(f"GraphQL endpoint: {graphql_endpoint}")

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
    
    try:
        response = requests.post(
            graphql_endpoint,
            json={'query': query_string, 'variables': {'search': query}},
            headers=headers,
            verify=False,  # Changed to match settings.py
            timeout=30
        )
        
        logger.info(f"Response status: {response.status_code}")
        logger.debug(f"Response content: {response.text}")
        
        response.raise_for_status()
        data = response.json()
        
        if 'errors' in data:
            error_msg = data['errors'][0].get('message', 'Unknown GraphQL error')
            logger.error(f"GraphQL error: {error_msg}")
            return jsonify({'error': f'GraphQL error: {error_msg}'}), 400
            
        if 'data' in data and 'stixCoreObjects' in data['data']:
            results = []
            for edge in data['data']['stixCoreObjects']['edges']:
                node = edge['node']
                result = {
                    'id': node.get('id'),
                    'type': node.get('entity_type'),
                    'created': node.get('created_at'),
                    'updated': node.get('updated_at'),
                    'author': node.get('createdBy', {}).get('name'),
                    'markings': [m.get('definition') for m in node.get('objectMarking', [])],
                    'labels': [l.get('value') for l in node.get('objectLabel', [])],
                    'name': node.get('name'),
                    'description': node.get('description')
                }
                results.append(result)
            
            return jsonify({'results': results})
            
        return jsonify({'error': 'No results found'}), 404
            
    except requests.exceptions.SSLError as e:
        logger.error(f"SSL Error: {str(e)}")
        return jsonify({'error': 'SSL verification failed'}), 500
        
    except requests.exceptions.Timeout as e:
        logger.error(f"Timeout Error: {str(e)}")
        return jsonify({'error': 'Request timed out'}), 504
        
    except requests.exceptions.ConnectionError as e:
        logger.error(f"Connection Error: {str(e)}")
        return jsonify({'error': 'Failed to connect to OpenCTI server'}), 503
        
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        return jsonify({'error': 'An unexpected error occurred'}), 500