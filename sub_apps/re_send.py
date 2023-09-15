from flask import Flask, session, flash, Blueprint, render_template, redirect, url_for, request
from configparser import ConfigParser
import csv
import os
import shutil
from flask_login import login_required

re_send_bp = Blueprint('re_send', __name__, url_prefix='/re_send')

config = ConfigParser()
storage_folder = '/mnt/opencti/dev'
queued_folder = '/mnt/opencti/dev'
low_side_folder = '/mnt/opencti/dev/manifest.csv'
system_type = 'prod'

if os.path.exists('config/dashy.conf'):
    config.read('config/dashy.conf')
    storage_folder = config.get('re_send.py', 'storage_folder', fallback=storage_folder)
    queued_folder = config.get('re_send.py', 'queued_folder', fallback=queued_folder)
    low_side_folder = config.get('manifest.py', 'low_side_folder', fallback=low_side_folder)
    system_type = config.get('manifest.py', 'system_type', fallback=system_type)


def file_exists(filename, ctifeed):
    config.read('config/dashy.conf')  # Read the configuration file
    storage_directory = config.get('re_send.py', 'storage_folder', fallback='/mnt/ctibackupdata')
    print(f"Configured storage directory: {storage_directory}")  # Debugging print

    source_path = os.path.join(storage_directory, ctifeed, filename)
    print(f"Checking if file exists: {source_path}")  # Debugging print

    if os.path.exists(source_path):
        return True
    else:
        print(f"File '{filename}' in '{ctifeed}' does not exist.")  # Debugging print
        return False


def get_csv_data():
    csv_data = []
    other_data = None

    files = os.listdir(low_side_folder)
    for file in files:
        if file.endswith('.csv'):
            table_name = file.split('.')[0]

            if table_name == 'CTImanifest_other':
                other_data = (table_name, read_csv_table(file))
            elif system_type == 'all' or table_name.startswith(f"CTImanifest_{system_type}"):
                csv_data.append((table_name, read_csv_table(file)))

    # Append the 'CTImanifest_other' data at the end
    if other_data:
        csv_data.append(other_data)

    return csv_data

def read_csv_table(file):
    table_data = []
    with open(os.path.join(low_side_folder, file), 'r') as csvfile:
        reader = csv.reader(csvfile)
        is_header_row = True
        for row in reader:
            if is_header_row:
                is_header_row = False
                continue

            # Check if the row has enough columns
            if len(row) >= 7:
                file_size_str = format_file_size(row[4])
                row[4] = file_size_str

                table_data.append([row[0], row[1], row[2], row[3], file_size_str, row[5], row[6]])
            else:
                # Handle the case where the row doesn't have enough columns
                # You might want to log a warning or handle this in a way that makes sense for your application
                print(f"Row {row} doesn't have enough columns")
                # Alternatively, you can skip appending this row to the table_data
                continue

    return table_data

def format_file_size(file_size):
    file_size = int(file_size)
    if file_size >= 1024 * 1024 * 1024:
        return f"{file_size / (1024 * 1024 * 1024):.2f} GB"
    else:
        return f"{file_size / (1024 * 1024):.2f} MB"


def update_csv_file(filename, ctifeed):
    config.read('config/dashy.conf')  # Read the configuration file
    low_side_folder = config.get('manifest.py', 'low_side_folder', fallback='/mnt/opencti/dev/manifest.csv')

    csv_file_path = os.path.join(low_side_folder, f"CTImanifest_{ctifeed}.csv")
    updated_rows = []

    with open(csv_file_path, 'r') as csvfile:
        reader = csv.reader(csvfile)
        for row in reader:
            if row[0] == filename:
                # Check if the "Resend" column value is empty or not a valid integer
                resent_value = row[-1]
                if resent_value and resent_value.isdigit():
                    row[-1] = str(int(resent_value) + 1)
                else:
                    row[-1] = '1'  # Set the initial value to 1 if empty or invalid
            updated_rows.append(row)

    with open(csv_file_path, 'w', newline='') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerows(updated_rows)



def copy_file_to_location(filename, ctifeed):
    config.read('config/dashy.conf')  # Read the configuration file
    storage_directory = config.get('re_send.py', 'storage_folder', fallback='/mnt/ctibackupdata')
    queued_directory = config.get('re_send.py', 'queued_folder', fallback='/mnt/connector')

    source_path = os.path.join(storage_directory, ctifeed, filename)
    destination_path = os.path.join(queued_directory, ctifeed, filename)

    if not os.path.exists(queued_directory):
        error_message = "The destination folder is invalid."
        return error_message

    try:
        shutil.copyfile(source_path, destination_path)
        print(f"Source: {filename} Destination: {filename} Transferred Successfully")
    except Exception as e:
        print(f"An error occurred while transferring {filename}: {e}")
        error_message = f"An error occurred while transferring {filename}: {e}"
        return error_message

    return None  # No error occurred, return None


@re_send_bp.route('/', methods=['GET', 'POST'])
@login_required
def re_send():
    if request.method == 'POST':
        filename = request.form.get('filename')
        ctifeed = request.form.get('ctifeed')

        # Now you have the filename and ctifeed values
        print(f"Resend requested for: {filename}, CTIFeed: {ctifeed}")

        # Call the function to copy the file
        error_message = copy_file_to_location(filename, ctifeed)

        if error_message:
            flash(error_message, 'error')
        else:
            flash("File transferred successfully.", 'success')
            # Update the CSV file
            update_csv_file(filename, ctifeed)

        return redirect(url_for('re_send.re_send'))  # Redirect back to the page

    # If it's a GET request, continue with the existing code to render the page
    try:
        csv_data = get_csv_data()
        return render_template('re_send.html', csv_data=csv_data)
    except FileNotFoundError as e:
        error_message = str(e)
        return render_template('error.html', error_message=error_message)


@re_send_bp.route('/delete/<path:filename>/<ctifeed>')
@login_required
def delete(filename, ctifeed):
    try:
        source_path = os.path.join(storage_folder, ctifeed, filename)
        queued_path = os.path.join(queued_folder, ctifeed, filename)

        if os.path.exists(source_path):
            os.remove(source_path)
            return redirect(url_for('re_send.re_send'))
        elif os.path.exists(queued_path):
            os.remove(queued_path)
            return redirect(url_for('re_send.re_send'))
        else:
            return "Source file not found or could not be deleted."
    except Exception as e:
        return f"An error occurred: {e}"


