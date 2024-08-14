import time
from typing import Tuple

from device_manager.scrcpy_adb import ScrcpyADB
from data_const.coordinate import *
import math
from utils.logger import logger


class HeroControlBase:
    """
    英雄控制基类
    """

    def __init__(self, adb: ScrcpyADB):
        self.adb = adb

    @staticmethod
    def calc_mov_point(angle: float) -> Tuple[int, int]:
        """
        根据角度计算轮盘 x y 坐标
        :param angle:
        :return:
        """
        # 手机是横屏的，计算角度是按照横屏去计算的，所以这里要修改一下坐标判断
        rx, ry = roulette_wheel
        r = 125

        # 将角度转换为弧度
        angle_rad = math.radians(angle)

        x = rx + r * math.cos(angle_rad)
        y = ry - r * math.sin(angle_rad)
        return int(x), int(y)

    def touch_roulette_wheel(self):
        """
        按压轮盘中心位置
        :return:
        """
        rx, ry = roulette_wheel
        self.adb.touch_start((rx, ry))

    def swipe_roulette_wheel(self, angle: float):
        """
        转动轮盘位置
        :return:
        """
        x, y = self.calc_mov_point(angle)
        self.adb.touch_move((x, y))

    def move(self, angle: float, t: float = 0.5):
        """
        角色移动
        :param angle:
        :param t:
        :return:
        """
        rx, ry = roulette_wheel
        # 计算轮盘x, y坐标
        x, y = self.calc_mov_point(angle)
        logger.debug(f"移动到坐标:{x},{y}")
        self.adb.swipe((rx, ry), (x, y), t)

    def quick_move(self, direction: str, t: int or float):
        """
        快捷移动
        :param direction:
        :param t:
        :return:
        """
        direction_to_angle = {
            "right": 0,
            "right_up": 45,
            "up": 90,
            "left_up": 125,
            "left": 180,
            "left_down": 225,
            "down": 270,
            "right_down": 315,
        }
        if direction in direction_to_angle:
            angle = direction_to_angle[direction]
            self.move(angle, t)
        else:
            logger.error("移动方向错误")

    def normal_attack(self, t: float or int = 1):
        """
        普通攻击
        :return:
        """
        x, y = attack
        logger.info("执行普通攻击")
        self.adb.touch((x, y), t)

    def skill_attack(self, skill_coordinate: Tuple[int, int], t: float or int = 0.1):
        """
        技能攻击
        :param skill_coordinate: 技能坐标
        :param t:
        :return:
        """
        x, y = skill_coordinate
        logger.info("执行技能攻击")
        self.adb.touch((x, y), t)

    def combination_skill_attack(self, skill_coordinates: [Tuple[int, int]]):
        """
        组合技能攻击
        :param skill_coordinates:
        :return:
        """
        for skill_coordinate in skill_coordinates:
            self.skill_attack(skill_coordinate)
            time.sleep(0.5)

    def awaken_attack(self, t: float or int = 0.1):
        """
        觉醒技能攻击
        :param t:
        :return:
        """
        x, y = awaken_skill
        logger.info("执行觉醒攻击")
        self.adb.touch((x, y), t)


if __name__ == '__main__':
    ctl = HeroControlBase(ScrcpyADB())
# ctl.move(180, 3)
# time.sleep(0.3)
# ctl.attack()
# time.sleep(0.3)
# ctl.move(270, 5)
# time.sleep(0.3)
# ctl.attack(3)
