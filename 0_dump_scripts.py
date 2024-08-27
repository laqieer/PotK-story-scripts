import os
import json
import sys

def dump_script_files(input_folder):
    json_files = [file for file in os.listdir(input_folder) if file.endswith('.json')]
    for file in json_files:
        file_path = os.path.join(input_folder, file)
        print(f"Processing {file_path}")
        with open(file_path, 'r', encoding='utf-8') as f_json, open(f'scripts/{file[:-5]}.txt', 'w', encoding='utf-8') as f_script:
            data = json.load(f_json)
            assert len(data) == 1, f"Expected 1 element in {file_path}, found {len(data)} elements"
            assert data[0]['ID'] == int(file[:-5]), f"Expected ID to be {file[:-5]}, found {data[0]['ID']}"
            f_script.write(data[0]['script'])

# Check if the input folder path is provided as a command line argument
if len(sys.argv) > 1:
    input_folder = sys.argv[1]
else:
    # If no command line argument is provided, prompt the user to enter the input folder path
    input_folder = input("Enter the path to masterdata/ScriptScript folder: ")

input_folder = os.path.join(input_folder, 'masterdata/ScriptScript')

dump_script_files(input_folder)
