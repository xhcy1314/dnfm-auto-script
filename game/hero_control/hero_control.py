from device_manager.scrcpy_adb import ScrcpyADB
import time


def get_hero_control(name: str, scrcpy_adb: ScrcpyADB):
    """
    获取英雄控制的实例
    :param name:英雄名称
    :param scrcpy_adb:设备链接实例
    :return:
    """
    if name == 'hong_yan':
        from game.hero_control.hong_yan import HongYan
        return HongYan(scrcpy_adb)
    elif name == 'nai_ma':
        from game.hero_control.nai_ma import NaiMa
        return NaiMa(scrcpy_adb)
    elif name == 'hua_hua':
      from game.hero_control.hua_hua import Huahua
      return Huahua(scrcpy_adb)
    elif name == 'wu_shen':
      from game.hero_control.wu_shen import WuShen
      return WuShen(scrcpy_adb)
    elif name == 'axl':
      from game.hero_control.axl import AXL
      return AXL(scrcpy_adb)
    elif name == 'jian_zong':
      from game.hero_control.jian_zong import JianZong
      return JianZong(scrcpy_adb)
    
    else:
        raise ValueError(f'{name} is not support')


if __name__ == '__main__':
    adb = ScrcpyADB()
    hero = get_hero_control('jian_zong', adb)
    # hero.room_skill_combo.get(6)()
    hero.skill_combo_5() 
    # hero.move(30, 1)
    # time.sleep(2)
    # hero.move(60, 1)
    # time.sleep(2)
    
    # hero.move(400, 1)
    # hero.move(300, 1)
    # adb.touch([1018, 75])
    # adb.display_frames()
    # hero.move(0, 1) 右边
    # hero.move(90, 1) 上
    # hero.move(180, 1) 左
    # hero.move(270, 1) 下
