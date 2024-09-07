

import scrcpy
from adbutils import adb
import cv2 as cv


class ScrcpyADB:
    """
    连接设备，并启动 scrcpy
    """

    def __init__(self):
        devices = adb.device_list()[0]
        if not devices:
            raise Exception("No devices connected")
        adb.connect("127.0.0.1:5555")
        # self.client = scrcpy.Client(device=devices, max_width=600, max_fps=10)
        self.client = scrcpy.Client(device=devices, max_width=1168, max_fps=30)
        self.client.add_listener(scrcpy.EVENT_FRAME, self.on_frame)
        self.client.start(threaded=True)

    def on_frame(self, frame: cv.Mat):
        """
        获取当前帧进行渲染
        """
        if frame is not None:
            self.last_screen = frame
            cv.imshow('frame', frame)
            cv.waitKey(1)
    


if __name__ == '__main__':
    this = ScrcpyADB()
    # this.display_queue_frames()
   
