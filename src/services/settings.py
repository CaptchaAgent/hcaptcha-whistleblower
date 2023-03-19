# -*- coding: utf-8 -*-
# Time       : 2022/7/15 20:48
# Author     : QIN2DIM
# Github     : https://github.com/QIN2DIM
# Description:
import os
from os.path import join, dirname

from services.utils import ToolBox

# ---------------------------------------------------
# [√]Lock the project directory
# ---------------------------------------------------
# Source root directory
PROJECT_ROOT = dirname(dirname(__file__))

# File database directory
PROJECT_DATABASE = join(PROJECT_ROOT, "database")

# The storage directory of the YOLO object detection model
DIR_MODEL = join(PROJECT_ROOT, "model")

PATH_RAINBOW_YAML = join(PROJECT_DATABASE, "rainbow.yaml")
PATH_PROMPT = join(PROJECT_DATABASE, "prompt.yaml")

DIR_RAINBOW_BACKUP = join(PROJECT_DATABASE, "rainbow_backup")
DIR_CANVAS_BACKUP = join(PROJECT_DATABASE, "canvas_backup")

# Run cache directory
DIR_TEMP_CACHE = join(PROJECT_DATABASE, "temp_cache")

# Directory for challenge images
DIR_CHALLENGE = join(DIR_TEMP_CACHE, "_challenge")

# Service log directory
DIR_LOG = join(PROJECT_DATABASE, "logs")
# ---------------------------------------------------
# [√]Server log configuration
# ---------------------------------------------------
logger = ToolBox.init_log(error=join(DIR_LOG, "error.log"), runtime=join(DIR_LOG, "runtime.log"))

# ---------------------------------------------------
# [√]Path completion
# ---------------------------------------------------

for _pending in [
    PROJECT_DATABASE,
    DIR_MODEL,
    DIR_TEMP_CACHE,
    DIR_CHALLENGE,
    DIR_LOG,
    DIR_CANVAS_BACKUP,
    DIR_RAINBOW_BACKUP,
]:
    os.makedirs(_pending, exist_ok=True)

TOP_LEVEL_SITEKEY = [
    "f5561ba9-8f1e-40ca-9b5b-a0b3f719ef34",  # discord
    "91e4137f-95af-4bc9-97af-cdcedce21c8c",  # epic
    "adafb813-8b5c-473f-9de3-485b4ad5aa09",  # top level
    "ace50dd0-0d68-44ff-931a-63b670c7eed7",  # new-type challenge
    "edc4ce89-8903-4906-80b1-7440ad9a69c8",  # cloud horse
    "c86d730b-300a-444c-a8c5-5312e7a93628",  # user
    "a5f74b19-9e45-40e0-b45d-47ff91b7a6c2",  # hcaptcha
    "13257c82-e129-4f09-a733-2a7cb3102832",  # hcaptcha-signup
]

config_ = ToolBox.check_sample_yaml(
    path_output=join(dirname(dirname(__file__)), "config.yaml"),
    path_sample=join(dirname(dirname(__file__)), "config-sample.yaml"),
)


class LogLevel:
    EXCEPTION = 2**0
    DEBUG = 2**1
    INFO = 2**2
    SUCCESS = 2**3
    WARNING = 2**4
    ERROR = 2**5
    CRITICAL = 2**6


class LarkSettings:
    APP_ID = config_.get("APP_ID", "")
    APP_SECRET = config_.get("APP_SECRET", "")
    WEBHOOK_UUID = config_.get("WEBHOOK_UUID", "")
    CHAT_ID = config_.get("CHAT_ID", "")


class SentinelSettings:
    s = config_.get("sentinel", {})
    INTERVAL_SECONDS = s.get("interval_seconds", 60 * 8)


class CollectorSettings:
    s = config_.get("collector", {})
    INTERVAL_SECONDS = s.get("interval_seconds", 60 * 10)
    GETTER_RETRIES = 500
    ON_OUTDATED = None

    HOST = "127.0.0.1:10819"
    TOKEN = "39015381-c7cd-485e-8f13-3c2a2cecab80"
    API_CREATE_TASK = "/v1/createTask"
    API_CHECK_TASKS = "/v1/checkTasks"
    API_DOWNLOAD = "/v1/download"

    # 采集器默认的 rainbow key，用于合成彩虹表
    # focus labels 会被自动填充到 rainbow key
    PENDING_LABELS = [
        "vertical_river",
        "elephants_drawn_with_leaves",
        "giraffe",
        "bridge",
        # -- AlphaTraffic --
        "airplane_in_the_sky_flying_left",
        "airplanes_in_the_sky_that_are_flying_to_the_right",
        "seaplane",
        "airplane",
        "bicycle",
        "train",
        # -- AlphaRoom --
        "bedroom",
        "living_room",
        "conference_room",
        # -- AlphaBird --
        "parrot",
        # -- AlphaLion --
        "lion",
        "lion_with_mane_on_its_neck",
        "lion_with_a_closed_mouth",  # adafb813-8b5c-473f-9de3-485b4ad5aa09 一只闭着嘴的狮子
        "lion_with_an_open_mouth",  # c86d730b-300a-444c-a8c5-5312e7a93628 张开嘴的狮子
        "lion_with_open_eyes",
        "female_lion",  # c86d730b-300a-444c-a8c5-5312e7a93628 雌狮
        # -- AlphaHorse --
        "horse_with_white_legs",  # c86d730b-300a-444c-a8c5-5312e7a93628 白腿马
        "horse_facing_to_the_left",  # edc4ce89-8903-4906-80b1-7440ad9a69c8 朝左马
        "horse_facing_to_the_right",  # c86d730b-300a-444c-a8c5-5312e7a93628 面向右侧的马
        "horse_walking_or_running",  # adafb813-8b5c-473f-9de3-485b4ad5aa09 马在行走或奔跑
        "horse_made_of_clouds",
        "horse",
        # -- AlphaCat --
        "domestic_cat",  # 家猫
        "kitten",  # f5561ba9-8f1e-40ca-9b5b-a0b3f719ef34 小猫
        "baby_cat",  # adafb813-8b5c-473f-9de3-485b4ad5aa09 一只小猫
        "adult_cat",  # adafb813-8b5c-473f-9de3-485b4ad5aa09 成年猫
        "cat_with_long_hair",  # 91e4137f-95af-4bc9-97af-cdcedce21c8c 长毛猫
        "cat_with_short_hair",  # 91e4137f-95af-4bc9-97af-cdcedce21c8c 短毛猫
        "cat_with_thick_fur",  # adafb813-8b5c-473f-9de3-485b4ad5aa09 厚毛猫
        "cat_with_large_rounded_head",
        # -- AlphaDog --
        "dog_with_a_collar_on_its_neck",  # adafb813-8b5c-473f-9de3-485b4ad5aa09 一条脖子上有项圈的狗
        "dog",
        # -- Animal[20220921]Theme --
        # porcelain_teacup  | adafb813-8b5c-473f-9de3-485b4ad5aa09
        # teacup with similar porcelain design pattern 请点击每张包含类似瓷器设计图案的茶杯的图片
        "porcelain_teacup",
        "whole_glass_bottle",  # edc4ce89-8903-4906-80b1-7440ad9a69c8 整个玻璃瓶
        "broken_glass_bottle",  # adafb813-8b5c-473f-9de3-485b4ad5aa09 破碎玻璃瓶
        # -- Animal[20220921]Theme --
        "dog_shaped_cookie"  # edc4ce89-8903-4906-80b1-7440ad9a69c8 狗形饼干
        "cat_shaped_cookie",  # edc4ce89-8903-4906-80b1-7440ad9a69c8 猫形饼干
        # -- Animal[20220921]Theme --
        "fish_underwater",  # adafb813-8b5c-473f-9de3-485b4ad5aa09 水下鱼
        "fish_jumping_over_the_water",  # edc4ce89-8903-4906-80b1-7440ad9a69c8 鱼跃过水面
        "bird_flying",  # adafb813-8b5c-473f-9de3-485b4ad5aa09 一只飞翔的鸟
        "bird_on_a_branch",  # adafb813-8b5c-473f-9de3-485b4ad5aa09 树枝上的鸟
        # -- Animal[20220921]Theme --
        "flower_in_a_vase",  # ace50dd0-0d68-44ff-931a-63b670c7eed7 花瓶中的花
        "plant_hanging_from_the_ceiling",  # adafb813-8b5c-473f-9de3-485b4ad5aa09 悬挂在天花板上的植物
        "plant_on_the_table",  # adafb813-8b5c-473f-9de3-485b4ad5aa09 植物
        "dead_and_dried_plant_in_the_pot",  # edc4ce89-8903-4906-80b1-7440ad9a69c8 花盆中枯死和干燥植物
        # -- Animal[20220921]Theme --
        "toy_rabbit",  # edc4ce89-8903-4906-80b1-7440ad9a69c8 玩具兔子
        "rabbit_in_the_grass",  # edc4ce89-8903-4906-80b1-7440ad9a69c8 兔子(草丛中的兔子)
        "turtle",  # c86d730b-300a-444c-a8c5-5312e7a93628 海龟
        "rabbit_in_the_grass",  # edc4ce89-8903-4906-80b1-7440ad9a69c8 兔子
        "turtle_under_the_water",  # edc4ce89-8903-4906-80b1-7440ad9a69c8 水下乌龟
        "toy_turtle",  # a5f74b19-9e45-40e0-b45d-47ff91b7a6c2 玩具乌龟
        "toy_house",  # a5f74b19-9e45-40e0-b45d-47ff91b7a6c2 玩具屋
        "duck",  # ace50dd0-0d68-44ff-931a-63b670c7eed7 鸭子
        "house_covered_in_snow",  # edc4ce89-8903-4906-80b1-7440ad9a69c8 被雪覆盖的房子
        "rabbit_swimming_in_water",  # edc4ce89-8903-4906-80b1-7440ad9a69c8 兔子在水中游泳
        "duck_in_the_water",  # c86d730b-300a-444c-a8c5-5312e7a93628 水中鸭子
        "house",  # f5561ba9-8f1e-40ca-9b5b-a0b3f719ef34 房子
        "cactus",  # ace50dd0-0d68-44ff-931a-63b670c7eed7 仙人掌
        "house_in_the_beach",  # 91e4137f-95af-4bc9-97af-cdcedce21c8c
        "penguin",  # 企鹅
        "penguin_behind_rocks",  # 岩石后面的企鹅
        "penguin_surrounded_by_flowers",  # 91e4137f-95af-4bc9-97af-cdcedce21c8c 被鲜花包围的企鹅
        "penguin_on_ice",  # ace50dd0-0d68-44ff-931a-63b670c7eed7 冰上企鹅
        "cactus_in_the_sand",  # 沙中仙人掌
        "cactus_in_a_pot",  # f5561ba9-8f1e-40ca-9b5b-a0b3f719ef34 盆中仙人掌
        "bee_flying_near_a_flower"  # a5f74b19-9e45-40e0-b45d-47ff91b7a6c2 蜜蜂在花朵附近飞翔
        "hat",  # item that a person normally wears on their head
        "shoes",  # item that a person normally wears on their feet
        "belt",  # item that a person normally wears on their pants
        "dangerous_sea",  # 危险海域
        "calm_sea",
        "hot_food",
        "cold_drink",
        "glass_with_ice",
        # https://accounts.hcaptcha.com/demo?sitekey=ace50dd0-0d68-44ff-931a-63b670c7eed7
        "cup_of_coffee",
        # https://accounts.hcaptcha.com/demo?sitekey=adafb813-8b5c-473f-9de3-485b4ad5aa09
        "shark",
        # https://accounts.hcaptcha.com/demo?sitekey=edc4ce89-8903-4906-80b1-7440ad9a69c8
        "octopus",
        # https://accounts.hcaptcha.com/demo?sitekey=c86d730b-300a-444c-a8c5-5312e7a93628
        "strawberry_cake",
        # https://accounts.hcaptcha.com/demo?sitekey=91e4137f-95af-4bc9-97af-cdcedce21c8c
        "carved_pumpkin_with_a_face",  # 带有面部的雕刻南瓜
        "bowl_of_pasta",  # 一碗意大利面
        # https://accounts.hcaptcha.com/demo?sitekey=adafb813-8b5c-473f-9de3-485b4ad5aa09
        "starfish",
        # https://accounts.hcaptcha.com/demo?sitekey=c86d730b-300a-444c-a8c5-5312e7a93628
        "jellyfish",
        "cupcake",  # 纸杯蛋糕
        # https://accounts.hcaptcha.com/demo?sitekey=edc4ce89-8903-4906-80b1-7440ad9a69c8
        "skeleton_ridding_a_bicycle",
        "drawing_of_a_haunted_house",
        "ghost_riding_a_bicycle",
        # https://accounts.hcaptcha.com/demo?sitekey=f5561ba9-8f1e-40ca-9b5b-a0b3f719ef34
        "orange_fruit",
        # "rabbit": "rabbit_blur", # rabbit
        "strawberry_cake",
        # "horse": "horse_mask",
        # "lion": "lion_mask",
        "lemons_in_a_basket",
        "oranges_in_a_basket",
        # https://accounts.hcaptcha.com/demo?sitekey=c86d730b-300a-444c-a8c5-5312e7a93628
        "flying_bat",
        # https://accounts.hcaptcha.com/demo?sitekey=91e4137f-95af-4bc9-97af-cdcedce21c8c
        "black_cat_in_a_forest",
        # https://accounts.hcaptcha.com/demo?sitekey=ace50dd0-0d68-44ff-931a-63b670c7eed7
        "chocolate_cake",
        "lemon",
        "duck_behind_rocks",
        "pancake",
        "icecream",
        "ant",
        "hot_air_balloon",  # 热气球
        "helicopter",  # 直升机
        "dragonfly",
        # "ladybug": "ladybug",
        "cake",
        # https://accounts.hcaptcha.com/demo?sitekey=edc4ce89-8903-4906-80b1-7440ad9a69c8
        "chicken_on_the_beach",
        # https://accounts.hcaptcha.com/demo?sitekey=91e4137f-95af-4bc9-97af-cdcedce21c8c
        "chicken_on_a_tree",
        # https://accounts.hcaptcha.com/demo?sitekey=adafb813-8b5c-473f-9de3-485b4ad5aa09
        "squirrel_on_a_tree",
        "hedgehog_in_a_bowl",
    ]

    # 采集器中的默认聚焦挑战，不在聚焦表中的挑战将被跳过
    FOCUS_LABELS = {
        # "elephant with long tusk": "elephant_with_long_tusk",
        # "dog with closed eyes": "dog_with_closed_eyes",
        # "dog without a collar": "dog_without_a_collar",
        # "smiling dog": "smiling_dog",  # 微笑狗
        # --------------------------------------------------------------------------------------------------------
        # "rabbit on a beach": "rabbit_on_a_beach",
        # "hedgehog on sand": "hedgehog_on_sand",
        # https://accounts.hcaptcha.com/demo?sitekey=adafb813-8b5c-473f-9de3-485b4ad5aa09
        # "crab": "crab",
        # https://accounts.hcaptcha.com/demo?sitekey=c86d730b-300a-444c-a8c5-5312e7a93628
        # "toy penguin": "toy_penguin",
        # "squirrel": "squirrel",
        # "banana in a basket": "banana_in_a_basket",  # a5f74b19-9e45-40e0-b45d-47ff91b7a6c2
        # "hedgehog surrounded by flowers": "hedgehog_surrounded_by_flowers",
        # "squirrel surrounded by flowers": "squirrel_surrounded_by_flowers"  # adafb813-8b5c-473f-9de3-485b4ad5aa09
        # --------------------------------------------------------------------------------------------------------
        # NEW ORDER
        # https://accounts.hcaptcha.com/demo?sitekey=c86d730b-300a-444c-a8c5-5312e7a93628
        # "butterfly": "butterfly",  # 蝴蝶
        # "apple on a tree": "apple_on_a_tree",  # 树上苹果
        # "strawberry in a basket": "strawberry_in_a_basket",  # 篮子里的草莓
        # https://accounts.hcaptcha.com/demo?sitekey=91e4137f-95af-4bc9-97af-cdcedce21c8c
        # "daisy": "daisy",  # 雏菊
        # "hedgehog in water": "hedgehog_in_water",  # 水中刺猬
        # "pineapple": "pineapple",  # 菠萝
        # "dolphin": "dolphin", # 海豚
        # "panda": "panda", # 熊猫
        # "tulip": "tulip", # 郁金香
        # "hedgehog on rocks": "hedgehog_on_rocks",
        # https://accounts.hcaptcha.com/demo?sitekey=edc4ce89-8903-4906-80b1-7440ad9a69c8
        # "rose": "rose",  # 玫瑰
        # "sea otter": "sea_otter",  # 海獭
        # "ladybug": "ladybug",
        # "sunflower": "sunflower",
        # "rough sea": "rough_sea",
        # "panda in a living room": "panda_in_a_living_room",
        # https://accounts.hcaptcha.com/demo?sitekey=91e4137f-95af-4bc9-97af-cdcedce21c8c
        # "tall building": "tall_building",  # 高层建筑
        # "residential house": "residential_house",  # 住宅
        # NEW parrot
        # "piano": "piano",
        # f5561ba9-8f1e-40ca-9b5b-a0b3f719ef34
        # "cymbal": "cymbal",  # 请点击每张包含铙钹的图片
        # "lease click each image containing red roses in a garden": "red_roses_in_a_garden",
        # "red roses in a garden": "red_roses_in_a_garden",  # 花园中红玫瑰
        # << 2023-02-02 >>
        # "lease click each image containing sunflowers in a field": "sunflowers_in_a_field",  # 田野中包含向日葵
        # "sunflowers in a field": "sunflowers_in_a_field",  # 田野中包含向日葵
        # "desert": "desert",  # 沙漠
        # "mountain": "mountain",
        # "forest": "forest",
        # "daisy in a pot": "daisy_in_a_pot",  # 盆中雏菊
        # "panda in a garden": "panda_in_a_garden",  # 花园中熊猫
        # "panda in a forest": "panda_in_a_forest",  # 森林中熊猫，
        # "burning fire spot like in the examples": "burning_fire_spot",
        # edc4ce89-8903-4906-80b1-7440ad9a69c8
        # "violin": "violin",  # 小提琴
        # "beach": "beach",  # 海滩
        # "trumpet": "trumpet",  # 小号
        # "guitar": "guitar",  # 吉他
        # << 2023-03-19 >> c86d730b-300a-444c-a8c5-5312e7a93628
        "sunny sky": "sunny_sky",  # 晴空
        "steering wheel": "steering_wheel",  # 方向盘
        "someone playing golf": "someone_playing_golf",  # 打高尔夫球
        "someone playing hockey": "someone_playing_hockey",  # 有人打曲棍球
    }
