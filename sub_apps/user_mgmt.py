
# cat sub_apps/user_mgmt.py
import hashlib
import configparser
import os
import re
from email_validator import validate_email, EmailNotValidError
import random
import string
import secrets
import csv
import string
from flask import jsonify, Blueprint, render_template, request, redirect, url_for, current_app, send_file
from flask_login import login_required
from pycti import OpenCTIApiClient

user_mgmt_bp = Blueprint('user_mgmt', __name__, url_prefix='/user_mgmt')

#######              read config file            #######
config = configparser.ConfigParser()
ip_address = 'localhost'
api_key = 'your-default-api-key'
port = 4000
connector_group_id = '123456'

if os.path.exists('config/dashy.conf'):
    config.read('config/dashy.conf')
    ip_address = config.get('user_mgmt.py', 'ip_address', fallback=ip_address)
    api_key = config.get('user_mgmt.py', 'api_key', fallback=api_key)
    port = config.get('user_mgmt.py', 'port', fallback=port)
    connector_group_id = config.get('user_mgmt.py', 'connector_group_id', fallback=connector_group_id)


#######              API Details  file            #######

# API information
URL = f"http://{ip_address}:{port}"
TOKEN = api_key
api = None

try:
    # Try to establish a connection with the OpenCTI API
    api = OpenCTIApiClient(url=URL, token=TOKEN, log_level="info", ssl_verify=False)
except Exception as e:
    # Handle the connection error
    print("Error connecting to the OpenCTI API:", str(e))
    api = None  # Set api to None if the connection fails

#######              OpenCTI User iframes           #######

@user_mgmt_bp.route('/opencti_list')
@login_required
def opencti_list():
    try:
        # Fetch user data from the OpenCTI API
        if api:
            users = search_user("")  # Assuming you want to fetch all users without any search filter
        else:
            users = []  # If the API connection failed, set users to an empty list

        return render_template('user_mgmt/opencti_list.html', users=users)

    except Exception as e:
        # Handle any other errors that may occur during data retrieval
        print("Error fetching user data:", str(e))
        return render_template('error.html', error_message="Error fetching user data from OpenCTI API")


@user_mgmt_bp.route('/opencti_groups')
@login_required
def opencti_groups():
    try:
        # Fetch user data from the OpenCTI API
        if api:
            user_data = search_user("")  # Fetch user data using your search function
            formatted_user_data = format_user_data(user_data)
            users_with_groups = []

            for user in formatted_user_data:
                user_details = get_user_by_id(user['id'])
                groups = user_details.get('groups', {}).get('edges', [])

                user['groups'] = [{'id': group['node']['id'], 'name': group['node']['name']} for group in groups]

                is_connector = any(group['name'] == 'Connectors' for group in user['groups'])
                user['is_connector'] = is_connector
                users_with_groups.append(user)

            # Pass the connector_group_id to the template
            return render_template('user_mgmt/opencti_groups.html', users=users_with_groups, connector_group_id=connector_group_id)
        else:
            # Handle API connection error
            error_message = "Error connecting to the OpenCTI API."
            return render_template('error.html', error_message=error_message)

    except Exception as e:
        # Handle other errors
        print("Error fetching user group data:", str(e))
        return render_template('error.html', error_message="Error fetching user group data")


    except Exception as e:
        # Handle other errors
        print("Error fetching user group data:", str(e))
        return render_template('error.html', error_message="Error fetching user group data")


@user_mgmt_bp.route('/opencti_create')
@login_required
def opencti_create():
    return render_template('user_mgmt/opencti_create.html')


#######              Connector User Presets            #######

# Function to get the path to the user_template.csv file
def _preset_get_user_file_path():
    file_path = os.path.abspath(os.path.join("config", "user_template.csv"))
    return file_path


@user_mgmt_bp.route('/_preset_delete_user', methods=['POST'])
@login_required
def _preset_delete_user():
    username = request.form['username']

    # Read existing user data
    user_data = _preset_read_user_file()

    # Remove user with matching username
    user_data = [user for user in user_data if user['Username'] != username]

    # Write updated user data back to the file
    _preset_write_user_file(user_data)

    return redirect(url_for('user_mgmt.opencti_users'))




# Helper function to read the user_template.csv file
def _preset_read_user_file():
    user_data = []
    file_path = os.path.abspath(os.path.join("config", "user_template.csv"))

    if not os.path.exists(file_path):
        # Create the file with default data if it doesn't exist
        with open(file_path, 'w', newline='') as file:
            fieldnames = ['Username', 'Email']
            writer = csv.DictWriter(file, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerow({'Username': 'Template1', 'Email': 'template1@cti.local'})
            writer.writerow({'Username': 'Template2', 'Email': 'template2@cti.local'})

    # Read data from the file
    with open(file_path, 'r') as file:
        reader = csv.DictReader(file)
        for row in reader:
            user_data.append(row)
    return user_data

# Helper function to write user data to config/user_template.csv
def _preset_write_user_file(user_data):
    file_path = os.path.abspath(os.path.join("config", "user_template.csv"))
    with open(file_path, 'w', newline='') as file:
        fieldnames = ['Username', 'Email']
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(user_data)

# Route to download the CSV file
@user_mgmt_bp.route('/_preset_download_csv')
@login_required
def _preset_download_csv():
    file_path = os.path.abspath(os.path.join("config", "user_template.csv"))
    return send_file(file_path, as_attachment=True)



#######              Core Config            #######

@user_mgmt_bp.route('/')
@login_required
def user_mgmt():
    # Add your user management view logic here
    return render_template('user_mgmt.html')

@user_mgmt_bp.route('/dashy_users')
@login_required
def dashy_users():
    # Read user data from .user.txt
    users = read_user_file()
    return render_template('user_mgmt/dashy_users.html', users=users)

@user_mgmt_bp.route('/opencti_users')
@login_required
def opencti_users():
    try:
        # Check if the user_template.csv file exists and create it if not
        if not os.path.exists(_preset_get_user_file_path()):
            _preset_write_user_file([])  # Create the file with an empty list

        # Pull user data from the config file
        users = _preset_read_user_file()
        return render_template('user_mgmt/opencti_users.html', users=users)

    except ValueError as e:
        error_message = "Unable to fetch data from OpenCTI API. Please check your API settings in the settings page."
        return render_template('error.html', error_message=error_message)

@user_mgmt_bp.errorhandler(ValueError)
@login_required
def handle_value_error(error):
    error_message = "An unexpected error occurred. Please try again later."
    return render_template('error.html', error_message=error_message)

#######              Dashy user Config            #######

# Function to read the .user.txt file and extract user data
def read_user_file():
    users = []
    with open('config/.user.txt', 'r') as f:
        for line in f:
            users.append(line.strip().split(','))
    return users

# Function to write the updated user data to .user.txt
def write_user_file(users):
    with open('config/.user.txt', 'w') as f:
        for user in users:
            f.write(','.join(user) + '\n')

@user_mgmt_bp.route('/dashy_delete_user', methods=['POST'])
@login_required
def dashy_delete_user():
    username = request.form['username']

    # Read user data from .user.txt
    users = read_user_file()

    # Remove the user from the user list
    users = [user for user in users if user[0] != username]

    # Write the updated user data to .user.txt
    write_user_file(users)
    print(f"Dashy user '{username}' was deleted  successfully.")


    # Redirect back to the Dashy Users page
    return redirect(url_for('user_mgmt.dashy_users'))

@user_mgmt_bp.route('/dashy_update_user', methods=['POST'])
@login_required
def dashy_update_user():
    username = request.form['username']
    user_index = int(request.form['user_index'])

    # Read user data from .user.txt
    users = read_user_file()

    # Update the user's group based on the toggles
    for group in ['api_search', 'data_dupe', 'folder_size', 'hash_search', 're_send', 'manifest', 'settings', 'user_mgmt']:
        group_status = request.form.get(f'toggle_{group}')
       # print(f"Group: {group}, Status: {group_status}")

        if group_status == 'on':
            if group not in users[user_index][2:]:
                users[user_index].append(group)
                print(f"Dashy user '{username}' added to '{group}' successfully.")

        else:
            if group in users[user_index][2:]:
                users[user_index].remove(group)
                print(f"Dashy user '{username}' removed from '{group}' successfully.")

    # Write the updated user data to .user.txt
    write_user_file(users)

    # Redirect back to the Dashy Users page
    return redirect(url_for('user_mgmt.dashy_users'))

# Inside the dashy_add_user route
@user_mgmt_bp.route('/dashy_add_user', methods=['POST'])
@login_required
def dashy_add_user():
    username = request.form['username']
    password = request.form['password']

    # Convert the password to SHA-256
    hashed_password = hashlib.sha256(password.encode()).hexdigest()

    # Read the existing user data from .user.txt
    users = read_user_file()

    # Check if the user already exists
    for user in users:
        if user[0] == username:
            # User already exists, redirect back to the Dashy Users page
            return redirect(url_for('user_mgmt.dashy_users'))

    # Add the user to the user list with the 'api_search' group
    new_user = [username, hashed_password, 'api_search']
    users.append(new_user)

    # Write the updated user data to .user.txt
    write_user_file(users)
    print(f"New Dasy User '{username}' was created  successfully.")

    # Redirect back to the Dashy Users page
    return redirect(url_for('user_mgmt.dashy_users'))


#######   API LIST USERS #####


def get_user_by_id(user_id):
    response = api.query(
        """
        query UserQuery($id: String!) {
            user(id: $id) {
                id
                name
                ...User_user
            }
        }
        fragment User_user on User {
            id
            name
            description
            external
            user_email
            firstname
            lastname
            language
            api_token
            otp_activated
            roles {
                id
                name
                description
            }
            groups {
                edges {
                    node {
                        id
                        name
                        description
                    }
                }
            }
            objectOrganization {
                edges {
                    node {
                        id
                        name
                    }
                }
            }
            sessions {
                id
                created
                ttl
            }
        }
        """,
        {
            "id": user_id
        }
    )
    return response['data']['user']

@user_mgmt_bp.route('/delete_user', methods=['POST'])
@login_required
def delete_user():
    user_id = request.form['user_id']

    # Call the function to delete the user from the API
    delete_result = delete_user_by_id(user_id)

    if delete_result:
        # Redirect back to the user list page after successful deletion
        return redirect(url_for('user_mgmt.opencti_list'))
    else:
        # If deletion failed, show an error message or handle it as desired
        error_message = "Error deleting user."
        return render_template('error.html', error_message=error_message)

def delete_user_by_id(user_id):
    response = delete_user_api_query(user_id)
    if response:
        return response['data']['userEdit']['delete']
    return False


def delete_user_api_query(user_id):
    response = api.query(
        """
        mutation UserPopoverDeletionMutation($id: ID!) {
            userEdit(id: $id) {
                delete
            }
        }
        """,
        {
            "id": user_id
        }
    )
    return response



# API-related functions
def search_user(text):
    response = api.query(
        """
        query UsersLinesPaginationQuery(
            $search: String
            $count: Int!
            $cursor: ID
            $orderBy: UsersOrdering
            $orderMode: OrderingMode
        ) {
            ...UsersLines_data_2ltyuX
        }
        fragment UserLine_node on User {
            id
            name
            user_email
            firstname
            external
            lastname
            otp_activated
            created_at
        }
        fragment UsersLines_data_2ltyuX on Query {
            users(
                search: $search
                first: $count
                after: $cursor
                orderBy: $orderBy
                orderMode: $orderMode
            ) {
                edges {
                    node {
                        id
                        name
                        api_token
                        firstname
                        lastname
                        ...UserLine_node
                        __typename
                    }
                    cursor
                }
                pageInfo {
                    endCursor
                    hasNextPage
                    globalCount
                }
            }
        }
        """,
        {
            "search": text,
            "count": 25,
            "cursor": None,
            "orderBy": "name",
            "orderMode": "asc"
        }
    )
    return response['data']['users']['edges']

def get_all_users_from_api():
    # Implement the logic to fetch all user data from the OpenCTI API using the provided API query function.
    # For example, you can use the search_user function to search for all users and get their API token as well.
    users = search_user("")  # Use an empty string to search for all users
    return users



    #######   API LIST groups #####

@user_mgmt_bp.route('/add_group', methods=['POST'])
@login_required
def add_group():
    user_id = request.form.get('user_id')
    group_id = request.form.get('group_id')
    
    # Check if user_id and group_id are present in the form submission
    if user_id and group_id:
        response = add_group_member(group_id, user_id)
        if response:
            # Check if the response contains an 'errors' field
            if 'errors' in response:
                print('Failed to add the user to the group')
            else:
                print('User added to the group successfully')
        else:
            print('Failed to add the user to the group')
    else:
        print('Invalid form submission')
    
    # Redirect back to the user groups page
    return redirect(url_for('user_mgmt.opencti_groups'))


def add_group_member(group_id, user_id):
    response = api.query(
        """
        mutation GroupEditionUsersRelationAddMutation(
          $id: ID!
          $input: InternalRelationshipAddInput!
        ) {
          groupEdit(id: $id) {
            relationAdd(input: $input) {
              to {
                __typename
                ...GroupEditionUsers_group
                id
              }
              id
            }
          }
        }
        fragment GroupEditionUsers_group on Group {
          id
          members {
            edges {
              node {
                id
                name
              }
            }
          }
        }
        """,
        {
          "id": group_id,
          "input":{
            "fromId": user_id,
            "relationship_type":"member-of"}
        }
    )
    return response['data']['groupEdit']['relationAdd']



@user_mgmt_bp.route('/groups')
@login_required
def groups():
    try:
        # Fetch user data from the OpenCTI API
        if api:
            user_data = search_user("")  # Fetch user data using your search function
            formatted_user_data = format_user_data(user_data)
            users_with_groups = []

            for user in formatted_user_data:
                user_details = get_user_by_id(user['id'])
                print("User Details:", user_details)  # Print user details for debugging
                groups = user_details.get('groups', {}).get('edges', [])
                print("Groups:", groups)  # Print groups for debugging

                user['groups'] = [{'id': group['node']['id'], 'name': group['node']['name']} for group in groups]

                is_connector = any(group['name'] == 'Connectors' for group in user['groups'])
                user['is_connector'] = is_connector
                users_with_groups.append(user)

            print("Users with Groups:", users_with_groups)  # Print final users_with_groups for debugging

            return render_template('user_mgmt/opencti_groups.html', users=users_with_groups)
        else:
            # Handle API connection error
            error_message = "Error connecting to the OpenCTI API."
            return render_template('error.html', error_message=error_message)

    except Exception as e:
        # Handle other errors
        print("Error fetching user group data:", str(e))
        return render_template('error.html', error_message="Error fetching user group data")



  #######   CREATE USER  #####


def user_exists(name):
    user_data = search_user(name)
    return len(user_data) > 0


def is_valid_email(email):
    email_regex = r'^[\w\.-]+@[\w\.-]+\.\w+$'
    return re.match(email_regex, email) is not None



def get_users():
    # Replace this with your actual code to retrieve the list of users
    # For example, if you're using a database, you might have something like:
    # users = db.query("SELECT * FROM users")
    # return users
    # For now, let's return a dummy list for testing purposes
    return [{'Username': 'User1', 'Email': 'user1@example.com'}, {'Username': 'User2', 'Email': 'user2@example.com'}]
    
    
    
def create_user(email, name, password, firstname, lastname, description):
    if not firstname:
        firstname = ""
    if not lastname:
        lastname = ""
    if not description:
        description = ""

    try:
        response = api.query(
            """
            mutation UserAdd($input: UserAddInput!) {
                userAdd(input: $input) {
                    id
                }
            }
            """,
            {
                "input": {
                    "user_email": email,
                    "name": name,
                    "password": password,  # Corrected the variable name here
                    "firstname": firstname,
                    "lastname": lastname,
                    "description": description
                }
            }
        )
        return True
    except Exception as e:
        print("Error creating user:", str(e))
        return False

print('Created by PB')

@user_mgmt_bp.route('/create_user_route', methods=['POST'])
@login_required
def create_user_route():
    # Extract user data from the form
    username = request.form.get('username')
    email = request.form.get('email')
    password = request.form.get('password')
    firstname = None  # You can extract these fields similarly
    lastname = None
    description = None

    # Validate the email address format
    if not is_valid_email(email):
        message = "Invalid email address format."
    elif user_exists(username):
        message = "User already exists."
    else:
        # Call the create_user function to add the user to the OpenCTI API
        success = create_user(email, username, password, firstname, lastname, description)

        if success:
            message = "User created successfully."
        else:
            message = "Error creating user."

    # You can handle the 'message' variable as you did before
    return render_template('user_mgmt/opencti_create.html', message=message)


# Route to handle adding a user to the preset list
@user_mgmt_bp.route('/_preset_add_user', methods=['POST'])
@login_required
def _preset_add_user():
    data = request.form.to_dict()
    username = data.get('username')
    email = data.get('email')

    # Add the new user to the CSV file
    with open('config/user_template.csv', mode='a', newline='') as csvfile:
        csv_writer = csv.writer(csvfile)
        csv_writer.writerow([username, email])

    print(f"User {username} added to the preset list.")
    return redirect(url_for('user_mgmt.opencti_users'))


@user_mgmt_bp.route('/_preset_add_to_opencti', methods=['POST'])
@login_required
def _preset_add_to_opencti():
    username = request.form.get('username')
    email = request.form.get('email')

    # Generate a random password for the user
    password = generate_random_password()

    # Call the function to add user to OpenCTI API
    success = create_user(email, username, password, "", "", "")

    if success:
        success_message = f"User '{username}' added to OpenCTI with random password."
    else:
        success_message = f"Error adding user '{username}' to OpenCTI."

    # Update the 'success_message' in the template context
    users = _preset_read_user_file()
    return render_template('user_mgmt/opencti_users.html', users=users, success_message=success_message)




def generate_random_password(length=12):
    characters = string.ascii_letters + string.digits + string.punctuation
    return ''.join(random.choice(characters) for _ in range(length))

def is_valid_email(email):
    try:
        valid = validate_email(email)
        return True
    except EmailNotValidError:
        return False

def format_user_data(user_data):
    formatted_data = []
    for user_edge in user_data:
        user_node = user_edge['node']
        formatted_user = {
            'id': user_node['id'],
            'name': user_node['name'],
            'user_email': user_node['user_email'],
            'api_token': user_node['api_token']  # Add this line
        }
        formatted_data.append(formatted_user)
    return formatted_data 
