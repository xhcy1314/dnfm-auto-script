import queue
import os
import threading
import time
from typing import Tuple

import scrcpy
from adbutils import adb
import cv2 as cv

from device_manager.constant import TARGET_COLOUR
from utils.logger import logger
from utils.path_manager import PathManager

# from utils.yolov5 import YoloV5s
from utils.yolov5_onnx import YOLOv5
from device_manager.auto_cleaning_queue import AutoCleaningQueue


class ScrcpyADB:
    """
    连接设备，并启动 scrcpy
    """

    def __init__(self, max_width=1168, max_fps=30):
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

    def touch_start(self, coordinate: Tuple[int or float, int or float]):
        """
        触摸屏幕
        :param coordinate:坐标
        :return:
        """
        x, y = coordinate
        self.client.control.touch(int(x), int(y), scrcpy.ACTION_DOWN)

    def touch_move(self, coordinate: Tuple[int or float, int or float]):
        """
        触摸拖动
        :param coordinate: 坐标
        :return:
        """
        x, y = coordinate
        self.client.control.touch(int(x), int(y), scrcpy.ACTION_MOVE)

    def touch_end(self, coordinate: Tuple[int or float, int or float] = (0, 0)):
        """
        释放触摸
        :param coordinate:坐标
        :return:
        """
        x, y = coordinate
        self.client.control.touch(int(x), int(y), scrcpy.ACTION_UP)

    def touch(
        self, coordinate: Tuple[int or float, int or float], t: int or float = 0.5
    ):
        """
        :param coordinate:坐标
        :param t:按压时间
        :return:
        """
        self.touch_start(coordinate)
        time.sleep(t)
        self.touch_end(coordinate)

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
    this = ScrcpyADB()
    while True:
        if this.show_queue.empty():
            time.sleep(0.001)
            continue
        image,result = this.show_queue.get()
        for boxs in result:
            # 把坐标从 float 类型转换为 int 类型
            det_x1, det_y1, det_x2, det_y2,conf,label = boxs
            # 裁剪目标框对应的图像640*img1/img0 
            x1 = int(det_x1*image.shape[1])
            y1 = int(det_y1*image.shape[0])
            x2 = int(det_x2*image.shape[1])
            y2 = int(det_y2*image.shape[0])
            # 绘制矩形边界框
            cv.rectangle(image, (x1, y1), (x2, y2), (0, 255, 0), 2)
            cv.putText(image, "{:.2f}".format(conf), (int(x1), int(y1-10)), cv.FONT_HERSHEY_SIMPLEX, 0.5, (0,0,255), 2)
            cv.putText(image, this.yolo.label[int(label)], (int(x1), int(y1-30)), cv.FONT_HERSHEY_SIMPLEX, 0.5, (0,0,255), 2)
        image = cv.resize(image,(1800,int(image.shape[0]*1800/image.shape[1])))
        cv.imshow("Image", image)
        cv.waitKey(1)
        
