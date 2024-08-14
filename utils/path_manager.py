import os


class PathManager:
    """
    路径管理
    """
    ROOT_OATH = os.path.dirname(os.path.dirname(os.path.abspath(__file__))).replace('\\', '/')

    PROJECT_NAME = ROOT_OATH.split('/')[-1]

    LOG_PATH = ROOT_OATH + '/logs/'

    MODEL_PATH = ROOT_OATH + '/model/'

    DUNGEON_INFO_PATH = ROOT_OATH + '/data/dungeon_info.json'
