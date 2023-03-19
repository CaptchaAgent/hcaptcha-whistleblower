# -*- coding: utf-8 -*-
# Time       : 2022/7/15 21:00
# Author     : QIN2DIM
# Github     : https://github.com/QIN2DIM
# Description:
from typing import Optional

from services.deploy import ChallengeCollector
from services.deploy import ChallengeScheduler
from services.guarder import CollectorT
from services.settings import (
    DIR_RAINBOW_BACKUP,
    PATH_RAINBOW_YAML,
    logger,
    CollectorSettings,
    DIR_CANVAS_BACKUP,
)
from services.utils import get_challenge_ctx, ToolBox


@logger.catch()
def _interactive_console(
    sitekey=None, silence=None, debug=None, merge=None, unpack=None, on_outdated=None
):
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
    # 解压数据集
    if unpack:
        return cc.unpack()
    # 采集数据集 | 自动解包数据集
    ctx = get_challenge_ctx(silence=silence, lang="en")
    try:
        cc.claim(ctx, retries=CollectorSettings.GETTER_RETRIES, on_outdated=on_outdated)
    finally:
        ctx.quit()


def startup(
    deploy: Optional[bool] = None,
    silence: Optional[bool] = None,
    lang: Optional[str] = None,
    debug: Optional[bool] = None,
    site_key: Optional[str] = None,
    merge: Optional[bool] = None,
    unpack: Optional[bool] = None,
    upto: Optional[int] = None,
):
    """根据label定向采集数据集"""
    logger.info(
        ToolBox.runtime_report(
            motive="SETUP", action_name="ScaffoldRainbow", silence=silence, debug=debug, lang=lang
        )
    )
    scheduler = ChallengeScheduler(silence=silence, lang=lang, debug=debug)
    if not deploy:
        return _interactive_console(
            silence=silence,
            debug=debug,
            sitekey=site_key,
            merge=merge,
            unpack=unpack,
            on_outdated=upto,
        )
    return scheduler.deploy_on_vps(scheduler.waltz, "collector")


def canvas_mining(
    silence: Optional[bool] = None,
    debug: Optional[bool] = None,
    site_key: Optional[str] = None,
    retry_times: int = 5,
):
    logger.warning(
        ToolBox.runtime_report(
            motive="SETUP[dev]",
            action_name="ScaffoldCanvas",
            silence=silence,
            debug=debug,
            retry=retry_times,
        )
    )

    ct = CollectorT(dir_canvas_backup=DIR_CANVAS_BACKUP, sitekey=site_key, silence=silence)
    with get_challenge_ctx(silence=False, lang="en") as ctx:
        ct.claim(ctx, retries=retry_times)
