import queue
import os
import threading
import time
from typing import Tuple

import scrcpy
from adbutils import adb
import cv2 as cv

from utils.logger import logger
from utils.path_manager import PathManager

# from utils.yolov5 import YoloV5s
from utils.yolov5_onnx import YOLOv5
from device_manager.auto_cleaning_queue import AutoCleaningQueue


class ScrcpyADB:
    """
    连接设备，并启动 scrcpy
    """

    def __init__(self, max_width=1168, max_fps=15):
        devices = adb.device_list()[0]
        if not devices:
            raise Exception("No devices connected")
        adb.connect("127.0.0.1:5555")

        self.client = scrcpy.Client(
            device=devices, max_width=max_width, max_fps=max_fps
        )
        self.client.add_listener(scrcpy.EVENT_FRAME, self.on_frame)
        self.client.start(threaded=True)

        self.last_screen = None
        self.image_queue = AutoCleaningQueue(maxsize=3)
        self.infer_queue = AutoCleaningQueue(maxsize=3)
        self.show_queue = AutoCleaningQueue(maxsize=3)
        self.yolo = self.init_yolov5(
            self.image_queue, self.infer_queue, self.show_queue
        )

        self.frame_queue = queue.Queue()
        self.stop_event = threading.Event()

    @staticmethod
    def init_yolov5(image_queue, infer_queue, show_queue):
        """
        初始化 yolo v5
        :return:
        """
        return YOLOv5(
            os.path.join(PathManager.MODEL_PATH, "best.onnx"),
            image_queue,
            infer_queue,
            show_queue,
        )

    def on_frame(self, frame: cv.Mat):
        """
        获取当前帧进行渲染
        """
        if frame is not None:
            try:
                self.image_queue.put(frame)
            except Exception as e:
                logger.error(e)

    def touch_start(self, coordinate: Tuple[int or float, int or float], id: int = -1):
        """
        触摸屏幕
        :param coordinate:坐标
        :return:
        """
        x, y = coordinate
        # logger.info('moveV2 ACTION_DOWN')
        # logger.info(id)
        # logger.info(coordinate)
        self.client.control.touch(int(x), int(y), scrcpy.ACTION_UP, id)
        time.sleep(0.1)
        self.client.control.touch(int(x), int(y), scrcpy.ACTION_DOWN, id)

    def touch_move(self, coordinate: Tuple[int or float, int or float], id: int = -1):
        """
        触摸拖动
        :param coordinate: 坐标
        :return:
        """
        # logger.info('moveV2 ACTION_MOVE')
        x, y = coordinate
        self.client.control.touch(int(x), int(y), scrcpy.ACTION_MOVE, id)

    def touch_end(
        self, coordinate: Tuple[int or float, int or float] = (0, 0), id: int = -1
    ):
        """
        释放触摸
        :param coordinate:坐标
        :return:
        """
        # logger.info('moveV2 ACTION_UP')
        # logger.info(id)
        x, y = coordinate
        self.client.control.touch(int(x), int(y), scrcpy.ACTION_UP, id)

    def touch(
        self, coordinate: Tuple[int or float, int or float], t: int or float = 0.5, id: int = -1
    ):
        """
        :param coordinate:坐标
        :param t:按压时间
        :return:
        """
        self.touch_start(coordinate, id)
        time.sleep(t)
        self.touch_end(coordinate, id)

    def swipe(
        self,
        start_coordinate: Tuple[int or float, int or float],
        end_coordinate: Tuple[int or float, int or float],
        t: int or float = 0.5,
    ):
        """
        实现屏幕拖动（滑动手势）
        :param start_coordinate: 起始点的坐标
        :param end_coordinate: 结束点的坐标
        :param t: 持续时间，默认 0.5 秒
        """
        self.touch_start(start_coordinate)
        time.sleep(0.1)
        self.touch_move(end_coordinate)
        time.sleep(t)
        self.touch_end()


if __name__ == "__main__":
    adb = ScrcpyADB()
