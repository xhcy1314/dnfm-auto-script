import os.path
import random
import sys
from typing import Tuple, List

from utils.yolov5 import YoloV5s
from utils.logger import logger
from device_manager.scrcpy_adb import ScrcpyADB
from game.hero_control.hero_control import get_hero_control
from utils.path_manager import PathManager
import time
import cv2 as cv
from ncnn.utils.objects import Detect_Object
import math
import numpy as np
import threading


def get_detect_obj_bottom(obj: Detect_Object) -> Tuple[int, int]:
    """
    获取检测对象的底部坐标
    :param obj:
    :return:
    """
    return int(obj.rect.x + obj.rect.w / 2), int(obj.rect.y + obj.rect.h)


def calc_angle(hero_pos: Tuple[int, int], target_pos: Tuple[int, int]) -> float:
    """
    计算英雄和目标的角度
    角度从正 x 轴（向右方向）逆时针计算
    :return:
    """
    # 计算两点之间的水平和垂直距离,这里需要注意的是，手机玩游戏的时候是横屏，所以 X 坐标和 Y 坐标是需要对调的
    delta_y = hero_pos[1] - target_pos[1]
    delta_x = hero_pos[0] - target_pos[0]

    # 计算角度（以正右方向为0度，正上方为90度）
    angle_rad = math.atan2(delta_y, delta_x)
    angle_deg = 180 - int(angle_rad * 180 / math.pi)

    return angle_deg


def is_within_error_margin(
    coord1: Tuple[int, int],
    coord2: Tuple[int, int],
    x_error_margin: int = 100,
    y_error_margin: int = 50,
) -> bool:
    """
    检查两个坐标点之间的误差是否在指定范围内。

    :param coord1: 第一个坐标点 (x1, y1)
    :param coord2: 第二个坐标点 (x2, y2)
    :param x_error_margin: x 坐标的误差范围
    :param y_error_margin: y 坐标的误差范围
    :return: 如果误差在范围内返回 True，否则返回 False
    """
    x1, y1 = coord1
    x2, y2 = coord2

    x_error = abs(x1 - x2)
    y_error = abs(y1 - y2)

    return x_error <= x_error_margin and y_error <= y_error_margin


def calculate_distance(coord1: Tuple[int, int], coord2: Tuple[int, int]) -> float:
    """
    计算两个坐标之间的欧几里得距离
    :param coord1: 第一个坐标 (x, y)
    :param coord2: 第二个坐标 (x, y)
    :return: 距离
    """
    return math.sqrt((coord1[0] - coord2[0]) ** 2 + (coord1[1] - coord2[1]) ** 2)


def find_nearest_target_to_the_hero(
    hero: Tuple[int, int], target: List[Tuple[int, int]]
):
    """
    寻找到距离英雄最近的目标
    :param hero: 英雄的坐标 (x, y)
    :param target: 怪物坐标的列表 [(x1, y1), (x2, y2), ...]
    :return: 距离英雄最近的怪物坐标 (x, y)
    """
    if not target:
        return None

    closest_target = min(target, key=lambda t: calculate_distance(hero, t))
    return closest_target


def calculate_direction_based_on_angle(angle: int or float):
    """
    根据角度计算方向
    :param angle:
    :return:
    """
    if 0 <= angle <= 360:
        if 0 <= angle <= 90:
            return ["up", "right"]
        elif 90 < angle <= 180:
            return ["up", "left"]
        elif 180 < angle <= 270:
            return ["down", "left"]
        else:
            return ["down", "right"]
    else:
        return None


def get_door_coordinate_by_direction(direction):
    """
    根据方向计算下一个房间的门 lable
    :param direction:
    :return:
    """
    direction_to_direction = {
        "up": "opendoor_u",
        "down": "opendoor_d",
        "left": "opendoor_l",
        "right": "opendoor_r",
    }
    return direction_to_direction.get(direction, "")


class GameAction:
    """
    游戏控制
    """

    LABLE_LIST = [
        line.strip()
        for line in open(os.path.join(PathManager.MODEL_PATH, "new.txt")).readlines()
    ]

    LABLE_INDEX = {}
    for i, lable in enumerate(LABLE_LIST):
        LABLE_INDEX[i] = lable

    def __init__(self, hero_name: str, adb: ScrcpyADB):
        self.hero_ctrl = get_hero_control(hero_name, adb)
        self.yolo = YoloV5s(num_threads=4, use_gpu=True)
        self.adb = adb
        self.room_index = 0
        self.special_room = False  # 狮子头
        self.boss_room = False  # boss
        self.next_room_direction = "down"  # 下一个房间的方向

    def random_move(self):
        """
        防卡死
        :return:
        """
        logger.info("随机移动一下")
        self.hero_ctrl.move(random.randint(0, 360), 0.5)

    def get_map_info(self, frame=None, show=False):
        """
        获取当前地图信息
        :return:
        """
        if sys.platform.startswith("win"):
            frame = self.adb.last_screen if frame is None else frame
        else:
            frame = self.adb.frame_queue.get(timeout=1) if frame is None else frame
        result = self.yolo(frame)
        self.adb.picture_frame(frame, result)

        lable_list = [
            line.strip()
            for line in open(
                os.path.join(PathManager.MODEL_PATH, "new.txt")
            ).readlines()
        ]
        result_dict = {}
        for lable in lable_list:
            result_dict[lable] = []

        for detection in result:
            label = GameAction.LABLE_INDEX.get(detection.label)
            if label in result_dict:
                result_dict[label].append(detection)

        final_result = {}
        for label, objects in result_dict.items():
            count = len(objects)
            bottom_centers = [get_detect_obj_bottom(obj) for obj in objects]
            final_result[label] = {
                "count": count,
                "objects": objects,
                "bottom_centers": bottom_centers,
            }

        return final_result

    def get_items(self):
        """
        捡材料
        :return:
        """
        logger.info("开始捡材料")
        start_move = False
        while True:
            map_info = self.get_map_info(show=True)
            itme_list = self.is_exist_item(map_info)
            if not itme_list:
                logger.info("材料全部捡完")
                self.adb.touch_end()
                return True
            else:
                if map_info["hero"]["count"] != 1:
                    self.random_move()
                    continue
                else:
                    # 循环捡东西
                    hx, hy = map_info["hero"]["bottom_centers"][0]
                    closest_item = find_nearest_target_to_the_hero((hx, hy), itme_list)
                    angle = calc_angle((hx, hy), closest_item)
                    if not start_move:
                        self.hero_ctrl.touch_roulette_wheel()
                        start_move = True
                    else:
                        self.hero_ctrl.swipe_roulette_wheel(angle)

    @staticmethod
    def is_exist_monster(map_info):
        """
        判断房间是否存在怪物,如果存在怪物就把怪物坐标返回去，否则返回空
        :return:
        """
        if (
            map_info["Monster"]["count"]
            and map_info["Monster_ds"]["count"]
            and map_info["Monster_szt"]["count"] == 0
        ):
            return []
        else:
            monster = []
            if map_info["Monster"]["count"] > 0:
                monster.extend(map_info["Monster"]["bottom_centers"])
            if map_info["Monster_ds"]["count"] > 0:
                monster.extend(map_info["Monster_ds"]["bottom_centers"])
            if map_info["Monster_szt"]["count"] > 0:
                monster.extend(map_info["Monster_szt"]["bottom_centers"])
            return monster

    @staticmethod
    def is_exist_item(map_info):
        """
        判断房间是否存在材料
        :return:
        """
        if map_info["equipment"]["count"] == 0:
            return []
        else:
            return map_info["equipment"]["bottom_centers"]

    @staticmethod
    def is_exist_reward(map_info):
        """
        判断是否存在翻牌奖励
        :return:
        """
        if map_info["card"]["count"] == 0:
            return []
        else:
            return map_info["card"]["bottom_centers"]

    def is_allow_move(self, map_info):
        """
        判断是否满足移动条件，如果不满足返回原因
        :return:
        """
        if self.is_exist_monster(map_info):
            logger.info("怪物未击杀完毕，不满足过图条件,结束跑图")
            return False, "怪物未击杀"
        if self.is_exist_item(map_info):
            logger.info("存在没检的材料，不满足过图条件,结束跑图")
            return False, "存在没检的材料"
        return True, ""

    def mov_to_next_room(self, direction=None):
        """
        移动到下一个房间
        :param direction:
        :return:
        """
        logger.info("移动到下一个房间")

        start_move = False
        hlx, hly = 0, 0
        move_count = 0
        # 执行跑图逻辑
        while True:
            screen = self.hero_ctrl.adb.last_screen
            # 下一帧未生成 或 不存在 退出循环
            if screen is None:
                continue

            ada_image = cv.adaptiveThreshold(
                cv.cvtColor(screen, cv.COLOR_BGR2GRAY),
                255,
                cv.ADAPTIVE_THRESH_GAUSSIAN_C,
                cv.THRESH_BINARY_INV,
                13,
                3,
            )
            # 屏幕变黑色 则认为过图成功
            if np.sum(ada_image) == 0:
                logger.info("过图成功")
                self.adb.touch_end()
                self.mov_to_next_room()
                return True

            # 获取当前地图信息
            map_info = self.get_map_info(screen, show=True)
            # 判断是否满足进入下一个房间的条件
            conditions, reason = self.is_allow_move(map_info)
            # 不满足条件 返回 False 及 原因
            if not conditions:
                self.adb.touch_end()
                return False, reason

            # 如果没有找到英雄 则随机移动 并退出当前循环
            if map_info["hero"]["count"] == 0:
                logger.info("没有找到英雄")
                self.random_move()
                continue
            # 获取英雄坐标
            else:
                hx, hy = map_info["hero"]["bottom_centers"][0]

            # 没有箭头 随机移动一下
            if map_info["go"]["count"] == 0:
                logger.info("没有找到箭头标记")
                # 尝试查找大箭头 go_u 或 go_d
                alternative_marks = None
                if map_info["go_u"]["count"] > 0:
                    alternative_marks = map_info["go_u"]["bottom_centers"]
                    logger.info("使用 go_u 标记")
                elif map_info["go_d"]["count"] > 0:
                    alternative_marks = map_info["go_d"]["bottom_centers"]
                    logger.info("使用 go_d 标记")
                elif map_info["go_r"]["count"] > 0:
                    alternative_marks = map_info["go_r"]["bottom_centers"]
                    logger.info("使用 go_r 标记")

                if alternative_marks:
                    # 如果找到替代的标记，使用这些标记
                    marks = alternative_marks
                else:
                    # 如果没有找到替代标记，执行随机移动
                    self.random_move()
                    continue
            # 使用小箭头坐标
            else:
                marks = map_info["go"]["bottom_centers"]
            closest_mark = find_nearest_target_to_the_hero((hx, hy), marks)
            # 没有坐标异常时退出
            if closest_mark is None:
                logger.info("没有找到距离英雄最近的坐标")
                continue
            mx, my = closest_mark

            # 计算出英雄和目标的角度
            angle = calc_angle((hx, hy), (mx, my))

            # 按压轮盘
            if not start_move:
                self.hero_ctrl.touch_roulette_wheel()
                start_move = True
            # 拖动轮盘
            else:
                self.hero_ctrl.swipe_roulette_wheel(angle)


if __name__ == "__main__":
    adb = ScrcpyADB()
    # 将 display_queue_frames 放入单独的线程中执行
    # thread = threading.Thread(target=adb.display_queue_frames)
    # thread.start()

    action = GameAction("hong_yan", adb)
    # for i in range(5):
    action.mov_to_next_room()

    # adb.display_queue_frames()

    # action.mov_to_next_room()
    #     # action.get_items()
    #     time.sleep(3)
    # print(calc_angle((472, 1328), (788, 1655)))
