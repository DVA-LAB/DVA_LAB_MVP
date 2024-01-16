import os
import sys
import glob
import cv2
import datetime
import pandas as pd
from haversine import haversine
from utils.log_sync.adjust_height import get_offset
# from log_sync import adjust_height

use_cols = ['OSD.latitude', 'OSD.longitude', 'OSD.height [ft]', 'OSD.altitude [ft]',
            'OSD.xSpeed [MPH]', 'OSD.ySpeed [MPH]', 'OSD.zSpeed [MPH]', 'OSD.directionOfTravel',
            'OSD.pitch', 'OSD.roll', 'OSD.yaw', 'OSD.droneType', 'GIMBAL.pitch', 'GIMBAL.roll', 'GIMBAL.yaw',
            'HOME.longitude', 'HOME.latitude', 'CAMERA.isVideo', 'OSD.flyTime [s]']

drone_type = {'Mavic 2':'mavic2zoom', 'Mavic Pro':'mavicpro', 'Mavic 3':'mavic2procine', 'Mavic Mini':'mavicmini'}


def get_log(csv_path):
    """
        log csv 파일을 데이터 프레임 형식으로 변환합니다.

        Args
            - csv_path (str): 데이터 프레임으로 변환할 csv 파일 경로

        Return
            - pd_use_log (pd.DataFrame): csv 파일을 pandas 데이터 프레임 형식으로 만든 데이터
            - base_time (datetime): csv 파일명에서 추출한 시간 정보
    """

    pd_log = pd.read_csv(csv_path, encoding='utf-8', low_memory=False).reset_index(drop=False)
    pd_log.columns = list(pd_log.iloc[0])

    pd_use_log = pd_log[1:][use_cols].reset_index(drop=True)

    # get date info from file name
    str_time = os.path.basename(csv_path)[16:-4].replace('_', ' ').replace('[', '').replace(']', '')
    base_time = datetime.datetime.strptime(str_time, '%Y-%m-%d %H-%M-%S')
    # convert record time based on the fly time info
    record_time = [base_time+datetime.timedelta(seconds=float(diff_time)) for diff_time in pd_use_log['OSD.flyTime [s]']]

    pd_use_log.insert(0, 'CUSTOM.date [local]', record_time)
    pd_use_log = pd_use_log.drop(columns='OSD.flyTime [s]')
    #print(pd_use_log)
    return pd_use_log, base_time.strftime('%Y%m%d%H%M%S')


def get_srt(srt_path, osd_typ='mavic2zoom'):
    """
        srt 로그를 데이터 pandas 데이터 프레임 형식으로 변환합니다.

        Args
            - srt_path (str): srt 파일 경로
            - osd_type (str): 드론 기종 정보
            
        Return
            - pd_srt (pd.DataFrame): pandas 데이터 프레임 형식으로 변환된 srt 데이터

            ex) pd.DataFrame({'time_now': df_time, 'latitude': df_lat, 'longitude': df_lon, 'focal_length': df_fl})
    """

    srt_file = open(srt_path, 'r', encoding='utf-8')
    txt_srt = srt_file.readlines()
    srt_file.close()

    df_time, df_lat, df_lon, df_fl = [], [], [], []

    if osd_typ=='mavic2zoom':
        for idx, line in enumerate(txt_srt):
            line = line.strip()
            if idx % 6 == 3:
                df_time.append(datetime.datetime.strptime(line[:19], '%Y-%m-%d %H:%M:%S'))
            elif idx % 6 == 4:
                divide = line.split('] [')
                df_fl.append(float(divide[6].split(': ')[-1]))
                df_lat.append(float(divide[7].split(': ')[-1]))
                df_lon.append(float(divide[8].split(': ')[-1]))

    elif osd_typ=='mavicpro':
        for idx, line in enumerate(txt_srt):
            line = line.strip()
            if idx % 6 == 2:
                df_time.append(datetime.datetime.strptime(line.split(') ')[-1], '%Y.%m.%d %H:%M:%S'))
            elif idx % 6 == 3:
                divide = line.split(') ')[0][4:].split(',')
                df_lat.append(float(divide[1]))
                df_lon.append(float(divide[0]))
        df_fl += [280]*len(df_time) # focal length value of mavic2 drone is 28 mm

    pd_srt = pd.DataFrame({'time_now': df_time, 'latitude': df_lat, 'longitude': df_lon, 'focal_length': df_fl})

    return pd_srt


def get_mov_idx(pd_log):
    """
        csv 파일에서 SRT index 후보를 탐색합니다.    
    
        Args
            - pd_log(pd.DataFrame): pandas 데이터 프레임 형식으로 변환된 log

        Return
            - pd_idx (pd.DataFrame): 시작 인덱스와 종료 인덱스가 담긴 데이터 프레임 
            
            ex) pd.DataFrame({'idx_start': start_idx, 'idx_end': end_idx})
    """

    mov_status = list(pd_log['CAMERA.isVideo'])
    start_idx = []
    end_idx = []

    for idx in range(len(mov_status)):
        if idx == 0:
            if mov_status[idx] == 'True':
                start_idx.append(idx)
        elif idx == len(mov_status) - 1:
            if mov_status[idx - 1] == 'True' and mov_status[idx] == 'True':
                end_idx.append(idx)
        else:
            if mov_status[idx - 1] == 'False' and mov_status[idx] == 'True':
                start_idx.append(idx)

            if mov_status[idx - 1] == 'True' and mov_status[idx] == 'False':
                end_idx.append(idx)

    pd_idx = pd.DataFrame({'idx_start': start_idx, 'idx_end': end_idx})

    return pd_idx


def get_time_diff(time1, time2):
    """
        두 타임스탬프 간의 차이를 계산하여 초 단위로 반환합니다.

        Args
            - time1 (datetime): 첫 번째 타임스탬프
            - time2 (datetime): 두 번째 타임스탬프

        Return
            - 두 타임스탬프 간의 차이를 초 단위로 나타낸 값
    """

    if time1 > time2:
        return (time1 - time2).seconds
    elif time1 < time2:
        return (time2 - time1).seconds
    else:
        return 0


def get_num_frame(mov_path):
    """
        비디오 파일의 프레임 개수를 반환합니다.

        Args
            - mov_path (str): 비디오 파일의 경로

        Return
            - cnt_frame (int): 프레임 개수
    """

    video = cv2.VideoCapture(mov_path)
    cnt_frame = int(video.get(cv2.CAP_PROP_FRAME_COUNT))

    return cnt_frame



def match_srt(pd_log, pd_srt, pd_idx):
    """
        log 파일과 srt 파일 간 매칭을 수행합니다.
        
        Args
            - pd_log (pd.DataFrame): pandas 데이터 프레임 형식으로 변환된 log입니다.
            - pd_srt (pd.DataFrame): pandas 데이터 프레임 형식으로 변환된 srt입니다.
            - pd_idx (pd.DataFrame): ?

        Return
            - pd_log (pd.DataFrame): ?
            - start_idx (?): ?
            - end_idx (?): ?
    """

    # get lat/lon info of start & end point in input SRT file
    start_point = list(pd_srt[['time_now','latitude','longitude']].iloc[0])

    # get lat/lon info of start & end point in entire CSV file
    coord_start = pd_log[['CUSTOM.date [local]','OSD.latitude','OSD.longitude']].iloc[list(pd_idx['idx_start'])]
    coord_end = pd_log[['CUSTOM.date [local]','OSD.latitude','OSD.longitude']].iloc[list(pd_idx['idx_end'])]

    # calculate time & distance of start point
    start_dist, start_time = [], []
    for idx in range(len(coord_start)):
        start_dist.append(haversine(start_point[1:],
                                    [float(coord_start['OSD.latitude'].iloc[idx]),
                                     float(coord_start['OSD.longitude'].iloc[idx])]))
        start_time.append(get_time_diff(start_point[0], coord_start['CUSTOM.date [local]'].iloc[idx]))

    # get SRT matching region based on time (major) & distance (minor)
    if min(start_time) <= 60:
        start_idx = coord_start.index[start_time.index(min(start_time))]
        end_idx = coord_end.index[start_time.index(min(start_time))]
        print('match type: time')
    else:
        start_idx = coord_start.index[start_dist.index(min(start_dist))]
        end_idx = coord_end.index[start_dist.index(min(start_dist))]
        print('match type: distance')

    return pd_log[start_idx:end_idx+1], start_idx, end_idx


# # match SRT and log file
# def match_srt(pd_log, pd_srt, pd_idx):
#     # get lat/lon info of start & end point in input SRT file
#     start_point = list(pd_srt[['time_now','latitude','longitude']].iloc[0])

#     # get lat/lon info of start & end point in entire CSV file
#     coord_start = pd_log[['CUSTOM.date [local]','OSD.latitude','OSD.longitude']].iloc[list(pd_idx['idx_start'])]
#     coord_end = pd_log[['CUSTOM.date [local]','OSD.latitude','OSD.longitude']].iloc[list(pd_idx['idx_end'])]

#     # calculate time & distance of start point
#     start_dist, start_time = [], []
#     for idx in range(len(coord_start)):
#         start_dist.append(haversine(start_point[1:],
#                                     [float(coord_start['OSD.latitude'].iloc[idx]),
#                                      float(coord_start['OSD.longitude'].iloc[idx])]))
#         start_time.append(get_time_diff(start_point[0], coord_start['CUSTOM.date [local]'].iloc[idx]))

#     # get SRT matching region based on time (major) & distance (minor)
#     if min(start_time) <= 60:
#         start_idx = coord_start.index[start_time.index(min(start_time))]
#         end_idx = coord_end.index[start_time.index(min(start_time))]
#         print('match type: time')
#     else:
#         if min(start_dist) <= 0.05:
#             start_idx = coord_start.index[start_dist.index(min(start_dist))]
#             end_idx = coord_end.index[start_dist.index(min(start_dist))]
#             print('match type: distance')
#         else:
#             return

#     return pd_log[start_idx:end_idx+1], start_idx, end_idx


# adjust SRT matching region based on SRT file
def adjust_csv_w_srt(pd_log, pd_srt, cnt_frame):
    """
        ?

        Args
            - pd_log (pd.DataFrame): pandas 데이터 프레임 형식으로 변환된 log 입니다.
            - pd_srt (pd.DataFrame): pandas 데이터 프레임 형식으로 변환된 srt 입니다.

        Return
            - pd_log_final (pd.DataFrame): ?
    """

    pd_log_adjust = pd_log.copy()
    pd_log_adjust = pd_log_adjust.drop(['CUSTOM.date [local]','CAMERA.isVideo','OSD.droneType'], axis='columns')

    print("video length:", cnt_frame, ' ', "srt length:", len(pd_srt))

    if len(pd_srt) == cnt_frame:
        print("Length of video and SRT file are same!")
        print("Thus, we set the final length of log file into the length of SRT file")
        len_log = len(pd_srt)
    else:
        print("Length of video and SRT file are not same..")
        print("Thus, we set the final length of log file into the length of video")
        len_log = cnt_frame

    pd_log_final = pd.DataFrame(index=range(len_log), columns=pd_log_adjust.columns)

    cnt = 0.
    cnt_inc = len_log / len(pd_log_adjust)
    for idx in range(len(pd_log_adjust)):
        pd_log_final.iloc[int(cnt)] = pd_log_adjust.iloc[idx]
        cnt += cnt_inc

    pd_log_final = pd_log_final.astype('float')
    pd_log_final = pd_log_final.interpolate(method='values')

    pd_log_final.insert(0, 'FrameCnt', [idx+1 for idx in range(len_log)])
    pd_log_final.insert(1, 'focal_length', pd_srt['focal_length'])
    pd_log_final.insert(2, 'datetime', pd_srt['time_now'])

    return pd_log_final


# adjust SRT matching region based on SRT file
def adjust_csv_wo_srt(pd_log, cnt_frame):
    """
        ?
        
        Args
            - pd_log (pd.DataFrame): pandas 데이터 프레임 형식으로 변환된 log입니다.
            - cnt_frame (int): 비디오의 프레임 개수입니다.
        
        Return
            - pd_log_final (pd.DataFrame): ?
    """
    pd_log_adjust = pd_log.copy()
    pd_log_adjust = pd_log_adjust.drop(['CUSTOM.date [local]','CAMERA.isVideo','OSD.droneType'], axis='columns')

    pd_log_final = pd.DataFrame(index=range(cnt_frame), columns=pd_log_adjust.columns)

    cnt = 0.
    cnt_inc = cnt_frame / len(pd_log_adjust)
    for idx in range(len(pd_log_adjust)):
        pd_log_final.iloc[int(cnt)] = pd_log_adjust.iloc[idx]
        cnt += cnt_inc

    pd_log_final = pd_log_final.astype('float')
    pd_log_final = pd_log_final.interpolate(method='values')

    pd_log_final.insert(0, 'FrameCnt', [idx+1 for idx in range(cnt_frame)])

    return pd_log_final


def main(argv):
    """
        ?

        argv (?): ?
    """
    args = argv
    if len(args) != 1:
        print("[ERROR] Insufficient argument")

    root_dir = args[0]
    # root_dir = 'C:/Users/user/Desktop/dva-test/log/data/231110_iphone'

    log_dirs = glob.glob(root_dir+'/DJIFlightRecord_*.csv')
    assert len(log_dirs) == 1, '[ERROR] Input log file should be one'
    log_dir = log_dirs[0]
    srt_dir_list = glob.glob(root_dir+'/*.SRT')

    pd_use_log, flight_date = get_log(log_dir)
    osd_dronetype = list(set(pd_use_log['OSD.droneType']))[0]
    osd_typ = drone_type[osd_dronetype]

    if len(srt_dir_list):
        for srt_dir in srt_dir_list:
            out_dir = srt_dir.replace('SRT', 'csv')

            pd_use_srt = get_srt(srt_dir, osd_typ)
            pd_use_idx = get_mov_idx(pd_use_log)

            pd_use_log_adjust, start_idx, end_idx = match_srt(pd_use_log, pd_use_srt, pd_use_idx)
            pd_use_log_final = adjust_csv_w_srt(pd_use_log_adjust, pd_use_srt)

            # fill unexpected NaN value
            pd_use_log_final = pd_use_log_final.fillna(method='backfill')
            pd_use_log_final = pd_use_log_final.fillna(method='ffill')

            # adjust height
            osd_info = (float(pd_use_log_final['OSD.latitude'][0]), float(pd_use_log_final['OSD.longitude'][0]),
                        float(pd_use_log_final['HOME.latitude'][0]), float(pd_use_log_final['HOME.longitude'][0]))

            osd_hgt_offset = adjust_height.get_offset(osd_info, flight_date)
            print("Adjusted height : ", osd_hgt_offset)

            pd_use_log_final['adjusted height'] = [hgt * 0.3048 + osd_hgt_offset for hgt in pd_use_log_final['OSD.height [ft]']]
            pd_use_log_final['Drone type'] = [osd_dronetype] * len(pd_use_log_final)
            pd_use_log_final = pd_use_log_final.drop(['OSD.height [ft]', 'OSD.altitude [ft]'], axis=1)

            # save sync csv
            pd_use_log_final.to_csv(out_dir, index=False)

            print(os.path.basename(srt_dir), 'match with log file.', 'start idx:', start_idx, 'end idx:', end_idx)

    else:
        pd_use_idx = get_mov_idx(pd_use_log)

        mov_dir_list = glob.glob(root_dir+'/DJI_*.MP4') + glob.glob(root_dir+'/DJI_*.MOV')
        for idx, mov_dir in enumerate(mov_dir_list):
            out_dir = mov_dir[:-4] + '.csv'
            cnt_frame = get_num_frame(mov_dir)

            start_idx, end_idx = pd_use_idx['idx_start'][idx], pd_use_idx['idx_end'][idx]
            pd_use_log_adjust = pd_use_log[start_idx:end_idx+1]
            pd_use_log_final = adjust_csv_wo_srt(pd_use_log_adjust, cnt_frame)

            # fill unexpected NaN value
            pd_use_log_final = pd_use_log_final.fillna(method='backfill')
            pd_use_log_final = pd_use_log_final.fillna(method='ffill')

            osd_info = (float(pd_use_log_final['OSD.latitude'][0]), float(pd_use_log_final['OSD.longitude'][0]),
                        float(pd_use_log_final['HOME.latitude'][0]), float(pd_use_log_final['HOME.longitude'][0]))

            osd_hgt_offset = adjust_height.get_offset(osd_info, flight_date)
            print("Adjusted height : ", osd_hgt_offset)

            pd_use_log_final['adjusted height'] = [hgt * 0.3048 + osd_hgt_offset for hgt in
                                                   pd_use_log_final['OSD.height [ft]']]

            pd_use_log_final = pd_use_log_final.drop(['OSD.height [ft]', 'OSD.altitude [ft]'], axis=1)

            pd_use_log_final.to_csv(out_dir, index=False)

    return


def do_sync(video_path, csv_path, srt_path, save_path):
    """
        srt 파일과 csv 파일 간의 동기화를 수행한 파일을 저장합니다.

        동기화된 파일은 `save_path` 경로에 `sync_log.csv`라는 파일명으로 저장됩니다.

        Args
            - video_path (str): 입력 비디오 파일 경로
            - csv_path (str): csv 파일 경로
            - srt_path (str): srt 파일 경로
            - save_path (str): 동기화된 파일이 저장될 경로
    """

    log_dirs = glob.glob(os.path.join(csv_path, '*.csv'))
    assert len(log_dirs) == 1, '[ERROR] Input log file should be one'
    log_dir = log_dirs[0]
    srt_dir_list = glob.glob(os.path.join(srt_path, '*.srt'))

    pd_use_log, flight_date = get_log(log_dir)
    osd_dronetype = list(set(pd_use_log['OSD.droneType']))[0]
    osd_typ = drone_type[osd_dronetype]

    video_list_1 = glob.glob(os.path.join(video_path, '*.mov'))
    video_list_2 = glob.glob(os.path.join(video_path, '*.mp4'))
    mov_dir_list = video_list_1 + video_list_2
    cnt_frame = get_num_frame(mov_dir_list[0])
    
    out_dir = os.path.join(save_path, 'sync_log.csv')

    if len(srt_dir_list):
        for srt_dir in srt_dir_list:
            # out_dir = srt_dir.replace('SRT', 'csv')

            pd_use_srt = get_srt(srt_dir, osd_typ)
            pd_use_idx = get_mov_idx(pd_use_log)

            pd_use_log_adjust, start_idx, end_idx = match_srt(pd_use_log, pd_use_srt, pd_use_idx)
            pd_use_log_final = adjust_csv_w_srt(pd_use_log_adjust, pd_use_srt, cnt_frame)

            # fill unexpected NaN value
            pd_use_log_final = pd_use_log_final.fillna(method='backfill')
            pd_use_log_final = pd_use_log_final.fillna(method='ffill')

            # adjust height
            osd_info = (float(pd_use_log_final['OSD.latitude'][0]), float(pd_use_log_final['OSD.longitude'][0]),
                        float(pd_use_log_final['HOME.latitude'][0]), float(pd_use_log_final['HOME.longitude'][0]))

            osd_hgt_offset = get_offset(osd_info, flight_date)
            print("Adjusted height : ", osd_hgt_offset)

            pd_use_log_final['adjusted height'] = [hgt * 0.3048 + osd_hgt_offset for hgt in pd_use_log_final['OSD.height [ft]']]
            pd_use_log_final['Drone type'] = [osd_dronetype] * len(pd_use_log_final)
            pd_use_log_final = pd_use_log_final.drop(['OSD.height [ft]', 'OSD.altitude [ft]'], axis=1)

            # save sync csv
            pd_use_log_final.to_csv(out_dir, index=False)

            print(os.path.basename(srt_dir), 'match with log file.', 'start idx:', start_idx, 'end idx:', end_idx)

    else:
        pd_use_idx = get_mov_idx(pd_use_log)

        video_list_1 = glob.glob(os.path.join(video_path, '*.mov'))
        video_list_2 = glob.glob(os.path.join(video_path, '*.mp4'))
        mov_dir_list = video_list_1 + video_list_2
        for idx, mov_dir in enumerate(mov_dir_list):
            # out_dir = mov_dir[:-4] + '.csv'
            cnt_frame = get_num_frame(mov_dir)

            start_idx, end_idx = pd_use_idx['idx_start'][idx], pd_use_idx['idx_end'][idx]
            pd_use_log_adjust = pd_use_log[start_idx:end_idx+1]
            pd_use_log_final = adjust_csv_wo_srt(pd_use_log_adjust, cnt_frame)

            # fill unexpected NaN value
            pd_use_log_final = pd_use_log_final.fillna(method='backfill')
            pd_use_log_final = pd_use_log_final.fillna(method='ffill')

            osd_info = (float(pd_use_log_final['OSD.latitude'][0]), float(pd_use_log_final['OSD.longitude'][0]),
                        float(pd_use_log_final['HOME.latitude'][0]), float(pd_use_log_final['HOME.longitude'][0]))

            osd_hgt_offset = get_offset(osd_info, flight_date)
            print("Adjusted height : ", osd_hgt_offset)

            pd_use_log_final['adjusted height'] = [hgt * 0.3048 + osd_hgt_offset for hgt in
                                                   pd_use_log_final['OSD.height [ft]']]

            pd_use_log_final = pd_use_log_final.drop(['OSD.height [ft]', 'OSD.altitude [ft]'], axis=1)

            pd_use_log_final.to_csv(out_dir, index=False)

    return

if __name__ == "__main__":
    # execute main function
    # argument : root directory (one csv file and many srt file are in the root directory)
    main(sys.argv[1:])