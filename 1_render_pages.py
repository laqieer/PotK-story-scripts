import json
import os
import sys
import shutil
import warnings

script_ids = sorted([int(file[:-4]) for file in os.listdir('scripts/') if file.endswith('.txt')])

def load_unit_data(masterdata_folder):
    unit_data = {}
    unit_ids_by_name = {}
    unit_file = os.path.join(masterdata_folder, 'UnitUnit.json')
    with open(unit_file, 'r', encoding='utf-8') as f_unit:
        data = json.load(f_unit)
        for unit in data:
            unit_data[unit['ID']] = unit
            if unit['name'] not in unit_ids_by_name:
                unit_ids_by_name[unit['name']] = []    
            unit_ids_by_name[unit['name']].append(unit['ID'])
    return unit_data, unit_ids_by_name

def parse_script_files(masterdata_folder, extracted_folder):
    unit_data, unit_ids_by_name = load_unit_data(masterdata_folder)
    for script_index, script_id in enumerate(script_ids):
        script_file = os.path.join('scripts/', f"{script_id}.txt")
        page_file = os.path.join('pages/', f"{script_id}.md")
        print(f"Processing {script_file}")
        with open(script_file, "r", encoding='utf-8') as f_script, open(page_file, 'w', encoding='utf-8') as f_page:
            f_page.write(f"[View script in lisp](../scripts/{script_id}.txt)\n")
            lines = f_script.readlines()
            units = {}
            for line in lines:
                if not line.strip() or line.startswith(';;'):
                    continue
                if line.startswith('#'):
                    lispAction = line[1:].strip().split(' ')
                    lispAction = [x for x in lispAction if x]
                    match lispAction[0]:
                        case 'background':
                            background = lispAction[1].replace('"','') + '.png'
                            background_path = 'images/backgrounds/' + background
                            f_page.write(f"\n![{background}](../{background_path})\n")
                            if not os.path.exists(background_path):
                                try:
                                    shutil.copy(os.path.join(extracted_folder, 'Prefabs/BackGround/', background), background_path)
                                except FileNotFoundError:
                                    warnings.warn(f"Background image {background} not found")
                        case 'select':
                            f_page.write("\n選択肢:\n")
                            for i in range(1, len(lispAction) - 1, 2):
                                text = lispAction[i].replace('"','')
                                label = lispAction[i + 1].replace('"','')
                                f_page.write(f"- {text} → [{label}](#{label})へ\n")
                            f_page.write("\n")
                        case 'label':
                            label = lispAction[1].replace('"','')
                            f_page.write(f"\n#### {label}:\n")
                        case 'labeljump':
                            label = lispAction[1].replace('"','')
                            f_page.write(f" → [{label}](#{label})へ\n")
                        case 'body':
                            uid = int(lispAction[1])
                            units[uid] = {
                                'uid': uid,
                                'name': unit_data[uid]['name'] if uid in unit_data else None,
                                'hidden': False,
                            }
                        case 'chara':
                            if len(lispAction) > 1:
                                try:
                                    uid = int(lispAction[1])
                                    units[uid] = {
                                        'uid': uid,
                                        'name': unit_data[uid]['name'] if uid in unit_data else None,
                                        'hidden': False,
                                    }
                                except ValueError:
                                    pass
                        case 'entry':
                            eid = int(lispAction[1])
                            uid = int(lispAction[2])
                            units[eid] = {
                                'uid': uid,
                                'name': unit_data[uid]['name'] if uid in unit_data else None,
                                'hidden': False,
                            }
                        case 'clone':
                            eid = int(lispAction[1])
                            uid = int(lispAction[2])
                            units[eid] = {
                                'uid': uid,
                                'name': unit_data[uid]['name'] if uid in unit_data else None,
                                'hidden': False,
                            }
                        case 'face':
                            if len(lispAction) > 1:
                                uid = lispAction[1]
                                try:
                                    uid = int(uid)
                                    if uid in units:
                                        units[uid]['hidden'] = False
                                except ValueError:
                                    pass
                        case 'alpha':
                            uid = int(lispAction[1])
                            if uid in units:
                                units[uid]['hidden'] = False
                                alpha = lispAction[2]
                                try:
                                    alpha = float(alpha)
                                    if alpha == 0:
                                        units[uid]['hidden'] = True
                                except ValueError:
                                    pass
                elif line.startswith('@'):
                    speaker = line[1:].strip()
                    if speaker:
                        # active_units = [units[eid]['uid'] for eid in units if not units[eid]['hidden']]
                        active_units = [units[eid]['uid'] for eid in units]
                        active_unit = None
                        if len(active_units) > 0: # has face
                            for uid in active_units:
                                if uid in unit_data and unit_data[uid]['name'] == speaker:
                                    active_unit = uid
                                    break
                            for uid in active_units:
                                # if uid in unit_data and speaker in [unit_data[unit_id]['name'] for unit_id in unit_data if unit_data[unit_id]['same_character_id'] == unit_data[uid]['same_character_id']]:
                                if uid in unit_data and speaker in unit_ids_by_name:
                                    for unit_id in unit_ids_by_name[speaker]:
                                        if unit_data[unit_id]['same_character_id'] == unit_data[uid]['same_character_id'] or unit_data[unit_id]['resource_reference_unit_id_UnitUnit'] == unit_data[uid]['resource_reference_unit_id_UnitUnit']:
                                            active_unit = uid
                                            break
                                    if active_unit is not None:
                                        break
                            if active_unit is None:
                                for uid in active_units:
                                    if uid in unit_data and unit_data[uid]['name'].startswith(speaker):
                                        active_unit = uid
                                        break
                            if active_unit is None:
                                for uid in active_units:
                                    if uid in unit_data and speaker in unit_data[uid]['name']:
                                        active_unit = uid
                                        break
                            if active_unit is not None:
                                if active_unit in unit_data: # not mob unit
                                    res_ref_unit_id = unit_data[active_unit]['resource_reference_unit_id_UnitUnit']
                                    unit_thumb = f'images/units/{res_ref_unit_id}.png'
                                    if not os.path.exists(unit_thumb):
                                        try:
                                            shutil.copy(os.path.join(extracted_folder, f'StreamingAssets/AssetBundle/Resources/Units/{res_ref_unit_id}/2D/c_thum.png'), unit_thumb)
                                        except FileNotFoundError:
                                            warnings.warn(f"Unit {res_ref_unit_id} thumbnail not found")
                                    # f_page.write(f"\n![{res_ref_unit_id}.png](../{unit_thumb})")
                                    f_page.write(f'\n<img src="../{unit_thumb}" alt="{res_ref_unit_id}.png" height="34"/>\n')
                        f_page.write(f"\n**【{speaker}】**\n")
                    else:
                        f_page.write("\n")
                else:
                    f_page.write(line)
            if script_index < len(script_ids) - 1:
                f_page.write(f"\n\nNext: [{script_ids[script_index + 1]}]({script_ids[script_index + 1]}.md)")
            f_page.write("\n\n[Back to index](index.md)\n")

def build_index_page():
    index_page = 'scripts/index.md'
    with open(index_page, 'w', encoding='utf-8') as f_index:
        f_index.write("# Scripts\n\n")
        for script_id in script_ids:
            f_index.write(f"- [{script_id}]({script_id}.txt)\n")
    index_page = 'pages/index.md'
    with open(index_page, 'w', encoding='utf-8') as f_index:
        f_index.write("# Pages\n\n")
        for script_id in script_ids:
            f_index.write(f"- [{script_id}]({script_id}.md)\n")


# Check if the input folder path is provided as a command line argument
if len(sys.argv) > 1:
    masterdata_folder = sys.argv[1]
else:
    # If no command line argument is provided, prompt the user to enter the input folder path
    masterdata_folder = input("Enter the path to masterdata folder: ")

masterdata_folder = os.path.join(masterdata_folder, 'masterdata/')

# Check if the input folder path is provided as a command line argument
if len(sys.argv) > 2:
    extracted_folder = sys.argv[2]
else:
    # If no command line argument is provided, prompt the user to enter the input folder path
    extracted_folder = input("Enter the path to extracted folder: ")

extracted_folder = os.path.join(extracted_folder, 'extracted/')

parse_script_files(masterdata_folder, extracted_folder)

build_index_page()
