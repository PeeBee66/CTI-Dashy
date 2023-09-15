import os
import csv
import configparser
from datetime import datetime
from pycti import OpenCTIApiClient
from flask import Flask, Blueprint, render_template, request, redirect, url_for
from flask_login import login_required

hash_search_bp = Blueprint('hash_search', __name__, url_prefix='/hash_search')

config = configparser.ConfigParser()
ip_address = 'localhost'
api_key = 'your-default-api-key'
port = 4000
csv_file = 'config/assit_list.csv'

if os.path.exists('config/dashy.conf'):
    config.read('config/dashy.conf')
    ip_address = config.get('hash_search.py', 'ip_address', fallback=ip_address)
    api_key = config.get('hash_search.py', 'api_key', fallback=api_key)
    port = config.get('hash_search.py', 'port', fallback=port)

URL = f"http://{ip_address}:{port}"

def perform_search(api, identifier):
    try:
        query = identifier
        indicators = api.stix_domain_object.list(search=query)

        results = []

        for index, indicator in enumerate(indicators):
            if index >= 10:
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

        if not results:
            error_result = {
                'Number': '1',
                'Type': 'Error',
                'Name': 'No search results found.',
                'Description': 'No search results found for this identifier.',
                'Author': 'CTI Dashy',
                'ConfidenceText': 'Confidence:',
                'Creator': '',
                'DateCreated': '',
                'LastSeen': '',
                'SearchLink': f'#{{ result["Identifier"] }}'
            }
            results.append(error_result)

        return results, False, None

    except Exception as e:
        print("An error occurred:", e)
        error_message = f"Error connecting to the OpenCTI API: {str(e)}"
        return None, True, error_message


@hash_search_bp.route('/generate_report')
@login_required
def generate_report():
    api_available = True
    data = []

    try:
        api = OpenCTIApiClient(url=URL, token=api_key, log_level="info", ssl_verify=False)
        api_error = False
    except Exception as e:
        api_error = True

    if api_error:
        return render_template('hash_search.html', api_error=True)

    try:
        with open(csv_file, 'r') as file:
            reader = csv.reader(file)
            for row in reader:
                identifier = row[2]
                results, no_results, error_message = perform_search(api, identifier)
                if no_results:
                    results = [{"Error": "No search results found for identifier"}]
                data.append({
                    "ID": row[0],
                    "Identifier": identifier,
                    "Results": results,
                    "ErrorMessage": error_message
                })
    except Exception as e:
        api_available = False
        error_message = "Unable to connect to OpenCTI API"

    if api_available:
        return render_template('report.html', data=data)
    else:
        return render_template('report.html', api_error=True, error_message=error_message)




@hash_search_bp.route('/')
@login_required
def hash_search():
    # Add your hash search view logic here
    return render_template('hash_search.html')

@hash_search_bp.route('/add', methods=['POST'])
@login_required
def add():
    id = get_next_id()
    hash_type = request.form['type']
    identifier = request.form['identifier']
    branch_area = request.form['branch_area']
    poc = request.form['poc']

    with open(csv_file, 'a', newline='') as file:
        writer = csv.writer(file)
        writer.writerow([id, hash_type, identifier, branch_area, poc])

    return redirect(url_for('hash_search.hash_search'))


@hash_search_bp.route('/table')
@login_required
def table():
    if not os.path.exists(csv_file):
        create_sample_csv(csv_file)  # Create the CSV file if not found
    
    data = []
    with open(csv_file, 'r') as file:
        reader = csv.reader(file)
        for row in reader:
            data.append(row)

    return render_template('table.html', data=data)


# Route to delete a row
@hash_search_bp.route('/delete/<int:index>')
@login_required
def delete(index):
    rows = []
    with open(csv_file, 'r') as file:
        reader = csv.reader(file)
        for row in reader:
            rows.append(row)

    del rows[index]

    with open(csv_file, 'w', newline='') as file:
        writer = csv.writer(file)
        writer.writerows(rows)

    return render_template('table.html', data=rows)

@hash_search_bp.route('/delete', methods=['POST'])
@login_required
def delete_row():
    row_id = request.form.get('row_id')

    # Open the CSV file and read its contents
    with open('config/assit_list.csv', 'r') as file:
        reader = csv.reader(file)
        rows = list(reader)

    # Find the index of the row with the given row_id
    row_index = None
    for i, row in enumerate(rows):
        if row[0] == row_id:
            row_index = i
            break

    # If the row_id is found, remove the row from the list
    if row_index is not None:
        rows.pop(row_index)

        # Write the updated contents back to the CSV file
        with open('config/assit_list.csv', 'w', newline='') as file:
            writer = csv.writer(file)
            writer.writerows(rows)

    # Redirect back to the table page after deletion
    return redirect(url_for('hash_search.table'))

def get_next_id():
    try:
        with open(csv_file, 'r') as file:
            reader = csv.reader(file)
            rows = list(reader)
            if rows:
                last_id = int(rows[-1][0])
                return last_id + 1
    except FileNotFoundError:
        pass

    return 1

def create_sample_csv(csv_file):
    sample_data = [
        "1,IP,152.32.157.157,Thunderbolt,Maxine Thompson",
        "2,IP,2001:41d0:1008:c3a::,Shadowhunter,Ethan Ramirez",
        "3,MD5,84E2F509D41B7566573277471068A803,Ironclad,Olivia Mitchell",
        "4,MALWARE,GusStuff,Viper,Caleb Johnson",
        "5,FQDN,jimmypickles.com.fl,Spectre,Maya Anderson",
        "6,IP,215.51.71.221,LoneWolf,Xavier Roberts",
        "7,MAC,A3:B7:4F:3C:55:33,WarriorPrincess,Ava Morgan"
    ]
    
    with open(csv_file, 'w', newline='') as file:
        for line in sample_data:
            file.write(line + '\n')


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
