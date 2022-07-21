# -*- coding: utf-8 -*-
# Time       : 2022/7/15 21:00
# Author     : QIN2DIM
# Github     : https://github.com/QIN2DIM
# Description:
from typing import Optional

from services.deploy import ChallengeCollector
from services.deploy import ChallengeScheduler
from services.settings import DIR_RAINBOW_BACKUP, PATH_RAINBOW_YAML, logger, CollectorSettings
from services.utils import get_challenge_ctx, ToolBox


def _interactive_console(sitekey=None, silence=None, debug=None, merge=None):
    """

    :type sitekey: str
    :type silence: bool
    :type debug: bool
    :type merge: bool
    :return:
    """
    debug = True if debug is None else debug
    cc = ChallengeCollector(
        dir_rainbow_backup=DIR_RAINBOW_BACKUP,
        focus_labels=CollectorSettings.FOCUS_LABELS,
        pending_labels=CollectorSettings.PENDING_LABELS,
        sitekey=sitekey,
        silence=silence,
        debug=debug,
    )
    # 合并彩虹表
    if merge:
        return cc.update(PATH_RAINBOW_YAML)
    # 采集数据集 | 自动解包数据集
    with get_challenge_ctx(silence=silence, lang="en") as ctx:
        return cc.claim(ctx, retry_times=2000)


def startup(
    deploy: Optional[bool] = None,
    silence: Optional[bool] = None,
    lang: Optional[str] = None,
    debug: Optional[bool] = None,
    site_key: Optional[str] = None,
    merge: Optional[bool] = None,
):
    """根据label定向采集数据集"""
    logger.info(
        ToolBox.runtime_report(
            motive="SETUP", action_name="ScaffoldRainbow", silence=silence, debug=debug, lang=lang
        )
    )
    scheduler = ChallengeScheduler(silence=silence, lang=lang, debug=debug)
    if not deploy:
        return _interactive_console(silence=silence, debug=debug, sitekey=site_key, merge=merge)
    return scheduler.deploy_on_vps(scheduler.waltz, "collector")
