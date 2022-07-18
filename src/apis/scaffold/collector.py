# -*- coding: utf-8 -*-
# Time       : 2022/7/15 21:00
# Author     : QIN2DIM
# Github     : https://github.com/QIN2DIM
# Description:
import random
from typing import Optional

from services.deploy import ChallengeCollector
from services.deploy import ChallengeScheduler
from services.settings import (
    DIR_RAINBOW_BACKUP,
    PATH_RAINBOW_YAML,
    logger,
    CollectorSettings,
    TOP_LEVEL_SITEKEY,
)
from services.utils import get_challenge_ctx, ToolBox


def _interactive_console(silence: Optional[bool] = None, debug: Optional[bool] = None):
    debug = True if debug is None else debug
    cc = ChallengeCollector(
        dir_rainbow_backup=DIR_RAINBOW_BACKUP,
        focus_labels=CollectorSettings.FOCUS_LABELS,
        pending_labels=CollectorSettings.PENDING_LABELS,
        sitekey=random.choice(TOP_LEVEL_SITEKEY),
        silence=silence,
        debug=debug,
    )
    while i := input(">> [1]采集; [2]解包; [3]更新 - ").strip():
        if i == "1":
            with get_challenge_ctx(silence=silence, lang="en") as ctx:
                cc.claim(ctx, retry_times=20)
        if i == "2":
            return cc.unpack()
        if i == "3":
            return cc.update(PATH_RAINBOW_YAML)


def startup(
    deploy: Optional[bool] = None,
    silence: Optional[bool] = None,
    lang: Optional[str] = None,
    debug: Optional[bool] = None,
):
    """根据label定向采集数据集"""
    logger.info(
        ToolBox.runtime_report(
            motive="SETUP", action_name="ScaffoldRainbow", silence=silence, debug=debug, lang=lang
        )
    )
    scheduler = ChallengeScheduler(silence=silence, lang=lang, debug=debug)
    if not deploy:
        return _interactive_console(silence=silence, debug=debug)
    return scheduler.deploy_on_vps(scheduler.waltz, "collector")
