import os
import sys
import shutil
import warnings

script_ids = sorted([int(file[:-4]) for file in os.listdir('scripts/') if file.endswith('.txt')])

def parse_script_files(extracted_folder):
    for i, script_id in enumerate(script_ids):
        script_file = os.path.join('scripts/', f"{script_id}.txt")
        page_file = os.path.join('pages/', f"{script_id}.md")
        print(f"Processing {script_file}")
        with open(script_file, "r", encoding='utf-8') as f_script, open(page_file, 'w', encoding='utf-8') as f_page:
            f_page.write(f"[View script in lisp](../scripts/{script_id}.txt)\n")
            lines = f_script.readlines()
            for line in lines:
                if not line.strip() or line.startswith(';;'):
                    continue
                if line.startswith('#'):
                    lispAction = line[1:].strip().split(' ')
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
                elif line.startswith('@'):
                    speaker = line[1:].strip()
                    if speaker:
                        f_page.write(f"\n**【{speaker}】**\n")
                    else:
                        f_page.write("\n")
                else:
                    f_page.write(line)
            if i < len(script_ids) - 1:
                f_page.write(f"\n\nNext: [{script_ids[i+1]}]({script_ids[i+1]}.md)")
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
    extracted_folder = sys.argv[1]
else:
    # If no command line argument is provided, prompt the user to enter the input folder path
    extracted_folder = input("Enter the path to extracted folder: ")

extracted_folder = os.path.join(extracted_folder, 'extracted/')

parse_script_files(extracted_folder)

build_index_page()
