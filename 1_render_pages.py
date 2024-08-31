import json
import os
import sys
import shutil
import warnings

videos = {}

# get videos from wiki
with open('wiki/Videos.md', 'r', encoding='utf-8') as f:
    video_name = None
    for line in f.readlines():
        line = line.strip()
        if not line or line.startswith('#'):
            continue
        if '.mp4' in line:
            video_name = line[:-4]
        elif 'http' in line:
            video_url = line
            assert video_name is not None
            videos[video_name] = f'<video controls src="{video_url}" type="video/mp4"></video>'
            video_name = None

script_ids = sorted([int(file[:-4]) for file in os.listdir('scripts/') if file.endswith('.txt')])
script_names = {}

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

def load_mob_unit_data():
    mob_unit_data = {}
    with open('MobUnits.json', 'r', encoding='utf-8') as f_mob_unit:
        data = json.load(f_mob_unit)
        for mob_unit in data:
            mob_unit_data[mob_unit['ID']] = mob_unit
    return mob_unit_data

def parse_script_files(masterdata_folder, extracted_folder):
    unit_data, unit_ids_by_name = load_unit_data(masterdata_folder)
    mob_unit_data = load_mob_unit_data()
    for script_index, script_id in enumerate(script_ids):
        script_file = os.path.join('scripts/', f"{script_id}.txt")
        page_file = os.path.join('pages/', f"{script_id}.md")
        print(f"Processing {script_file}")
        with open(script_file, "r", encoding='utf-8') as f_script, open(page_file, 'w', encoding='utf-8') as f_page:
            f_page.write(f"{script_names.get(script_id, script_id)}\n\n")
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
                        if speaker == '%(userName)s':
                            speaker = 'ユーザー名'
                        else:
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
                                if active_unit is None:
                                    for uid in active_units:
                                        if uid in mob_unit_data and speaker in mob_unit_data[uid]['name']:
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
                                        f_page.write(f'\n<img src="../{unit_thumb}" alt="{res_ref_unit_id}.png" height="34"/>')
                                    elif active_unit in mob_unit_data:
                                        mob_unit_thumb = f'images/units/{active_unit}.png'
                                        assert os.path.exists(mob_unit_thumb), f"Mob unit {active_unit} thumbnail not found"
                                        f_page.write(f'\n<img src="../{mob_unit_thumb}" alt="{active_unit}.png" height="34"/>')
                        f_page.write(f"\n【{speaker}】\n")
                    else:
                        f_page.write("\n")
                else:
                    f_page.write(line.replace('%(userName)s','[ユーザー名]'))
            if script_index < len(script_ids) - 1:
                f_page.write(f"\n\nNext: [{script_ids[script_index + 1]}]({script_ids[script_index + 1]}.md)")
            f_page.write("\n\n[Back to index](index.md)\n")

def build_index_page(masterdata_folder):
    QuestStoryXL = {}
    with open(os.path.join(masterdata_folder, 'QuestStoryXL.json'), 'r', encoding='utf-8') as f_QuestStoryXL:
        data = json.load(f_QuestStoryXL)
        for d in data:
            QuestStoryXL[d['ID']] = d
    # index for EarthQuestStoryPlayback
    EarthQuestChapter = {}
    with open(os.path.join(masterdata_folder, 'EarthQuestChapter.json'), 'r', encoding='utf-8') as f_EarthQuestChapter:
        data = json.load(f_EarthQuestChapter)
        for d in data:
            d['episode_ids'] = []
            EarthQuestChapter[d['ID']] = d
    EarthQuestEpisode = {}
    with open(os.path.join(masterdata_folder, 'EarthQuestEpisode.json'), 'r', encoding='utf-8') as f_EarthQuestEpisode:
        data = json.load(f_EarthQuestEpisode)
        for d in data:
            d['story_ids'] = []
            EarthQuestEpisode[d['ID']] = d
            EarthQuestChapter[d['chapter_EarthQuestChapter']]['episode_ids'].append(d['ID'])
    with open(os.path.join(masterdata_folder, 'EarthQuestPologue.json'), 'r', encoding='utf-8') as f_EarthQuestPrologue:
        data = json.load(f_EarthQuestPrologue)
        for d in data:
            if d['type'] == 'movie':
                EarthQuestEpisode[d['episode_EarthQuestEpisode']]['EarthQuestPrologue'] = d['arg1']
    EarthQuestStoryPlayback = {}
    with open(os.path.join(masterdata_folder, 'EarthQuestStoryPlayback.json'), 'r', encoding='utf-8') as f_EarthQuestStoryPlayback:
        data = json.load(f_EarthQuestStoryPlayback)
        for d in data:
            EarthQuestStoryPlayback[d['ID']] = d
            EarthQuestEpisode[d['episode_EarthQuestEpisode']]['story_ids'].append(d['ID'])
    index_EarthQuestStoryPlayback = 'pages/EarthQuestStoryPlayback.md'
    with open(index_EarthQuestStoryPlayback, 'w', encoding='utf-8') as f_index:
        f_index.write(f"# {QuestStoryXL[2]['name']}\n\n")
        f_index.write(f"earth_prologue_5\n\n{videos['earth_prologue_5']}\n\n")
        for chapter in sorted(EarthQuestChapter.values(), key=lambda x: x['ID']):
            f_index.write(f"## {chapter['chapter']} {chapter['chapter_name']}\n\n")
            for episode_id in chapter['episode_ids']:
                episode = EarthQuestEpisode[episode_id]
                f_index.write(f"### {episode['episode_name']}\n\n")
                if 'EarthQuestPrologue' in episode:
                    assert episode['EarthQuestPrologue'] in videos, f"Video {episode['EarthQuestPrologue']} not found"
                    f_index.write(f"{episode['EarthQuestPrologue']}\n\n{videos[episode['EarthQuestPrologue']]}\n\n")
                for story_id in sorted(episode['story_ids'], key=lambda x: EarthQuestStoryPlayback[x]['timing_StoryPlaybackTiming']):
                    story = EarthQuestStoryPlayback[story_id]
                    script_id = story['script_id']
                    f_index.write(f"- [{script_id} {story['title']}]({script_id}.md)\n")
                    script_names[script_id] = ' '.join([str(script_id), QuestStoryXL[2]['name'], chapter['chapter'], chapter['chapter_name'], story['title']])
                if len(episode['story_ids']) > 0:
                    f_index.write("\n")
        f_index.write(f"earth_endroll\n\n{videos['earth_endroll']}\n\n")
    # index for StoryPlaybackCharacterDetail
    QuestCharacterM = {}
    with open(os.path.join(masterdata_folder, 'QuestCharacterM.json'), 'r', encoding='utf-8') as f_QuestCharacterM:
        data = json.load(f_QuestCharacterM)
        for d in data:
            d['QuestCharacterS'] = []
            QuestCharacterM[d['ID']] = d
    QuestCharacterL = {}
    for character_id in sorted(QuestCharacterM.keys()):
        characterM = QuestCharacterM[character_id]
        if characterM['name'].strip() not in QuestCharacterL:
            QuestCharacterL[characterM['name'].strip()] = {
                'QuestCharacterM': [],
            }
        QuestCharacterL[characterM['name'].strip()]['QuestCharacterM'].append(character_id)
    QuestCharacterS = {}
    with open(os.path.join(masterdata_folder, 'QuestCharacterS.json'), 'r', encoding='utf-8') as f_QuestCharacterS:
        data = json.load(f_QuestCharacterS)
        for d in data:
            d['StoryPlaybackCharacter'] = []
            QuestCharacterS[d['ID']] = d
            QuestCharacterM[d['quest_m_QuestCharacterM']]['QuestCharacterS'].append(d['ID'])
    StoryPlaybackCharacter = {}
    with open(os.path.join(masterdata_folder, 'StoryPlaybackCharacter.json'), 'r', encoding='utf-8') as f_StoryPlaybackCharacter:
        data = json.load(f_StoryPlaybackCharacter)
        for d in data:
            d['StoryPlaybackCharacterDetail'] = []
            StoryPlaybackCharacter[d['ID']] = d
            QuestCharacterS[d['quest_QuestCharacterS']]['StoryPlaybackCharacter'].append(d['ID'])
    StoryPlaybackCharacterDetail = {}
    with open(os.path.join(masterdata_folder, 'StoryPlaybackCharacterDetail.json'), 'r', encoding='utf-8') as f_StoryPlaybackCharacterDetail:
        data = json.load(f_StoryPlaybackCharacterDetail)
        for d in data:
            StoryPlaybackCharacterDetail[d['ID']] = d
            StoryPlaybackCharacter[d['character_StoryPlaybackCharacter']]['StoryPlaybackCharacterDetail'].append(d['ID'])
    index_StoryPlaybackCharacterDetail = 'pages/StoryPlaybackCharacterDetail.md'
    with open(index_StoryPlaybackCharacterDetail, 'w', encoding='utf-8') as f_index:
        f_index.write("# StoryPlaybackCharacterDetail\n\n")
        for characterL_name in sorted(QuestCharacterL.keys(), key=lambda x: min(QuestCharacterL[x]['QuestCharacterM'])):
            characterL = QuestCharacterL[characterL_name]
            f_index.write(f"## {characterL_name}\n\n")
            for characterM_id in characterL['QuestCharacterM']:
                characterM = QuestCharacterM[characterM_id]
                # f_index.write(f"## {characterM['name']}\n\n")
                for characterS_id in characterM['QuestCharacterS']:
                    characterS = QuestCharacterS[characterS_id]
                    if len(characterS['StoryPlaybackCharacter']) > 0:
                        assert characterS['name'].strip() == characterM['name'].strip()
                        # f_index.write(f"## {characterS['name'].strip()}\n\n")
                    for characterStory_id in characterS['StoryPlaybackCharacter']:
                        characterStory = StoryPlaybackCharacter[characterStory_id]
                        f_index.write(f"### {characterStory['name']}\n\n")
                        for characterStoryDetail_id in characterStory['StoryPlaybackCharacterDetail']:
                            characterStoryDetail = StoryPlaybackCharacterDetail[characterStoryDetail_id]
                            script_id = characterStoryDetail['script_id']
                            f_index.write(f"- [{script_id} {characterStoryDetail['name']}]({script_id}.md)\n")
                            script_names[script_id] = ' '.join([str(script_id), characterStory['name'], characterStoryDetail['name']])
                        if len(characterStory['StoryPlaybackCharacterDetail']) > 0:
                            f_index.write("\n")
    # index for StoryPlaybackEventPlay
    StoryPlaybackEventPlay = {}
    with open(os.path.join(masterdata_folder, 'StoryPlaybackEventPlay.json'), 'r', encoding='utf-8') as f_StoryPlaybackEventPlay:
        data = json.load(f_StoryPlaybackEventPlay)
        for d in data:
            StoryPlaybackEventPlay[d['ID']] = d
    index_StoryPlaybackEventPlay = 'pages/StoryPlaybackEventPlay.md'
    with open(index_StoryPlaybackEventPlay, 'w', encoding='utf-8') as f_index:
        f_index.write("# Event Play\n\n")
        for eventPlay_id in sorted(StoryPlaybackEventPlay.keys()):
            eventPlay = StoryPlaybackEventPlay[eventPlay_id]
            script_id = eventPlay['script_id']
            f_index.write(f"- [{script_id} {eventPlay['scene_name']} {eventPlay['start_at']} ~ {eventPlay['end_at']}]({script_id}.md)\n")
            script_names[script_id] = ' '.join([str(script_id), "Event Play", f"#{eventPlay['ID']}", eventPlay['scene_name'], eventPlay['start_at'], '~', eventPlay['end_at']])
    # index for StoryPlaybackExtraDetail
    QuestExtraCategory = {}
    with open(os.path.join(masterdata_folder, 'QuestExtraCategory.json'), 'r', encoding='utf-8') as f_QuestExtraCategory:
        data = json.load(f_QuestExtraCategory)
        for d in data:
            d['QuestExtraL'] = []
            d['QuestExtraM'] = []
            QuestExtraCategory[d['ID']] = d
    QuestExtraLL = {
        0: {
		    "ID": 0,
		    "name": "",
            "QuestExtraL": [],
            "QuestExtraM": [],
        }
    }
    with open(os.path.join(masterdata_folder, 'QuestExtraLL.json'), 'r', encoding='utf-8') as f_QuestExtraLL:
        data = json.load(f_QuestExtraLL)
        for d in data:
            d['QuestExtraL'] = []
            d['QuestExtraM'] = []
            QuestExtraLL[d['ID']] = d
    QuestExtraL = {}
    with open(os.path.join(masterdata_folder, 'QuestExtraL.json'), 'r', encoding='utf-8') as f_QuestExtraL:
        data = json.load(f_QuestExtraL)
        for d in data:
            d['QuestExtraS'] = []
            QuestExtraL[d['ID']] = d
            QuestExtraLL[d['quest_ll_QuestExtraLL']]['QuestExtraL'].append(d['ID'])
            QuestExtraCategory[d['category_QuestExtraCategory']]['QuestExtraL'].append(d['ID'])
    QuestExtraM = {}
    with open(os.path.join(masterdata_folder, 'QuestExtraM.json'), 'r', encoding='utf-8') as f_QuestExtraM:
        data = json.load(f_QuestExtraM)
        for d in data:
            d['QuestExtraS'] = []
            QuestExtraM[d['ID']] = d
            QuestExtraLL[d['quest_ll_QuestExtraLL']]['QuestExtraM'].append(d['ID'])
            QuestExtraCategory[d['category_QuestExtraCategory']]['QuestExtraM'].append(d['ID'])
    QuestExtraS = {}
    with open(os.path.join(masterdata_folder, 'QuestExtraS.json'), 'r', encoding='utf-8') as f_QuestExtraS:
        data = json.load(f_QuestExtraS)
        for d in data:
            d['StoryPlaybackExtra'] = []
            d['StoryPlaybackExtraDetail'] = []
            QuestExtraS[d['ID']] = d
            QuestExtraM[d['quest_m_QuestExtraM']]['QuestExtraS'].append(d['ID'])
            QuestExtraL[d['quest_l_QuestExtraL']]['QuestExtraS'].append(d['ID'])
    StoryPlaybackExtra = {}
    with open(os.path.join(masterdata_folder, 'StoryPlaybackExtra.json'), 'r', encoding='utf-8') as f_StoryPlaybackExtra:
        data = json.load(f_StoryPlaybackExtra)
        for d in data:
            d['StoryPlaybackExtraDetail'] = []
            StoryPlaybackExtra[d['ID']] = d
            QuestExtraS[d['quest_QuestExtraS']]['StoryPlaybackExtra'].append(d['ID'])
    StoryPlaybackExtraDetail = {}
    with open(os.path.join(masterdata_folder, 'StoryPlaybackExtraDetail.json'), 'r', encoding='utf-8') as f_StoryPlaybackExtraDetail:
        data = json.load(f_StoryPlaybackExtraDetail)
        for d in data:
            StoryPlaybackExtraDetail[d['ID']] = d
            StoryPlaybackExtra[d['extra_StoryPlaybackExtra']]['StoryPlaybackExtraDetail'].append(d['ID'])
            QuestExtraS[d['quest_QuestExtraS']]['StoryPlaybackExtraDetail'].append(d['ID'])
    index_StoryPlaybackExtraDetail = 'pages/StoryPlaybackExtraDetail.md'
    with open(index_StoryPlaybackExtraDetail, 'w', encoding='utf-8') as f_index:
        f_index.write("# エクストラクエスト\n\n")
        for questExtraLL_id in sorted(QuestExtraLL.keys()):
            questExtraLL = QuestExtraLL[questExtraLL_id]
            f_index.write(f"## {questExtraLL['name']}\n\n")
            for questExtraM_id in questExtraLL['QuestExtraM']:
                questExtraM = QuestExtraM[questExtraM_id]
                category = QuestExtraCategory[questExtraM['category_QuestExtraCategory']]
                f_index.write(f"### 【{category['name']}】 {questExtraM['name']}\n\n")
                for questExtraS_id in questExtraM['QuestExtraS']:
                    questExtraS = QuestExtraS[questExtraS_id]
                    if len(questExtraS['StoryPlaybackExtraDetail']) > 0:
                        questExtraL = QuestExtraL[questExtraS['quest_l_QuestExtraL']]
                        f_index.write(f"#### 【{questExtraL['name']}】 {questExtraS['name']}\n\n")
                        for story_id in questExtraS['StoryPlaybackExtra']:
                            story = StoryPlaybackExtra[story_id]
                            if len(story['StoryPlaybackExtraDetail']) > 0:
                                f_index.write(f"##### {story['name']}\n\n")
                                for storyDetail_id in sorted(story['StoryPlaybackExtraDetail'], key=lambda x: StoryPlaybackExtraDetail[x]['timing_StoryPlaybackTiming']):
                                    storyDetail = StoryPlaybackExtraDetail[storyDetail_id]
                                    script_id = storyDetail['script_id']
                                    f_index.write(f"- [{script_id} {storyDetail['name']}]({script_id}.md)\n")
                                    script_names[script_id] = ' '.join([str(script_id), category['name'], questExtraLL['name'], questExtraL['name'], questExtraM['name'], questExtraS['name'], story['name'], storyDetail['name']])
                                if len(story['StoryPlaybackExtraDetail']) > 0:
                                    f_index.write("\n")
    # index for contents
    index_contents = 'contents.md'
    with open(index_contents, 'w', encoding='utf-8') as f_index:
        f_index.write("# Contents\n\n")
        f_index.write("## ストーリークエスト\n\n")
        f_index.write(f"- [{QuestStoryXL[2]['name']}]({index_EarthQuestStoryPlayback})\n")
        f_index.write(f"\n## [エクストラクエスト]({index_StoryPlaybackExtraDetail})\n")
        f_index.write(f"\n## [キャラクタークエスト]({index_StoryPlaybackCharacterDetail})\n")
        f_index.write(f"\n## [Event Play]({index_StoryPlaybackEventPlay})\n")
    # index for all scripts
    index_page = 'scripts/index.md'
    with open(index_page, 'w', encoding='utf-8') as f_index:
        f_index.write("# Scripts\n\n")
        for script_id in script_ids:
            f_index.write(f"- [{script_names.get(script_id, script_id)}]({script_id}.txt)\n")
    index_page = 'pages/index.md'
    with open(index_page, 'w', encoding='utf-8') as f_index:
        f_index.write("# Pages\n\n")
        for script_id in script_ids:
            f_index.write(f"- [{script_names.get(script_id, script_id)}]({script_id}.md)\n")


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

build_index_page(masterdata_folder)

parse_script_files(masterdata_folder, extracted_folder)
