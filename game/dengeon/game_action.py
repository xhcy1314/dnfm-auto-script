
import random

from utils.logger import logger
from device_manager.scrcpy_adb import ScrcpyADB
from game.hero_control.hero_control import get_hero_control
import time
import cv2 as cv
import math
import numpy as np
import threading
from collections import deque
from data_const.coordinate import *


def find_highest_confidence(box):
    if len(box) == 0:
        return None  # 如果列表为空，返回 None
    return max(box, key=lambda item: item[4])


def calculate_center(box):  # 计算矩形框的底边中心点坐标
    return ((box[0] + box[2]) / 2, box[3])


def calculate_origin_center(box):
    # 计算矩形框的中心点坐标
    center_x = (box[0] + box[2]) / 2
    center_y = (box[1] + box[3]) / 2
    return (center_x, center_y)


def get_dom_xy_px(box, image):
    x, y = calculate_origin_center(box)
    return [x * image.shape[1], y * image.shape[0]]


def calculate_distance(center1, center2):  # 计算两个底边中心点之间的欧几里得距离
    return math.sqrt((center1[0] - center2[0]) ** 2 + (center1[1] - center2[1]) ** 2)


def find_closest_box(boxes, target_box):  # 计算目标框的中心点
    target_center = calculate_center(target_box)  # 初始化最小距离和最近的box
    min_distance = float("inf")
    closest_box = None  # 遍历所有box，找出最近的box
    for box in boxes:
        center = calculate_center(box)
        distance = calculate_distance(center, target_center)
        if distance < min_distance:
            min_distance = distance
            closest_box = box
    return closest_box, min_distance


def find_farthest_box(boxes, target_box):
    target_center = calculate_center(target_box)  # 计算目标框的中心点
    max_distance = -float("inf")  # 初始化最大距离和最远的box
    farthest_box = None
    for box in boxes:  # 遍历所有box，找出最远的box
        center = calculate_center(box)
        distance = calculate_distance(center, target_center)
        if distance > max_distance:
            max_distance = distance
            farthest_box = box
    return farthest_box, max_distance


def find_closest_or_second_closest_box(boxes, point):
    """找到离目标框最近的框或第二近的框"""
    if len(boxes) < 2:
        # 如果框的数量少于两个，直接返回最近的框
        target_center = point
        closest_box = None
        min_distance = float("inf")
        for box in boxes:
            center = calculate_center(box)
            distance = calculate_distance(center, target_center)
            if distance < min_distance:
                min_distance = distance
                closest_box = box
        return closest_box, distance
    # 如果框的数量不少于两个
    target_center = point
    # 初始化最小距离和最近的框
    min_distance_1 = float("inf")
    closest_box_1 = None
    # 初始化第二近的框
    min_distance_2 = float("inf")
    closest_box_2 = None
    for box in boxes:
        center = calculate_center(box)
        distance = calculate_distance(center, target_center)
        if distance < min_distance_1:
            # 更新第二近的框
            min_distance_2 = min_distance_1
            closest_box_2 = closest_box_1
            # 更新最近的框
            min_distance_1 = distance
            closest_box_1 = box
        elif distance < min_distance_2:
            # 更新第二近的框
            min_distance_2 = distance
            closest_box_2 = box
    # 返回第二近的框
    return closest_box_2, min_distance_2


def find_close_point_to_box(boxes, point):  # 找距离点最近的框
    target_center = point  # 初始化最小距离和最近的box
    min_distance = float("inf")
    closest_box = None  # 遍历所有box，找出最近的box
    for box in boxes:
        center = calculate_center(box)
        distance = calculate_distance(center, target_center)
        if distance < min_distance:
            min_distance = distance
            closest_box = box
    return closest_box, min_distance


def calculate_point_to_box_angle(point, box):  # 计算点到框的角度
    center1 = point
    center2 = calculate_center(box)
    delta_x = center2[0] - center1[0]  # 计算相对角度（以水平轴为基准）
    delta_y = center2[1] - center1[1]
    angle = math.atan2(delta_y, delta_x)
    angle_degrees = math.degrees(angle)  # 将角度转换为度数
    adjusted_angle = -angle_degrees
    return adjusted_angle


def calculate_angle(box1, box2):
    center1 = calculate_center(box1)
    center2 = calculate_center(box2)
    delta_x = center2[0] - center1[0]  # 计算相对角度（以水平轴为基准）
    delta_y = center2[1] - center1[1]
    angle = math.atan2(delta_y, delta_x)
    angle_degrees = math.degrees(angle)  # 将角度转换为度数
    adjusted_angle = -angle_degrees
    return adjusted_angle


def calculate_gate_angle(point, gate):
    center1 = point
    center2 = ((gate[0] + gate[2]) / 2, (gate[3] - gate[1]) * 0.65 + gate[1])
    delta_x = center2[0] - center1[0]  # 计算相对角度（以水平轴为基准）
    delta_y = center2[1] - center1[1]
    angle = math.atan2(delta_y, delta_x)
    angle_degrees = math.degrees(angle)  # 将角度转换为度数
    adjusted_angle = -angle_degrees
    return adjusted_angle


def calculate_angle_to_box(point1, point2):  # 计算点到点的角度
    angle = math.atan2(
        point2[1] - point1[1], point2[0] - point1[0]
    )  # 计算从点 (x, y) 到中心点的角度
    angle_degrees = math.degrees(angle)  # 将角度转换为度数
    adjusted_angle = -angle_degrees
    return adjusted_angle


def calculate_iou(box1, box2):
    # 计算相交区域的坐标
    inter_x_min = max(box1[0], box2[0])
    inter_y_min = max(box1[1], box2[1])
    inter_x_max = min(box1[2], box2[2])
    inter_y_max = min(box1[3], box2[3])
    # 计算相交区域的面积
    inter_area = max(0, inter_x_max - inter_x_min) * max(0, inter_y_max - inter_y_min)
    # 计算每个矩形的面积和并集面积
    box1_area = (box1[2] - box1[0]) * (box1[3] - box1[1])
    box2_area = (box2[2] - box2[0]) * (box2[3] - box2[1])
    union_area = box1_area + box2_area - inter_area
    # 计算并返回IoU
    return inter_area / union_area if union_area > 0 else 0


def normalize_angle(angle):  # 将角度规范化到 [-180, 180) 的范围内
    angle = angle % 360
    if angle >= 180:
        angle -= 360
    return angle


def are_angles_on_same_side_of_y(angle1, angle2):  # 规范化角度
    norm_angle1 = normalize_angle(angle1)
    norm_angle2 = normalize_angle(angle2)  # 检查是否在 y 轴的同侧
    return (norm_angle1 >= 0 and norm_angle2 >= 0) or (
        norm_angle1 < 0 and norm_angle2 < 0
    )


def get_door_coordinate_by_direction(direction):
    """
    根据方向计算下一个房间的门 lable
    :param direction:
    :return:
    """
    direction_to_direction = {
        "top": "opendoor_t",
        "down": "opendoor_d",
        "left": "opendoor_l",
        "right": "opendoor_r",
    }
    return direction_to_direction.get(direction, "")


# 判断图片是否接近黑色
def is_image_almost_black(image, threshold=30):  # 读取图片
    image = cv.cvtColor(image, cv.IMREAD_GRAYSCALE)  # 检查图片是否成功读取
    num_black_pixels = np.sum(image < threshold)
    total_pixels = image.size
    black_pixel_ratio = (
        num_black_pixels / total_pixels
    )  # 定义一个比例阈值来判断图片是否接近黑色
    return black_pixel_ratio > 0.6


def annotate_output_with_labels(output, output_dict, labels):
    filtered_output = output[output[:, 4] > 0.35, :6]
    # 遍历输出并分类
    for detection in filtered_output:
        detection_list = detection[:5].tolist()  # 提取前5个数值（检测框坐标和置信度）
        category_index = int(detection[5].item())  # 获取类别索引
        label = labels[category_index]  # 获取对应的标签名称
        output_dict[label].append(detection_list)  # 添加检测框到相应的标签下


map_info = {
    "bwj": {
        "cn_name": "布万加",
        "boss_path": [
            [0, 0],
            [0, -1],
            [1, -1],
            [2, -1],
            [2, 0],
            [1, 0],
            [2, 0],
            [3, 0],
            [4, 0],
            [5, 0],
        ],
        "boss_gate": [
            "down",
            "right",
            "right",
            "top",
            "left",
            "right",
            "right",
            "right",
            "right",
            "right",
        ],
        "full_figure_path": [
            [0, 0],
            [0, -1],
            [1, -1],
            [2, -1],
            [2, 0],
            [1, 0],
            [2, 0],
            [2, 1],
            [1, 1],
            [0, 1],
            [1, 1],
            [2, 1],
            [2, 0],
            [3, 0],
            [4, 0],
            [5, 0],
        ],
        "szt": [1, 0],
    }
}


class GameAction:
    """
    游戏控制
    """

    def __init__(self, hero_name: str, adb: ScrcpyADB, next):
        self.adb = adb
        self.next = next
        self.hero_ctrl = get_hero_control(hero_name, adb)
        self.map_path = map_info["bwj"]["boss_path"]
        self.map_gate = map_info["bwj"]["boss_gate"]
        self.room_index = 0  # 房间下标
        self.pre_state = False  # 处理过图逻辑锁
        self.special_room = False  # 狮子头
        self.boss_room = False  # boss
        self.next_room_direction = "down"  # 下一个房间的方向
        self.detect_retry = False
        self.kashi = 0
        self.thread_run = True  # 循环执行条件
        self.thread = threading.Thread(target=self.control)  # 创建线程，并指定目标函数
        self.thread.daemon = True  # 设置为守护线程（可选）
        self.thread.start()

    def control(self):
        last_room_pos = []
        hero_track = deque()
        hero_track.appendleft([0, 0])
        # 执行游戏逻辑
        while self.thread_run:
            queue = self.adb.infer_queue
            if queue.empty():
                time.sleep(0.001)
                continue
            # 获取推理结果
            image, result = queue.get()
            # 初始化字典，键为标签名称，值为空列表
            output_dict = {label: [] for label in self.adb.yolo.labels}
            # 获取分类字典
            annotate_output_with_labels(result, output_dict, self.adb.yolo.labels)
            result = output_dict
            hero = result["hero"]
            monster = result["monster"]
            # 获取当前房间下应该进入的门
            if 0 <= self.room_index < len(self.map_gate):
                self.next_room_direction = self.map_gate[self.room_index]
            gate = result[get_door_coordinate_by_direction(self.next_room_direction)]
            go = result["go"]
            item = result["item"]
            guide = result["guide"]
            card = result["card"]
            again = result["again"]
            comeback = result["comeback"]
            zeroPL = result["zeroPL"]
            repair = result["repair"]
            if is_image_almost_black(image):
                if self.pre_state == False:
                    logger.info("过图了！")
                    self.kashi = 0
                    last_room_pos = hero_track[0]
                    hero_track = deque()
                    hero_track.appendleft([1 - last_room_pos[0], 1 - last_room_pos[1]])
                    self.hero_ctrl.reset()
                    self.pre_state = True
                else:
                    continue
            if self.pre_state == True:
                # 记录房间号
                if len(hero) > 0:
                    self.room_index += 1
                    self.pre_state = False
                    logger.info(f"记录房间号: {self.room_index}")
                else:
                    continue
            # 翻盘
            if len(card) >= 8:
                logger.info("翻盘")
                self.hero_ctrl.reset()
                time.sleep(1)
                self.adb.touch([0.7 * image.shape[1], 0.25 * image.shape[0]])
                self.detect_retry = True
                time.sleep(7)
            # 计算英雄位置
            self.calculate_hero_pos(hero_track, hero)

            # 如果有怪物
            if len(monster) > 0:
                logger.info(f"有怪物")
                close_monster, distance = find_close_point_to_box(
                    monster, hero_track[0]
                )
                angle = calculate_point_to_box_angle(hero_track[0], close_monster)
                close_monster_point = calculate_center(close_monster)
                self.hero_ctrl.killMonsters(angle, self.room_index, hero_track[0], close_monster_point)
            # 如果有物品
            elif len(item) > 0:
                logger.info("有物品")
                if len(gate) > 0:
                    close_gate, distance = find_close_point_to_box(gate, hero_track[0])
                    farthest_item, distance = find_farthest_box(item, close_gate)
                    angle = calculate_point_to_box_angle(hero_track[0], farthest_item)
                else:
                    close_item, distance = find_close_point_to_box(item, hero_track[0])
                    angle = calculate_point_to_box_angle(hero_track[0], close_item)
                # self.hero_ctrl.attack(False)
                self.hero_ctrl.moveV2(angle)
            # 修理装备
            elif len(repair) > 0 and repair[0][4] > 0.8:
                logger.info("修理装备")
                self.hero_ctrl.reset()
                self.adb.touch(get_dom_xy_px(repair[0], image), 0.2)
                time.sleep(1)
                self.adb.touch(repair_confirm, 0.3)
                time.sleep(1)
                self.adb.touch([0,0])
            # 发现引导位 并且还没到过狮子头房间 则当前房间为狮子头的前一个房间
            elif len(guide) > 0 and guide[0][4] > 0.8 and self.room_index < 4:
                logger.info("发现引导位 并且还没到过狮子头房间")
                self.room_index = 4
                continue
            # 狮子头前一个房间先找引导位
            elif len(guide) > 0 and self.room_index == 4 and len(gate) < 1:
                logger.info("找引导位")
                close_guide, distance = find_closest_or_second_closest_box(
                    guide, hero_track[0]
                )
                angle = calculate_point_to_box_angle(hero_track[0], close_guide)
                # time.sleep(0.1)
                self.hero_ctrl.moveV2(angle, 0.2)
            # 如果有门
            elif len(gate) > 0:
                logger.info(f"记录门: {self.next_room_direction}")
                if len(guide) > 0 and self.room_index == 4:
                    continue
                # if(self.room_index == 4):
                #     self.hero_ctrl.move(300, 0.3)
                #     time.sleep(1)
                #     self.hero_ctrl.move(180, 1.5)
                #     continue
                if self.next_room_direction == "left":  # 左门
                    close_gate, distance = find_close_point_to_box(gate, hero_track[0])
                    angle = calculate_gate_angle(hero_track[0], close_gate)
                    # 如果在执行普通攻击 则结束普通攻击
                    # self.ctrl.attack(False)
                else:
                    close_gate, distance = find_close_point_to_box(gate, hero_track[0])
                    angle = calculate_point_to_box_angle(hero_track[0], close_gate)
                    # self.ctrl.attack(False)
                self.hero_ctrl.moveV2(angle)
            # 如果有箭头
            elif (len(go) > 0 and self.room_index != 4) or (
                len(go) > 0 and self.kashi > 300
            ):
                logger.info("有箭头")
                close_arrow, distance = find_closest_or_second_closest_box(
                    go, hero_track[0]
                )
                angle = calculate_point_to_box_angle(hero_track[0], close_arrow)
                self.hero_ctrl.moveV2(angle)
            # pl已刷完 返回城镇
            elif len(comeback) > 0 and len(zeroPL) > 0 and zeroPL[0][4] > 0.9:
              logger.info("pl已刷完 返回城镇")
              self.thread_run = False
              self.adb.touch(get_dom_xy_px(find_highest_confidence(comeback), image), 0.2)
              time.sleep(10)
              self.next()
            # 重新挑战
            elif self.detect_retry == True:
                logger.info("重新挑战")
                if len(item) > 0 or len(again) < 1:
                    continue
                else:
                    self.hero_ctrl.reset()
                    time.sleep(1)
                    # 重新挑战
                    self.adb.touch(
                        get_dom_xy_px(find_highest_confidence(again), image), 0.2
                    )
                    time.sleep(0.5)
                    self.adb.touch(again_start_confirm, 0.2)
                    time.sleep(3)
                    self.hero_ctrl.useSkills = {}
                    self.next_room_direction = "down"
                    self.detect_retry = False
                    self.room_index = 0
                    hero_track = deque()
                    hero_track.appendleft([0, 0])
            # 无目标
            else:
                logger.info("无目标")
                self.kashi += 1
                if self.kashi % 50 == 0:
                    if self.room_index == 4:
                        angle = calculate_angle_to_box(hero_track[0], [0.25, 0.6])
                    else:
                        angle = calculate_angle_to_box(hero_track[0], [0.5, 0.75])
                    self.hero_ctrl.moveV2(0)
                    self.hero_ctrl.moveV2(angle, 0.2)

    def random_move(self):
        """
        防卡死
        :return:
        """
        logger.info("随机移动一下")
        self.hero_ctrl.moveV2(random.randint(0, 360))

    def calculate_hero_pos(self, hero_track: deque, result):
        if len(result) == 0:
            None
        elif len(result) == 1:
            hero_track.appendleft(calculate_center(result[0]))
        elif len(result) > 1:
            for box in result:
                if calculate_distance(box, hero_track[0]) < 0.1:
                    hero_track.appendleft(box)
                    return
                hero_track.appendleft(hero_track[0])


if __name__ == "__main__":
    adb = ScrcpyADB()
    action = GameAction("hong_yan", adb)
