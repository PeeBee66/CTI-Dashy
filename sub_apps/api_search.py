from datetime import datetime
import pytz 
import os
from flask import Blueprint, session, render_template, request
import configparser
from pycti import OpenCTIApiClient

api_search_bp = Blueprint('api_search', __name__, url_prefix='/api_search')

@api_search_bp.route('/', methods=['GET', 'POST'])
def api_search():
    if request.method == 'POST':
        query = request.form.get('q')
        if query:
            environment = "your_environment_value"  # Replace this with your actual environment value
            results, more_results, no_results, api_error = perform_search(query, environment)

            if api_error:
                error_message = "Unable to connect to OpenCTI API"
                return render_template('api_search.html', error_message=error_message, api_error=True)

            if no_results:
                return render_template('api_search.html', no_results=True)

            return render_template('api_search.html', data=results, more_results=more_results)

    return render_template('api_search.html', data=[], no_results=False)


def perform_search(query, environment):
    config = configparser.ConfigParser()
    ip_address = 'localhost'
    api_key = 'your-default-api-key'
    port = 4000
    
    if os.path.exists('config/dashy.conf'):
        config.read('config/dashy.conf')
        ip_address = config.get('api_search.py', 'ip_address', fallback=ip_address)
        api_key = config.get('api_search.py', 'api_key', fallback=api_key)
        port = config.get('api_search.py', 'port', fallback=port) 

    URL = f"http://{ip_address}:{port}"

    api_error = False
    no_results = False
    results = []
    indicators = []

    try:
        api = OpenCTIApiClient(url=URL, token=api_key, log_level="info", ssl_verify=False)
        indicators = api.stix_domain_object.list(search=query)

        username = session.get('current_username', 'Unknown User')
        print(f"'{username}' API Search: {query}")

        if not indicators:
            no_results = True


        for index, indicator in enumerate(indicators):
            if index >= 25:  # Limit to 25 entries
                break

            result = {}
            result['Number'] = index + 1
            result['Name'] = indicator.get('name')
            result['Type'] = indicator.get('entity_type')

            created_by_info = indicator.get('createdBy', {})
            author_name = created_by_info.get('name', 'N/A')
            result['Author'] = author_name

            creator_id = created_by_info.get('id', 'N/A')
            result['Creator'] = creator_id

            confidence = indicator.get('confidence', 0)
            result['Confidence'] = confidence
            result['ConfidenceText'] = f'Confidence: {confidence}'
            result['ConfidenceColor'] = get_confidence_color(confidence)

            result['Description'] = indicator.get('description')

            date_created = datetime.strptime(indicator.get('created'), '%Y-%m-%dT%H:%M:%S.%fZ')
            date_created_str = date_created.strftime('%B %d, %Y at %I:%M:%S %p zulu')
            result['DateCreated'] = date_created_str

            modified_datetime = datetime.strptime(indicator.get('modified'), '%Y-%m-%dT%H:%M:%S.%fZ')
            last_seen_str = modified_datetime.strftime('%B %d, %Y at %I:%M:%S %p zulu')
            result['LastSeen'] = last_seen_str

            result['SearchLink'] = f'{URL}/dashboard/search/"{result["Name"].replace(" ", "%20")}"'
            results.append(result)

    except Exception as e:
        print("Error connecting to the OpenCTI API:", str(e))
        api_error = True

    return results, len(indicators) > 25, no_results, api_error


def get_confidence_color(confidence):
    if 0 <= confidence <= 20:
        return '#ff0000'
    elif 21 <= confidence <= 40:
        return '#ffa700'
    elif 41 <= confidence <= 60:
        return '#fff400'
    elif 61 <= confidence <= 80:
        return '#a3ff00'
    elif 81 <= confidence <= 100:
        return '#2cba00'
    else:
        return '#000000'  
