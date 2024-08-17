from scrcpy_adb_c_img import ScrcpyADB
import time
import cv2 as cv
import os
from datetime import datetime



# 1280 * 720 dpi 320
if __name__ == '__main__':
    adb = ScrcpyADB()

    index = 0
    
        # 获取当前时间戳
    current_time = datetime.now().strftime("%Y%m%d_%H%M%S")

    # 生成文件路径
    folder_path = f'create_img/img/{current_time}'
    

    # 如果文件夹不存在，则创建它
    os.makedirs(folder_path, exist_ok=True)

    while True:
        index += 1
        time.sleep(2)
        screen = adb.last_screen
        file_path = os.path.join(folder_path, f'{index}.png')
        cv.imwrite(file_path, screen)
