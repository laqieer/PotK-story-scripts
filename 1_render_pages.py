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
        elif 'http' in line and video_name is not None:
            if line.startswith('http'):
                videos[video_name] = f'<video controls src="{line.strip()}" type="video/mp4"></video>'
            else:
                videos[video_name] = line
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
                        case 'movieplay':
                            video = lispAction[1].replace('"','')
                            if video not in videos:
                                video_path = f'videos/{video}.mp4'
                                if not os.path.exists(video_path):
                                    os.makedirs('videos', exist_ok=True)
                                    shutil.copy(os.path.join(extracted_folder, f'StreamingAssets/android/{video}.mp4'), video_path)
                                videos[video] = f'<video controls src="../{video_path}" type="video/mp4"></video>'
                            f_page.write(f"\n\n{video}\n\n{videos[video]}\n\n")
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
    QuestMoviePath = {}
    with open(os.path.join(masterdata_folder, 'QuestMoviePath.json'), 'r', encoding='utf-8') as f:
        data = json.load(f)
        for d in data:
            QuestMoviePath[d['ID']] = d
    QuestMovieQuest = {}
    with open(os.path.join(masterdata_folder, 'QuestMovieQuest.json'), 'r', encoding='utf-8') as f:
        data = json.load(f)
        for d in data:
            QuestMovieQuest[d['ID']] = d
    quest_s_videos = {}
    for questMovieQuest_id in sorted(QuestMovieQuest.keys()):
        questMovieQuest = QuestMovieQuest[questMovieQuest_id]
        questMoviePath = QuestMoviePath[questMovieQuest['movie_path_QuestMoviePath']]
        if questMovieQuest['quest_s_id'] not in quest_s_videos:
            quest_s_videos[questMovieQuest['quest_s_id']] = []
        quest_s_videos[questMovieQuest['quest_s_id']].append(os.path.basename(questMoviePath['android_path']))

    QuestStoryXL = {}
    with open(os.path.join(masterdata_folder, 'QuestStoryXL.json'), 'r', encoding='utf-8') as f_QuestStoryXL:
        data = json.load(f_QuestStoryXL)
        for d in data:
            d['QuestStoryL'] = []
            d['QuestStoryM'] = []
            d['QuestStoryS'] = []
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

    # index for StoryPlaybackSeaDetail
    QuestSeaXL = {}
    with open(os.path.join(masterdata_folder, 'QuestSeaXL.json'), 'r', encoding='utf-8') as f_QuestSeaXL:
        data = json.load(f_QuestSeaXL)
        for d in data:
            d['QuestSeaL'] = []
            d['QuestSeaM'] = []
            d['QuestSeaS'] = []
            QuestSeaXL[d['ID']] = d
    QuestSeaL = {}
    with open(os.path.join(masterdata_folder, 'QuestSeaL.json'), 'r', encoding='utf-8') as f_QuestSeaL:
        data = json.load(f_QuestSeaL)
        for d in data:
            d['QuestSeaM'] = []
            d['QuestSeaS'] = []
            QuestSeaL[d['ID']] = d
            QuestSeaXL[d['quest_xl_QuestSeaXL']]['QuestSeaL'].append(d['ID'])
    QuestSeaM = {}
    with open(os.path.join(masterdata_folder, 'QuestSeaM.json'), 'r', encoding='utf-8') as f_QuestSeaM:
        data = json.load(f_QuestSeaM)
        for d in data:
            d['QuestSeaS'] = []
            QuestSeaM[d['ID']] = d
            QuestSeaL[d['quest_l_QuestSeaL']]['QuestSeaM'].append(d['ID'])
            QuestSeaXL[d['quest_xl_QuestSeaXL']]['QuestSeaM'].append(d['ID'])
    QuestSeaS = {}
    with open(os.path.join(masterdata_folder, 'QuestSeaS.json'), 'r', encoding='utf-8') as f_QuestSeaS:
        data = json.load(f_QuestSeaS)
        for d in data:
            d['StoryPlaybackSea'] = []
            d['StoryPlaybackSeaDetail'] = []
            QuestSeaS[d['ID']] = d
            QuestSeaM[d['quest_m_QuestSeaM']]['QuestSeaS'].append(d['ID'])
            QuestSeaL[d['quest_l_QuestSeaL']]['QuestSeaS'].append(d['ID'])
            QuestSeaXL[d['quest_xl_QuestSeaXL']]['QuestSeaS'].append(d['ID'])
    StoryPlaybackSea = {}
    with open(os.path.join(masterdata_folder, 'StoryPlaybackSea.json'), 'r', encoding='utf-8') as f_StoryPlaybackSea:
        data = json.load(f_StoryPlaybackSea)
        for d in data:
            d['StoryPlaybackSeaDetail'] = []
            StoryPlaybackSea[d['ID']] = d
            QuestSeaS[d['quest_QuestSeaS']]['StoryPlaybackSea'].append(d['ID'])
    StoryPlaybackSeaDetail = {}
    with open(os.path.join(masterdata_folder, 'StoryPlaybackSeaDetail.json'), 'r', encoding='utf-8') as f_StoryPlaybackSeaDetail:
        data = json.load(f_StoryPlaybackSeaDetail)
        for d in data:
            StoryPlaybackSeaDetail[d['ID']] = d
            StoryPlaybackSea[d['story_StoryPlaybackSea']]['StoryPlaybackSeaDetail'].append(d['ID'])
            QuestSeaS[d['quest_s_id_QuestSeaS']]['StoryPlaybackSeaDetail'].append(d['ID'])
    index_StoryPlaybackSeaDetail = 'pages/StoryPlaybackSeaDetail.md'
    with open(index_StoryPlaybackSeaDetail, 'w', encoding='utf-8') as f_index:
        f_index.write(f"# {QuestStoryXL[3]['name']}\n\n")
        for questSeaXL_id in sorted(QuestSeaXL.keys()):
            questSeaXL = QuestSeaXL[questSeaXL_id]
            assert questSeaXL['name']
            # f_index.write(f"## {questSeaXL['name']}\n\n")
            for questSeaL_id in questSeaXL['QuestSeaL']:
                questSeaL = QuestSeaL[questSeaL_id]
                f_index.write(f"## {questSeaL['name']}\n\n")
                for questSeaM_id in questSeaL['QuestSeaM']:
                    questSeaM = QuestSeaM[questSeaM_id]
                    f_index.write(f"### {questSeaM['name']}\n\n")
                    for questSeaS_id in questSeaM['QuestSeaS']:
                        questSeaS = QuestSeaS[questSeaS_id]
                        if len(questSeaS['StoryPlaybackSeaDetail']) > 0:
                            f_index.write(f"#### {questSeaS['name']}\n\n")
                            # for story_id in questSeaS['StoryPlaybackSea']:
                            #     story = StoryPlaybackSea[story_id]
                            #     if len(story['StoryPlaybackSeaDetail']) > 0:
                            #         f_index.write(f"##### {story['name']}\n\n")
                            for storyDetail_id in sorted(questSeaS['StoryPlaybackSeaDetail'], key=lambda x: StoryPlaybackSeaDetail[x]['timing_StoryPlaybackTiming']):
                                storyDetail = StoryPlaybackSeaDetail[storyDetail_id]
                                story = StoryPlaybackSea[storyDetail['story_StoryPlaybackSea']]
                                script_id = storyDetail['script_id']
                                f_index.write(f"- [{script_id} {storyDetail['name']}]({script_id}.md)\n")
                                script_names[script_id] = ' '.join([str(script_id), questSeaXL['name'], questSeaL['name'], questSeaM['name'], storyDetail['name']])
                            f_index.write("\n")

    # index for StoryPlaybackStoryDetail
    QuestStoryL = {}
    with open(os.path.join(masterdata_folder, 'QuestStoryL.json'), 'r', encoding='utf-8') as f_QuestStoryL:
        data = json.load(f_QuestStoryL)
        for d in data:
            d['QuestStoryM'] = []
            d['QuestStoryS'] = []
            QuestStoryL[d['ID']] = d
            QuestStoryXL[d['quest_xl_QuestStoryXL']]['QuestStoryL'].append(d['ID'])
    QuestStoryM = {}
    with open(os.path.join(masterdata_folder, 'QuestStoryM.json'), 'r', encoding='utf-8') as f_QuestStoryM:
        data = json.load(f_QuestStoryM)
        for d in data:
            d['QuestStoryS'] = []
            QuestStoryM[d['ID']] = d
            QuestStoryL[d['quest_l_QuestStoryL']]['QuestStoryM'].append(d['ID'])
            QuestStoryXL[d['quest_xl_QuestStoryXL']]['QuestStoryM'].append(d['ID'])
    QuestStoryS = {}
    with open(os.path.join(masterdata_folder, 'QuestStoryS.json'), 'r', encoding='utf-8') as f_QuestStoryS:
        data = json.load(f_QuestStoryS)
        for d in data:
            d['StoryPlaybackStory'] = []
            d['StoryPlaybackStoryDetail'] = []
            QuestStoryS[d['ID']] = d
            QuestStoryM[d['quest_m_QuestStoryM']]['QuestStoryS'].append(d['ID'])
            QuestStoryL[d['quest_l_QuestStoryL']]['QuestStoryS'].append(d['ID'])
            QuestStoryXL[d['quest_xl_QuestStoryXL']]['QuestStoryS'].append(d['ID'])
    StoryPlaybackStory = {}
    with open(os.path.join(masterdata_folder, 'StoryPlaybackStory.json'), 'r', encoding='utf-8') as f_StoryPlaybackStory:
        data = json.load(f_StoryPlaybackStory)
        for d in data:
            d['StoryPlaybackStoryDetail'] = []
            StoryPlaybackStory[d['ID']] = d
            QuestStoryS[d['quest_QuestStoryS']]['StoryPlaybackStory'].append(d['ID'])
    StoryPlaybackStoryDetail = {}
    with open(os.path.join(masterdata_folder, 'StoryPlaybackStoryDetail.json'), 'r', encoding='utf-8') as f_StoryPlaybackStoryDetail:
        data = json.load(f_StoryPlaybackStoryDetail)
        for d in data:
            StoryPlaybackStoryDetail[d['ID']] = d
            StoryPlaybackStory[d['story_StoryPlaybackStory']]['StoryPlaybackStoryDetail'].append(d['ID'])
            QuestStoryS[d['quest_s_id_QuestStoryS']]['StoryPlaybackStoryDetail'].append(d['ID'])
    index_StoryPlaybackStoryDetail = 'pages/StoryPlaybackStoryDetail.md'
    with open(index_StoryPlaybackStoryDetail, 'w', encoding='utf-8') as f_index:
        f_index.write("# StoryPlaybackStoryDetail\n\n")
        for questStoryXL_id in sorted(QuestStoryXL.keys()):
            questStoryXL = QuestStoryXL[questStoryXL_id]
            if len(questStoryXL['QuestStoryS']) > 0:
                f_index.write(f"## {questStoryXL['name']}\n\n")
                for questStoryL_id in questStoryXL['QuestStoryL']:
                    questStoryL = QuestStoryL[questStoryL_id]
                    if len(questStoryL['QuestStoryS']) > 0 and questStoryL['quest_mode_CommonQuestMode'] == 1:
                        f_index.write(f"### {questStoryL['short_name']} {questStoryL['name']}\n\n")
                        for questStoryM_id in questStoryL['QuestStoryM']:
                            questStoryM = QuestStoryM[questStoryM_id]
                            if len(questStoryM['QuestStoryS']) > 0:
                                f_index.write(f"#### {questStoryM['short_name']} {questStoryM['name']}\n\n")
                                for questStoryS_id in questStoryM['QuestStoryS']:
                                    questStoryS = QuestStoryS[questStoryS_id]
                                    f_index.write(f"##### {questStoryL['number_l']}-{questStoryM['number_m']}-{questStoryS['number_s']} {questStoryS['name']}\n\n")
                                    if questStoryS_id in quest_s_videos:
                                        for quest_s_video in quest_s_videos[questStoryS_id]:
                                            assert quest_s_video in videos, f"Video {quest_s_video} not found"
                                            f_index.write(f"{quest_s_video}\n\n{videos[quest_s_video]}\n\n")
                                    if len(questStoryS['StoryPlaybackStoryDetail']) > 0:
                                        # for story_id in questStoryS['StoryPlaybackStory']:
                                            # story = StoryPlaybackStory[story_id]
                                            # if len(story['StoryPlaybackStoryDetail']) > 0:
                                                # for storyDetail_id in story['StoryPlaybackStoryDetail']:
                                        for storyDetail_id in questStoryS['StoryPlaybackStoryDetail']:
                                            storyDetail = StoryPlaybackStoryDetail[storyDetail_id]
                                            story = StoryPlaybackStory[storyDetail['story_StoryPlaybackStory']]
                                            script_id = storyDetail['script_id']
                                            f_index.write(f"- [{script_id} {storyDetail['name']}]({script_id}.md)\n")
                                            script_names[script_id] = ' '.join([str(script_id), questStoryXL['name'], questStoryL['short_name'], questStoryL['name'], questStoryM['short_name'], storyDetail['name']])
                                        f_index.write("\n")
            else:
                assert questStoryXL_id in (2, 3)
                f_index.write(f"## [{questStoryXL['name']}]({os.path.basename(index_EarthQuestStoryPlayback if questStoryXL_id == 2 else index_StoryPlaybackSeaDetail)})\n\n")

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
		    "name": "未分類",
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
                        f_index.write(f"#### 【{questExtraL['name']}】 {questExtraS['number_s']} - {questExtraS['name']}\n\n")
                        # for story_id in questExtraS['StoryPlaybackExtra']:
                        #     story = StoryPlaybackExtra[story_id]
                        #     if len(story['StoryPlaybackExtraDetail']) > 0:
                        #         f_index.write(f"##### {story['name']}\n\n")
                        for storyDetail_id in questExtraS['StoryPlaybackExtraDetail']:
                            storyDetail = StoryPlaybackExtraDetail[storyDetail_id]
                            story = StoryPlaybackExtra[storyDetail['extra_StoryPlaybackExtra']]
                            script_id = storyDetail['script_id']
                            f_index.write(f"- [{script_id} {storyDetail['name']}]({script_id}.md)\n")
                            script_names[script_id] = ' '.join([str(script_id), category['name'], questExtraLL['name'], questExtraL['name'], questExtraM['name'], str(questExtraS['number_s']), '-', questExtraS['name'], story['name'], storyDetail['name']])
                        f_index.write("\n")

    # index for StoryPlaybackHarmonyDetail
    QuestHarmonyM = {}
    with open(os.path.join(masterdata_folder, 'QuestHarmonyM.json'), 'r', encoding='utf-8') as f_QuestHarmonyM:
        data = json.load(f_QuestHarmonyM)
        for d in data:
            d['QuestHarmonyS'] = []
            QuestHarmonyM[d['ID']] = d
    QuestHarmonyS = {}
    with open(os.path.join(masterdata_folder, 'QuestHarmonyS.json'), 'r', encoding='utf-8') as f_QuestHarmonyS:
        data = json.load(f_QuestHarmonyS)
        for d in data:
            d['StoryPlaybackHarmony'] = []
            d['StoryPlaybackHarmonyDetail'] = []
            QuestHarmonyS[d['ID']] = d
            QuestHarmonyM[d['quest_m_QuestHarmonyM']]['QuestHarmonyS'].append(d['ID'])
    StoryPlaybackHarmony = {}
    with open(os.path.join(masterdata_folder, 'StoryPlaybackHarmony.json'), 'r', encoding='utf-8') as f_StoryPlaybackHarmony:
        data = json.load(f_StoryPlaybackHarmony)
        for d in data:
            d['StoryPlaybackHarmonyDetail'] = []
            StoryPlaybackHarmony[d['ID']] = d
            QuestHarmonyS[d['quest_QuestHarmonyS']]['StoryPlaybackHarmony'].append(d['ID'])
    StoryPlaybackHarmonyDetail = {}
    with open(os.path.join(masterdata_folder, 'StoryPlaybackHarmonyDetail.json'), 'r', encoding='utf-8') as f_StoryPlaybackHarmonyDetail:
        data = json.load(f_StoryPlaybackHarmonyDetail)
        for d in data:
            StoryPlaybackHarmonyDetail[d['ID']] = d
            StoryPlaybackHarmony[d['harmony_StoryPlaybackHarmony']]['StoryPlaybackHarmonyDetail'].append(d['ID'])
            QuestHarmonyS[d['quest_QuestHarmonyS']]['StoryPlaybackHarmonyDetail'].append(d['ID'])
    index_StoryPlaybackHarmonyDetail = 'pages/StoryPlaybackHarmonyDetail.md'
    with open(index_StoryPlaybackHarmonyDetail, 'w', encoding='utf-8') as f_index:
        f_index.write("# Harmony Quest\n\n")
        for questHarmonyM_id in sorted(QuestHarmonyM.keys()):
            questHarmonyM = QuestHarmonyM[questHarmonyM_id]
            # f_index.write(f"## {questHarmonyM['name']}\n\n")
            for questHarmonyS_id in questHarmonyM['QuestHarmonyS']:
                questHarmonyS = QuestHarmonyS[questHarmonyS_id]
                if len(questHarmonyS['StoryPlaybackHarmonyDetail']) > 0:
                    # f_index.write(f"### {questHarmonyS['name']}\n\n")
                    for story_id in questHarmonyS['StoryPlaybackHarmony']:
                        story = StoryPlaybackHarmony[story_id]
                        if len(story['StoryPlaybackHarmonyDetail']) > 0:
                            f_index.write(f"## {story['name']}\n\n")
                            for storyDetail_id in sorted(story['StoryPlaybackHarmonyDetail'], key=lambda x: StoryPlaybackHarmonyDetail[x]['timing_StoryPlaybackTiming']):
                                storyDetail = StoryPlaybackHarmonyDetail[storyDetail_id]
                                script_id = storyDetail['script_id']
                                f_index.write(f"- [{script_id} {storyDetail['name']}]({script_id}.md)\n")
                                script_names[script_id] = ' '.join([str(script_id), questHarmonyM['name'], questHarmonyS['name'], story['name'], storyDetail['name']])
                            if len(story['StoryPlaybackHarmonyDetail']) > 0:
                                f_index.write("\n")

    # index for StoryPlaybackRaidDetail
    RaidPlaybackStory = {}
    with open(os.path.join(masterdata_folder, 'RaidPlaybackStory.json'), 'r', encoding='utf-8') as f_RaidPlaybackStory:
        data = json.load(f_RaidPlaybackStory)
        for d in data:
            d['StoryPlaybackRaidDetail'] = []
            RaidPlaybackStory[d['ID']] = d
    StoryPlaybackRaidDetail = {}
    with open(os.path.join(masterdata_folder, 'StoryPlaybackRaidDetail.json'), 'r', encoding='utf-8') as f_StoryPlaybackRaidDetail:
        data = json.load(f_StoryPlaybackRaidDetail)
        for d in data:
            StoryPlaybackRaidDetail[d['ID']] = d
            RaidPlaybackStory[d['story_id']]['StoryPlaybackRaidDetail'].append(d['ID'])
    index_StoryPlaybackRaidDetail = 'pages/StoryPlaybackRaidDetail.md'
    with open(index_StoryPlaybackRaidDetail, 'w', encoding='utf-8') as f_index:
        f_index.write("# ギルドレイド\n\n")
        for raid_id in sorted(RaidPlaybackStory.keys()):
            raid = RaidPlaybackStory[raid_id]
            if len(raid['StoryPlaybackRaidDetail']) > 0:
                f_index.write(f"## {raid['name']}\n\n")
                for storyDetail_id in raid['StoryPlaybackRaidDetail']:
                    storyDetail = StoryPlaybackRaidDetail[storyDetail_id]
                    script_id = storyDetail['script_id']
                    f_index.write(f"- [{script_id} {storyDetail['name']}]({script_id}.md)\n")
                    script_names[script_id] = ' '.join([str(script_id), raid['name'], storyDetail['name']])
                if len(raid['StoryPlaybackRaidDetail']) > 0:
                    f_index.write("\n")

    # index for TowerPlaybackStoryDetail
    TowerPlaybackStoryDetail = {}
    with open(os.path.join(masterdata_folder, 'TowerPlaybackStoryDetail.json'), 'r', encoding='utf-8') as f_TowerPlaybackStoryDetail:
        data = json.load(f_TowerPlaybackStoryDetail)
        for d in data:
            TowerPlaybackStoryDetail[d['ID']] = d
    index_TowerPlaybackStoryDetail = 'pages/TowerPlaybackStoryDetail.md'
    with open(index_TowerPlaybackStoryDetail, 'w', encoding='utf-8') as f_index:
        f_index.write("# Tower\n\n")
        for storyDetail_id in sorted(TowerPlaybackStoryDetail.keys()):
            storyDetail = TowerPlaybackStoryDetail[storyDetail_id]
            script_id = storyDetail['script_id']
            f_index.write(f"- [{script_id} T{storyDetail['stage_TowerStage']} {storyDetail['name']}]({script_id}.md)\n")
            script_names[script_id] = ' '.join([str(script_id), 'Tower', str(storyDetail['stage_TowerStage']), storyDetail['name']])

    # index for UnitSEASkill
    UnitSEASkill = {}
    with open(os.path.join(masterdata_folder, 'UnitSEASkill.json'), 'r', encoding='utf-8') as f_UnitSEASkill:
        data = json.load(f_UnitSEASkill)
        for d in data:
            UnitSEASkill[d['ID']] = d
    unit_data, _ = load_unit_data(masterdata_folder)
    index_UnitSEASkill = 'pages/UnitSEASkill.md'
    with open(index_UnitSEASkill, 'w', encoding='utf-8') as f_index:
        f_index.write("# UnitSEASkill\n\n")
        for unitSEASkill_id in sorted(UnitSEASkill.keys()):
            unitSEASkill = UnitSEASkill[unitSEASkill_id]
            script_id = unitSEASkill['script_id']
            if script_id > 0:
                unit = unit_data[unitSEASkill_id * 10 + 1]
                assert unit['same_character_id'] == unitSEASkill_id
                f_index.write(f"- [{script_id} Unit {unitSEASkill_id} {unit['name']}]({script_id}.md)\n")
                script_names[script_id] = ' '.join([str(script_id), 'unitSEASkill', str(unitSEASkill_id), unit['name']])

    # index for contents
    index_contents = 'contents.md'
    with open(index_contents, 'w', encoding='utf-8') as f_index:
        f_index.write("# Contents\n\n")
        f_index.write(f"## [ストーリークエスト]({index_StoryPlaybackStoryDetail})\n\n")
        f_index.write(f"- [{QuestStoryXL[1]['name']}]({index_StoryPlaybackStoryDetail}#{QuestStoryXL[1]['name']})\n")
        f_index.write(f"- [{QuestStoryXL[2]['name']}]({index_EarthQuestStoryPlayback})\n")
        f_index.write(f"- [{QuestStoryXL[3]['name']}]({index_StoryPlaybackSeaDetail})\n")
        for i in range(4, max(QuestStoryXL.keys()) + 1):
            f_index.write(f"- [{QuestStoryXL[i]['name']}]({index_StoryPlaybackStoryDetail}#{QuestStoryXL[i]['name']})\n")
        f_index.write(f"\n## [エクストラクエスト]({index_StoryPlaybackExtraDetail})\n")
        f_index.write(f"\n## [キャラクタークエスト]({index_StoryPlaybackCharacterDetail})\n")
        f_index.write(f"\n## [Harmony Quest]({index_StoryPlaybackHarmonyDetail})\n")
        f_index.write(f"\n## [ギルドレイド]({index_StoryPlaybackRaidDetail})\n")
        f_index.write(f"\n## [Tower]({index_TowerPlaybackStoryDetail})\n")
        f_index.write(f"\n## [Event Play]({index_StoryPlaybackEventPlay})\n")
        f_index.write(f"\n## [UnitSEASkill]({index_UnitSEASkill})\n")

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
