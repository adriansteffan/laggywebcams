import os
from os.path import isfile, join
import subprocess
import shutil
import argparse
import json

import pandas as pd

import settings
from src.icatcher_handler import ICatcherHandler
from src.webgazer_handler import WebGazerHandler



def main():

    participants = set()
   
    participants = get_participants()

    prepare_data(participants, settings.RENDER_WEBCAM_VIDEOS)

    #icatcher = ICatcherHandler(settings.GAZECODER_NAMES['ICATCHER'], participants)
    webgazer_no_rec = WebGazerHandler(settings.GAZECODER_NAMES['WEBGAZER_NOREC'], participants, dot_color=(0, 255, 0), datafile_suffix="datanorec")
    webgazer = WebGazerHandler(settings.GAZECODER_NAMES['WEBGAZER'], participants, dot_color=(255, 0, 0), datafile_suffix="data")

    #icatcher.run(should_render=settings.RENDER_ICATCHER)
    webgazer_no_rec.run(should_render=settings.RENDER_WEBGAZER)
    webgazer.run(should_render=settings.RENDER_WEBGAZER)
    




def get_participants():

    files = [f for f in os.listdir(settings.DATA_DIR) if isfile(join(settings.DATA_DIR, f))]
    participants = set()

    for filename in files:
        if not (filename.endswith('.webm') or filename.endswith('.json')):
            continue

        special_stimulus_endings = [s + ".webm" for s in settings.stimuli_critical]
        split_pos = -2 if filename.endswith(tuple(special_stimulus_endings)) else -1
        participant = "_".join(filename.split("_")[:split_pos])
        participants.add(participant)

    return participants


def prepare_data(participants, render_webcam_videos):
    if not os.path.exists(settings.OUT_DIR):
        os.makedirs(settings.OUT_DIR)

    if not os.path.exists(settings.WEBCAM_MP4_DIR):
        os.makedirs(settings.WEBCAM_MP4_DIR)

    # extract a table with window sizes from the online data -> other eyetrackers might need the dimensions.
    # due to how the data is structured, we have to assume that the window size did not change over
    # the course of the experiment, as calibration and validation did not provide that data.
    # However, as the experiment went into fullscreen, constant window dimensions are likely.
    window_sizes_path = os.path.join(settings.OUT_DIR, '_window_sizes.csv')
    if not os.path.isfile(window_sizes_path):
        ws_dict_list = []
        for p in participants:

            data_file = f'{settings.DATA_DIR}/{p}_data.json'
            if not os.path.isfile(data_file):
                print(p)
                continue
            with open(data_file) as f:
                data = json.load(f)

            first_trial = [x for x in data if 'task' in x and x['task'] == 'video'][0]

            ws_dict_list.append({'id': p,
                                 'window_width': first_trial["windowWidth"],
                                 'window_height': first_trial["windowHeight"]
                                 })

        pd.DataFrame(ws_dict_list).to_csv(window_sizes_path, encoding='utf-8', index=False)

    if render_webcam_videos:
        for p in participants:
            for s in settings.stimuli:
                input_file = f'{settings.DATA_DIR}/{p}_{s}.webm'
                temp_file = f'{settings.WEBCAM_MP4_DIR}/{p}_{s}_temp.mp4'
                output_file = f'{settings.WEBCAM_MP4_DIR}/{p}_{s}.mp4'

                if os.path.isfile(input_file) and not os.path.isfile(output_file):

                    subprocess.Popen(['ffmpeg', '-y',
                                      '-i', f'{settings.DATA_DIR}/{p}_{s}.webm',
                                      '-filter:v',
                                      f'fps={settings.TARGET_FPS}',
                                      temp_file,
                                      ]).wait()

                    result = subprocess.run(["ffprobe", "-v", "error", "-show_entries",
                                             "format=duration", "-of",
                                             "default=noprint_wrappers=1:nokey=1", temp_file],
                                            stdout=subprocess.PIPE,
                                            stderr=subprocess.STDOUT)

                    webcam_length = float(result.stdout.splitlines()[-1])
                    mismatch = settings.STIMULI[s]['presentation_duration'] - webcam_length

                    if mismatch > 0.0:
                        subprocess.Popen(['ffmpeg', '-y',
                                          '-i', temp_file,
                                          '-filter_complex',
                                          f'[0:v]tpad=start_duration={mismatch}[v];[0:a]adelay={mismatch*1000}s:all=true[a]',
                                          "-map", "[v]", "-map", "[a]",
                                          output_file,
                                          ]).wait()
                    elif mismatch < 0.0:
                        subprocess.Popen(['ffmpeg',
                                          '-y',
                                          '-i',
                                          temp_file,
                                          '-ss',
                                          f'00:00:{(-1.0) * mismatch:06.3f}',
                                          output_file,
                                          ]).wait()
                    else:
                        shutil.copy(temp_file, output_file)

                    os.remove(temp_file)

    return participants


if __name__ == '__main__':
    main()

