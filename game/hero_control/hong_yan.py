from data_const.coordinate import *
from device_manager.scrcpy_adb import ScrcpyADB
from game.hero_control.hero_control_base import HeroControlBase
from utils.logger import logger


class HongYan(HeroControlBase):
    """
    红眼
    """

    def __init__(self, adb: ScrcpyADB):
        super().__init__(adb)
        self.buff = buff1  # 暴走
        self.awaken_skill = awaken_skill  # 觉醒
        self.attack = attack  # 普通攻击
        self.room_skill_combo = {
            1: self.skill_combo_1,
            2: self.skill_combo_2,
        }

    def add_buff(self):
        """
        添加buff
        :return:
        """
        logger.info("加 buff")
        pass


    def skill_combo_1(self):
        """
        技能连招1
        :return:
        """
        self.add_buff()
        self.adb.attack()
        logger.info("释放技能连招1")
        pass

    def skill_combo_2(self):
        """
        技能连招2
        :return:
        """
        pass

    def skill_combo_3(self):
        """
        技能连招3
        :return:
        """
        pass
