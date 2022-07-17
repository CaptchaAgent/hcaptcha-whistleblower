# -*- coding: utf-8 -*-
# Time       : 2022/7/17 4:17
# Author     : QIN2DIM
# Github     : https://github.com/QIN2DIM
# Description:
from typing import Optional

from services.deploy import SentinelScheduler
from services.settings import logger
from services.utils import ToolBox


@logger.catch()
def run(
    deploy: Optional[bool] = False,
    silence: Optional[bool] = True,
    lang: Optional[str] = "en",
    debug: Optional[bool] = None,
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

    sentinel = SentinelScheduler(silence=silence, lang=lang, debug=debug)
    if not deploy:
        return sentinel.tango()
    return sentinel.deploy_on_vps()
