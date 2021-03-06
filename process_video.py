import argparse
import csv
import math
import os
import subprocess
import sys
from datetime import datetime

import cv2
import numpy as np


def get_feature_line(image):
    """Grab one pixel line from image for feature comparison.
    feature_x: x coordinate from top left corner
    feature_y: y coordinate from top left corner (height of the 1px vertical line)
    """
    feature_x = 200
    feature_y = 500

    line = []

    for h in image[:feature_y]:
        line.append(h[feature_x])
    line = np.array(line)

    return line


def frames_to_timecode(frames, fps):
    """Convert frames to time code in HH:MM:SS"""
    secs = int(frames / fps)
    mins, secs = divmod(secs, 60)
    hours, mins = divmod(mins, 60)
    return f"{hours:02d}:{mins:02d}:{secs:02d}"


def main(video_file, base_image, output_folder=None):
    """Main prorgram.

    video_file: path to the video to be processed
    base_image: base image for feature detection.
    """
    start_time = datetime.now()

    cap = cv2.VideoCapture(video_file)
    fps = math.ceil(cap.get(cv2.CAP_PROP_FPS))

    # fourcc = 0x00000020 #cv2.VideoWriter_fourcc( *'AVC1' )
    # framesize = ( int( cap.get( cv2.CAP_PROP_FRAME_WIDTH ) ), int( cap.get( cv2.CAP_PROP_FRAME_HEIGHT ) ) )

    line = get_feature_line(cv2.imread(base_image))

    # line = []
    # base = cv2.imread('base.png')
    # for h in base[:feature_y]:
    #     line.append(h[feature_x])
    # line = np.array(line)

    c = 0
    ini = 0
    games = []
    started = False

    while cap.isOpened():
        ret = cap.grab()
        if not ret:
            break
        c += 1

        if c % (fps * 5) > 0:
            continue

        ret, frame = cap.retrieve()
        if not ret:
            break

        line2 = get_feature_line(frame)

        diff = np.mean(cv2.absdiff(line, line2))
        if diff > 10:
            if started:
                started = False
                # out.release()
                games.append((ini, c))
                print((ini, c))
                # print('.')

            continue

        if not started:
            started = True
            # out = cv2.VideoWriter( 'frame_'+str(c)+'.mp4', fourcc, fps, framesize )
            ini = c

    # out.write( frame )

    if started:
        # out.release()
        games.append((ini, c))

    cap.release()
    cv2.destroyAllWindows()

    games_time = []
    time_codes = []
    for (ini, end) in games:
        if end - ini < 60 * 90:
            # too short. maybe a repetition
            # if os.path.exists( 'frame_'+str( ini )+'.mp4' ):
            # os.remove( 'frame_'+str( ini )+'.mp4' )
            continue

        ini -= fps * 5

        m_ini = int(math.floor(ini / (fps * 60)))
        s_ini = int(math.ceil((ini / fps) - (m_ini * 60)))

        m_end = int(math.floor(end / (fps * 60)))
        s_end = int(math.ceil((end / fps) - (m_end * 60)))

        games_time.append(str(m_ini) + ':' + str(s_ini) + ' - ' + str(m_end) + ':' + str(s_end))

        # time codes
        tc_ini = frames_to_timecode(ini, fps)
        tc_end = frames_to_timecode(end, fps)
        time_codes.append(dict(
            video=video_file,
            tc_ini=tc_ini,
            tc_end=tc_end,
            ini=ini,
            end=end,
        ))

    print(games_time)
    print((datetime.now() - start_time).total_seconds())

    print("\n".join(games_time))

    # out paths
    output_path = os.path.join(output_folder)
    os.makedirs(output_path, exist_ok=True)

    # generate video filenames as sequences. Use 1-base for maintainers
    basename = os.path.basename(video_file)
    base = basename.split('.')[0]
    for i, time_code in enumerate(time_codes, 1):
        fn = f"{base}-{i:03d}.mp4"
        time_code.update(
            filename=fn,
            index=i,
        )

    # generate CSV results
    with open(os.path.join(output_path, f'{base}-time_codes.csv'), 'w') as f:
        writer = csv.DictWriter(f, fieldnames=['video', 'index', 'filename', 'tc_ini', 'tc_end', 'ini', 'end'])
        writer.writeheader()
        writer.writerows(time_codes)

    # generate split videos with ffmpeg
    for time_code in time_codes:
        fn = time_code.get('filename')
        tc_ini = time_code.get('tc_ini')
        tc_end = time_code.get('tc_end')
        out_path = os.path.join(output_path, fn)
        cmd = ["ffmpeg", "-i", video_file, "-ss", tc_ini, "-to", tc_end, "-c", "copy", out_path]
        subprocess.run(cmd, stderr=subprocess.STDOUT)


if __name__ == '__main__':
    """
    e.g.
    python process_video.py \
        --folder "/Users/sml/Dropbox/CRL-2019-CN-UP/W4" \
        --output "/Users/sml/Dropbox/CRL-2019-CN-UP/W4_dist"
    """
    parser = argparse.ArgumentParser(description="Process CRL videos")
    parser.add_argument('--videos', nargs='+', default=None, help="List of videos to process")
    parser.add_argument('--folder', default=None, help="Folder containing videos")
    parser.add_argument('--base', default='./base.png', help="Base image")
    parser.add_argument('--output', default='./dist', help="Output folder")
    args = parser.parse_args(sys.argv[1:])

    if not os.path.exists(args.base):
        print("The file base.png doesn’t exist")
        quit()

    input_videos = []

    if args.videos:
        for video in args.videos:
            input_videos.append(video)

    if args.folder:
        if not os.path.exists(args.folder):
            print(f"folder {args.folder} does not exist")
            quit()

        for dirpath, _, filenames in os.walk(args.folder):
            for f in filenames:
                video = os.path.join(dirpath, f)
                if not video.lower().endswith('mp4'):
                    continue

                input_videos.append(video)


    # run script
    for video in input_videos:
        main(video, args.base, output_folder=args.output)
