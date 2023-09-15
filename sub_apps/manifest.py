
import itertools
import os
import hashlib
import csv
import configparser
from flask import Flask, Blueprint, render_template
from jinja2 import Environment
from flask_login import login_required

manifest_bp = Blueprint('manifest', __name__, url_prefix='/manifest')

config = configparser.ConfigParser()
low_side_folder = 'Change/me/one'
high_side_folder = 'Change/me/two'
system_type = 'ChnageMe'
env = Environment()
env.filters['break'] = lambda x: x

try:
    if os.path.exists('config/dashy.conf'):
        config.read('config/dashy.conf')
        low_side_folder = config.get('manifest.py', 'low_side_folder', fallback=low_side_folder)
        high_side_folder = config.get('manifest.py', 'high_side_folder', fallback=high_side_folder)
        system_type = config.get('manifest.py', 'system_type', fallback=system_type)

    # Create the low side folder if it doesn't exist
    if not os.path.exists(low_side_folder):
        os.makedirs(low_side_folder)
        print(f"Low side folder '{low_side_folder}' created.")

    # Create the high side folder if it doesn't exist
    if not os.path.exists(high_side_folder):
        os.makedirs(high_side_folder)
        print(f"High side folder '{high_side_folder}' created.")

except Exception as e:
    print(f"An error occurred while reading the config file: {str(e)}")

# Function to calculate the MD5 hash of a string
def calculate_md5(string):
    md5_hash = hashlib.md5(string.encode()).hexdigest()
    return md5_hash

# Rest of your code...






if os.path.exists(low_side_folder):
    for filename in os.listdir(low_side_folder):
        # Check if the filename matches the system_type or system_type is "all"
        if system_type == "all" or f"CTImanifest_{system_type}" in filename:
            low_file = os.path.join(low_side_folder, filename)
            high_file = os.path.join(high_side_folder, filename)

            # Check if the file exists in the high folder
            if not os.path.isfile(high_file):  # File doesn't exist in the high folder
                print(f"Creating CSV in high side for: {filename}")

                # Write an empty CSV with the header row to the high-side folder
                header_row = ["Filename", "CTIFeed", "MD5Hash", "DateTime", "FileSize", "FlowUUID", "Resend"]
                with open(high_file, 'w', newline='') as file:
                    csv_writer = csv.writer(file)
                    csv_writer.writerow(header_row)

def compare_csv_contents(low_file, high_file):
    low_rows = read_csv_file(low_file)
    high_rows = read_csv_file(high_file)
    low_hashes = set(row[2] for row in low_rows[1:])
    return low_hashes == set(row[2] for row in high_rows[1:])

def read_csv_file(file_path):
    rows = []
    with open(file_path, 'r') as file:
        csv_reader = csv.reader(file)
        for row in csv_reader:
            rows.append(row)
    return convert_file_sizes(rows)



# Function to convert file sizes in the "FileSize" column to a readable format
def convert_file_sizes(rows):
    converted_rows = []
    for row in rows:
        converted_row = []
        for idx, value in enumerate(row):
            if idx == 4:  # Apply conversion only to the "FileSize" column (index 4)
                if value.isdigit():
                    size = int(value)
                    if size >= 1024 * 1024 * 1024:
                        size = f"{size / (1024 * 1024 * 1024):.2f} GB"
                    elif size >= 1024 * 1024:
                        size = f"{size / (1024 * 1024):.2f} MB"
                    elif size >= 1024:
                        size = f"{size / 1024:.2f} KB"
                    else:
                        size = f"{size} B"
                    converted_row.append(size)
                else:
                    converted_row.append(value)
            else:
                converted_row.append(value)
        converted_rows.append(converted_row)
    return converted_rows

for filename in os.listdir(low_side_folder):
    # Check if the filename matches the system_type or system_type is "all"
    if system_type == "all" or f"CTImanifest_{system_type}" in filename:
        low_file = os.path.join(low_side_folder, filename)
        high_file = os.path.join(high_side_folder, filename)

        # Check if the file exists in the high folder
        if not os.path.isfile(high_file):  # File doesn't exist in the high folder
            print(f"Creating CSV in high side for: {filename}")

            # Write an empty CSV with the header row to the high-side folder
            header_row = ["Filename", "CTIFeed", "MD5Hash", "DateTime", "FileSize", "FlowUUID", "Resend"]
            with open(high_file, 'w', newline='') as file:
                csv_writer = csv.writer(file)
                csv_writer.writerow(header_row)

@manifest_bp.route('/')
@login_required
def manifest():
    global low_side_folder, high_side_folder, system_type

    if os.path.exists('config/dashy.conf'):
        config.read('config/dashy.conf')
        low_side_folder = config.get('manifest', 'low_side_folder', fallback=low_side_folder)
        high_side_folder = config.get('manifest', 'high_side_folder', fallback=high_side_folder)
        system_type = config.get('manifest', 'system_type', fallback=system_type)
    else:
        return render_template('error.html', error_message="Config file not found")

    # Check if the low side folder exists
    if not os.path.exists(low_side_folder):
        error_message = "Low side folder not available"
        return render_template('error.html', error_message=error_message)

    # Check if the high side folder exists
    if not os.path.exists(high_side_folder):
        error_message = "High side folder not available"
        return render_template('error.html', error_message=error_message)

    # Create a list to store the tables
    tables = []

    # Get a list of filenames in both low and high side folders
    low_filenames = set(os.listdir(low_side_folder))
    high_filenames = set(os.listdir(high_side_folder))

    # Iterate over the files in the low folder
    for filename in os.listdir(low_side_folder):
        # Check if the filename matches the system_type or system_type is "all"
        if system_type == "all" or f"CTImanifest_{system_type}" in filename:
            low_file = os.path.join(low_side_folder, filename)
            high_file = os.path.join(high_side_folder, filename)

            # Check if the file exists in the high folder
            if os.path.isfile(high_file):
     
                # Read MD5 hashes from low CSV file, starting from line 2 (skip header)
                with open(low_file, 'r') as file:
                    low_csv_contents = file.readlines()[1:]
                low_hashes = [line.split(',')[2].strip() for line in low_csv_contents]

                # Read MD5 hashes from high CSV file, starting from line 2 (skip header)
                with open(high_file, 'r') as file:
                    high_csv_contents = file.readlines()[1:]
                high_hashes = [line.split(',')[2].strip() for line in high_csv_contents]



                # Compare MD5 hashes individually
                hash_results = []

                for low_hash in low_hashes:
                    hash_result = low_hash in high_hashes
                    hash_results.append(hash_result)


                # Check if there are any False hash results (i.e., not found in high hashes)
                file_status = "File Transferred" if all(hash_results) else "Missing File"
                
                # Get file size for low file
                low_file_size = os.path.getsize(low_file)
                
                # Read CSV contents and assign them to low_rows and high_rows
                low_rows = read_csv_file(low_file)
                high_rows = read_csv_file(high_file)
                
                # Create a list of tuples containing low_row and hash_result
                zipped_results = list(zip(low_rows[1:], hash_results))
                
                table = {
                    'filename': filename,
                    'low_file_size': low_file_size,
                    'file_status': file_status,
                    'low_rows': low_rows,
                    'high_rows': high_rows,
                    'zipped_results': zipped_results
                }

                tables.append(table)

    return render_template('manifest.html', tables=tables)
 
