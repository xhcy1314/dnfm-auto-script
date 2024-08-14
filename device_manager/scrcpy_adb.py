import queue
import sys

import threading
import time
from typing import Tuple

import scrcpy
from adbutils import adb
import cv2 as cv
from ncnn.utils import Detect_Object

from device_manager.constant import TARGET_COLOUR
from utils.logger import logger
from utils.yolov5 import YoloV5s


class ScrcpyADB:
    """
    连接设备，并启动 scrcpy
    """

    def __init__(self):
        devices = adb.device_list()[0]
        if not devices:
            raise Exception("No devices connected")
        adb.connect("127.0.0.1:5555")

        self.client = scrcpy.Client(device=devices, max_width=2688, max_fps=5)
        self.client.add_listener(scrcpy.EVENT_FRAME, self.on_frame)
        self.client.start(threaded=True)

        self.last_screen = None
        self.yolo = self.init_yolov5()

        self.frame_queue = queue.Queue()
        self.stop_event = threading.Event()

    @staticmethod
    def init_yolov5():
        """
        初始化 yolo v5
        :return:
        """
        return YoloV5s(num_threads=4, use_gpu=True)

    def on_frame(self, frame: cv.Mat):
        """
        获取当前帧进行渲染
        """
        if frame is not None:
            self.last_screen = frame
            try:
                result = self.yolo(frame)
                self.picture_frame(frame, result)
            except Exception as e:
                logger.error(e)
                
    def display_frames(self, frame):
        """
        渲染帧
        :return:
        """
        try:
            cv.namedWindow('frame', cv.WINDOW_NORMAL)
            cv.resizeWindow('frame', 1168, 540)
            cv.imshow('frame', frame)
            cv.waitKey(1)
        except Exception as e:
            logger.error(e)
        


    def display_queue_frames(self):
        """
        渲染队列帧
        :return:
        """
        if sys.platform.startswith('darwin'):
            while not self.stop_event.is_set():
                try:
                    frame = self.frame_queue.get(timeout=1)
                    if frame is not None:
                        self.display_frames(frame)
                except queue.Empty:
                    continue
                except Exception as e:
                    logger.error(e)
    

    def picture_frame(self, frame: cv.Mat, objs: [Detect_Object]):
        """
        在 cv 中画出目标框，并显示标签名称和置信度
        :return:
        """
        font = cv.FONT_HERSHEY_SIMPLEX  # 字体样式
        font_scale = 1  # 字体大小
        thickness = 3  # 文本线条厚

        for obj in objs:
            color = TARGET_COLOUR.get(obj.label)
            cv.rectangle(frame, (int(obj.rect.x), int(obj.rect.y)), (int(obj.rect.x + obj.rect.w), int(obj.rect.y + + obj.rect.h)), color, 2)

            # 构造显示的标签文本
            label_text = f"{self.yolo.class_names[int(obj.label)]}:{obj.prob:.2f}"

            # 计算文本位置
            text_size, _ = cv.getTextSize(label_text, font, font_scale, thickness)
            text_x = int(obj.rect.x)
            text_y = int(obj.rect.y - 5)  # 将文本放置在矩形框上方

            # 如果文本超出边界，则将其放置在矩形框下方
            if text_y < 0:
                text_y = int(obj.rect.y + obj.rect.h + 5)

            # 绘制标签文本
            cv.putText(frame, label_text, (text_x, text_y), font, font_scale, color, thickness=thickness)

         # mac 系统需要把帧添加到队列
        if sys.platform.startswith('darwin'):
            self.frame_queue.put(frame)
        # 其他 windows
        else:
            self.display_frames(frame)

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

    def touch(self, coordinate: Tuple[int or float, int or float], t: int or float = 0.5):
        """
        :param coordinate:坐标
        :param t:按压时间
        :return:
        """
        self.touch_start(coordinate)
        time.sleep(t)
        self.touch_end(coordinate)

    def swipe(self, start_coordinate: Tuple[int or float, int or float], end_coordinate: Tuple[int or float, int or float], t: int or float = 0.5):
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


if __name__ == '__main__':
    this = ScrcpyADB()
    this.display_queue_frames()
   
