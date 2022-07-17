# -*- coding: utf-8 -*-
# Time       : 2022/7/15 21:00
# Author     : QIN2DIM
# Github     : https://github.com/QIN2DIM
# Description:
from typing import Optional

from services.guarder import RainbowClaimer
from services.settings import DIR_RAINBOW_BACKUP, PATH_RAINBOW_YAML, logger
from services.utils import get_challenge_ctx, ToolBox

FOCUS_LABELS: dict = {}


def _rainbow_console(silence: Optional[bool] = None):
    rc = RainbowClaimer(dir_rainbow_backup=DIR_RAINBOW_BACKUP, focus_labels=FOCUS_LABELS)
    while i := input(">> [1]采集; [2]解包; [3]更新 - ").strip():
        if i == "1":
            with get_challenge_ctx(silence=silence, lang="en") as ctx:
                return rc.claim(ctx, retry_times=20)
        if i == "2":
            return rc.unpack()
        if i == "3":
            return rc.update(PATH_RAINBOW_YAML)


def rainbow_generator(console: Optional[bool] = None, silence: Optional[bool] = None):
    """根据label定向采集数据集"""
    logger.info(
        ToolBox.runtime_report(
            motive="SETUP", action_name="ScaffoldRainbow", console=console, silence=silence
        )
    )
    if console is True:
        return _rainbow_console(silence)
