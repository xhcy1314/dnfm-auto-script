from data_const.coordinate import *
from device_manager.scrcpy_adb import ScrcpyADB
from game.hero_control.hero_control_base import HeroControlBase
from utils.logger import logger
import time


class JianZong(HeroControlBase):
    """
    剑宗
    """
    wait = 0.1
    def __init__(self, adb: ScrcpyADB):
        super().__init__(adb)
        self.buff1 = buff1  # buff1
        self.buff2 = buff2  # buff2
        self.awaken_skill = awaken_skill  # 觉醒
        self.attack = attack  # 普通攻击
        self.useSkills = {}  # 存放已经释放技能的房间下标
        self.room_skill_combo = {
            1: self.skill_combo_1,
            2: self.skill_combo_2,
            3: self.skill_combo_3,
            4: self.skill_combo_4,
            5: self.skill_combo_5,
            6: self.skill_combo_6,
            8: self.skill_combo_8,
            9: self.skill_combo_9,
            10: self.skill_combo_10,
            77: self.skill_combo_77,
        }
        self.skills = { # 全部技能
            "千军破": skill1,
            "瞬影破": skill2,
            "破军斩": skill3,
            "恶即斩": skill4,
            "聚怪": skill5,
            "幻剑术": skill6,
            "穿云破空剑": skill7,
            "后跳": skill8
        }  
        self.last_angle = 0
        
    def sleep_01(self): 
      time.sleep(0.1)

    # 击杀怪物
    def killMonsters(self, angle, room_index, hero_pos, close_monster):
        self.last_angle = angle
        print(self.useSkills, 'useSkills')
        if self.useSkills.get(room_index, False):
            is_close_monster = self.move_to_monster(angle, hero_pos, close_monster)
            # 普通攻击
            if is_close_monster:
              self.normal_attack(1)
              time.sleep(0.3)
        else:
            self.room_skill_combo.get((room_index + 1), self.skill_combo_77)()
            self.useSkills[room_index] = True

    def add_buff(self):
        """
        添加buff
        :return:
        """
        self.adb.touch(self.buff1)
        time.sleep(0.5)
        self.adb.swipe(self.buff2, [self.buff2[0], self.buff2[1] + 100])
        logger.info("加 buff")
        pass

    def skill_combo_1(self):
        """
        技能连招1
        :return:
        """
        self.reset()
        self.moveV2(295)
        time.sleep(0.3)
        self.moveV2(0)
        self.add_buff()
        self.adb.touch(self.skills['破军斩'], 1)
        time.sleep(0.2)
        logger.info("技能连招1")
        pass

    def skill_combo_2(self):
        """
        技能连招2
        :return:
        """
        self.sleep_01()
        self.moveV2(295)
        time.sleep(0.3)
        self.moveV2(0)
        self.adb.touch(self.skills['千军破'])
        time.sleep(0.3)
        logger.info("技能连招2")
        pass

    def skill_combo_3(self):
        """
        技能连招3
        :return:
        """
        self.sleep_01()
        self.moveV2(340)
        time.sleep(0.3)
        self.moveV2(0)
        time.sleep(0.3)
        self.adb.touch(self.skills['聚怪'])
        time.sleep(0.1)
        self.adb.touch(self.skills['幻剑术'])
        time.sleep(0.1)
        logger.info("技能连招3")
        pass
    
    def skill_combo_4(self):
        """
        技能连招4
        :return:
        """
        self.sleep_01()
        self.moveV2(340)
        time.sleep(0.3)
        self.adb.touch(self.skills['瞬影破'])
        self.moveV2(0)
        time.sleep(2)
        logger.info("技能连招4")
        pass
    
    def skill_combo_5(self):
        """
        技能连招5
        :return:
        """
        self.sleep_01()
        self.moveV2(145, 0.8)
        self.moveV2(1, 0.1)
        self.adb.touch(self.skills['破军斩'], 0.6)
        self.sleep_01()
        self.moveV2(180, 1)
        self.moveV2(90, 0.4)
        self.moveV2(180)
        time.sleep(1)
        logger.info("技能连招5")
        pass
    
    def skill_combo_6(self):
        """
        技能连招6
        :return:
        """
        self.sleep_01()
        self.moveV2(180, 0.1)
        self.adb.touch(self.awaken_skill)
        logger.info("技能连招6")
        pass
    
    def skill_combo_8(self):
        """
        技能连招8
        :return:
        """
        self.sleep_01()
        self.moveV2(335)
        time.sleep(0.4)
        self.moveV2(1)
        time.sleep(0.1)
        self.moveV2(0)
        self.adb.touch(self.skills['瞬影破'])
        time.sleep(0.1)
        pass
    
    def skill_combo_9(self):
        """
        技能连招9
        :return:
        """
        self.sleep_01()
        self.moveV2(350)
        time.sleep(0.2)
        self.moveV2(0)
        self.adb.touch(self.skills['千军破'])
        pass
    
    def skill_combo_10(self):
        """
        技能连招10
        :return:
        """
        self.sleep_01()
        self.moveV2(335)
        time.sleep(0.3)
        self.moveV2(1)
        time.sleep(0.1)
        self.adb.touch(self.skills['恶即斩'])
        pass
      
    def skill_combo_77(self):
        """
        小技能连招
        :return:
        """
        logger.info("小技能连招")
        pass
