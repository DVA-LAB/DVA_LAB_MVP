import pandas as pd
from haversine import haversine

use_cols = ['CUSTOM.date [local]', 'CUSTOM.updateTime [local]', 'OSD.flyTime [s]',
            'OSD.latitude', 'OSD.longitude', 'OSD.height [ft]', 'OSD.altitude [ft]',
            'OSD.pitch', 'OSD.roll', 'OSD.yaw', 'GIMBAL.pitch', 'GIMBAL.roll', 'GIMBAL.yaw',
            'CAMERA.isVideo']


# log csv --> dataframe
def get_log(csv_path):
    pd_log = pd.read_csv(csv_path, encoding='utf-8', low_memory=False).reset_index(drop=False)
    pd_log.columns = list(pd_log.iloc[0])

    pd_use_log = pd_log[1:][use_cols].reset_index(drop=True)

    return pd_use_log


# log srt --> dataframe
def get_srt(srt_path):
    srt_file = open(srt_path, 'r', encoding='utf-8')
    txt_srt = srt_file.readlines()
    srt_file.close()

    df_time, df_diff, df_lat, df_lon = [], [], [], []
    for idx, line in enumerate(txt_srt):
        line = line.strip()
        if idx % 6 == 2:
            df_diff.append(int(line[-4:-2]))
        elif idx % 6 == 3:
            df_time.append(line[11:27])
        elif idx % 6 == 4:
            divide = line.split('] [')
            df_lat.append(float(divide[7][11:]))
            df_lon.append(float(divide[8][13:]))

    pd_srt = pd.DataFrame({'time_now': df_time, 'time_diff': df_diff, 'latitude': df_lat, 'longitude': df_lon})

    return pd_srt


# search SRT index candidates in csv
def get_mov_idx(pd_log):
    mov_status = list(pd_log['CAMERA.isVideo'])
    start_idx = []
    end_idx = []

    for idx in range(1, len(mov_status)):
        if mov_status[idx - 1] == 'False' and mov_status[idx] == 'True':
            start_idx.append(idx)

        if mov_status[idx - 1] == 'True' and mov_status[idx] == 'False':
            end_idx.append(idx)

    pd_idx = pd.DataFrame({'idx_start': start_idx, 'idx_end': end_idx})

    return pd_idx


# search SRT matching region among candidates based on haversine index
def match_srt(pd_log, pd_srt, pd_idx):
    # get lat/lon info of start & end point in input SRT file
    start_point = list(pd_srt[['latitude','longitude']].iloc[0])
    end_point = list(pd_srt[['latitude','longitude']].iloc[-1])


    # get lat/lon info of start & end point in entire CSV file
    coord_start = pd_log[['OSD.latitude', 'OSD.longitude']].iloc[list(pd_idx['idx_start'])]
    coord_end = pd_log[['OSD.latitude', 'OSD.longitude']].iloc[list(pd_idx['idx_end'])]

    # search SRT matching region
    dist = []
    for idx in range(len(coord_start)):
        dist.append(haversine(start_point,
                              [float(coord_start['OSD.latitude'].iloc[idx]), float(coord_start['OSD.longitude'].iloc[idx])]))

    start_idx, end_idx = coord_start.index[dist.index(min(dist))], coord_end.index[dist.index(min(dist))]

    # adjust SRT matching region based on time (search +&- 5s)
    search_start = pd_log[start_idx-5:start_idx+5][['OSD.latitude', 'OSD.longitude']]
    search_end = pd_log[end_idx-5:end_idx+5][['OSD.latitude', 'OSD.longitude']]

    dist_start = []
    for idx in range(len(search_start)):
        dist = haversine(start_point,
                         [float(list(search_start['OSD.latitude'])[idx]),
                          float(list(search_start['OSD.longitude'])[idx])])
        dist_start.append(dist)
    search_start['distance'] = dist_start

    dist_end = []
    for idx in range(len(search_end)):
        dist = haversine(end_point,
                         [float(list(search_end['OSD.latitude'])[idx]), float(list(search_end['OSD.longitude'])[idx])])
        dist_end.append(dist)
    search_end['distance'] = dist_end

    pd_log_adjust = pd_log[search_start['distance'].idxmin():search_end['distance'].idxmin() + 1]

    return pd_log_adjust


# adjust SRT matching region based on SRT file
def adjust_csv(pd_log, pd_srt):
    pd_log_adjust = pd_log.copy()
    pd_log_adjust = pd_log_adjust.drop(['CUSTOM.date [local]', 'CUSTOM.updateTime [local]', 'OSD.flyTime [s]',
                                        'CAMERA.isVideo'], axis='columns')

    pd_log_final = pd.DataFrame(index=range(len(pd_srt)), columns=pd_log_adjust.columns)

    cnt = 0.
    cnt_inc = len(pd_srt) / len(pd_log_adjust)
    for idx in range(len(pd_log_adjust)):
        pd_log_final.iloc[int(cnt)] = pd_log_adjust.iloc[idx]
        cnt += cnt_inc

    pd_log_final = pd_log_final.astype('float')
    pd_log_final = pd_log_final.interpolate(method='values')

    return pd_log_final


if __name__ == "__main__":
    csv_dir = 'C:/Users/user/Desktop/dolphin/log/data/case01/DJIFlightRecord_2023-10-15_[17-12-33].csv'
    srt_dir = 'C:/Users/user/Desktop/dolphin/log/data/case01/DJI_0107.SRT'
    out_dir = 'C:/Users/user/Desktop/dolphin/log/data/case01/DJI_0107.csv'

    pd_use_log, pd_use_srt = get_log(csv_dir), get_srt(srt_dir)
    pd_use_idx = get_mov_idx(pd_use_log)

    pd_use_log_adjust = match_srt(pd_use_log, pd_use_srt, pd_use_idx)
    pd_use_log_final = adjust_csv(pd_use_log_adjust, pd_use_srt)

    pd_use_log_final.to_csv(out_dir)