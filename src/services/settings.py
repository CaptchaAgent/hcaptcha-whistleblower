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

for _pending in [PROJECT_DATABASE, DIR_MODEL, DIR_TEMP_CACHE, DIR_CHALLENGE, DIR_LOG]:
    os.makedirs(_pending, exist_ok=True)

TOP_LEVEL_SITEKEY = [
    "f5561ba9-8f1e-40ca-9b5b-a0b3f719ef34",  # discord
    "91e4137f-95af-4bc9-97af-cdcedce21c8c",  # epic
    "adafb813-8b5c-473f-9de3-485b4ad5aa09",  # top level
    "ace50dd0-0d68-44ff-931a-63b670c7eed7",  # top level
    "edc4ce89-8903-4906-80b1-7440ad9a69c8",  # cloud horse
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

    # 采集器中的默认聚焦挑战，不在聚焦表中的挑战将被跳过
    FOCUS_LABELS = {
        # "lion yawning with open mouth": "lion_yawning_with_open_mouth",
        # "lion with closed eyes": "lion_with_closed_eyes",
        # "horse with white legs": "horse_with_white_legs",
        # "parrot bird with eyes open": "parrot_bird_with_eyes_open",
        # "elephant with long tusk": "elephant_with_long_tusk",
        "horse made of clouds": "horse_made_of_clouds"
    }

    # 采集器默认的 rainbow key，用于合成彩虹表
    # focus labels 会被自动填充到 rainbow key
    PENDING_LABELS = [
        "domestic_cat",
        "vertical_river",
        "airplane_in_the_sky_flying_left",
        "airplanes_in_the_sky_that_are_flying_to_the_right",
        "elephants_drawn_with_leaves",
        "seaplane",
        "airplane",
        "bicycle",
        "train",
        "bedroom",
        "lion",
        "bridge",
        "living_room",
        "horse",
        "conference_room",
        "smiling_dog",
        "dog",
        "horse_made_of_clouds",
    ]
