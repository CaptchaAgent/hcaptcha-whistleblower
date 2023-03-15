# -*- coding: utf-8 -*-
# Time       : 2022/7/17 4:17
# Author     : QIN2DIM
# Github     : https://github.com/QIN2DIM
# Description:
from typing import Optional

from services.deploy import ChallengeScheduler
from services.settings import logger, CollectorSettings
from services.utils import ToolBox


@logger.catch()
def run(
    deploy: Optional[bool] = False,
    silence: Optional[bool] = True,
    lang: Optional[str] = "en",
    debug: Optional[bool] = None,
    host: Optional[str] = None,
    sitekey: Optional[str] = None,
    timer: Optional[int] = 300,
):
    logger.info(
        ToolBox.runtime_report(
            motive="SETUP",
            action_name="ScaffoldSentinel",
            deploy=bool(deploy),
            silence=silence,
            lang=lang,
        )
    )
    CollectorSettings.HOST = host or CollectorSettings.HOST
    scheduler = ChallengeScheduler(silence=silence, lang=lang, debug=debug)
    if not deploy:
        return scheduler.tango(sitekey=sitekey, timer=timer)
    return scheduler.deploy_on_vps(scheduler.tango, "sentinel")
