# -*- coding: utf-8 -*-
# Time       : 2022/7/17 4:17
# Author     : QIN2DIM
# Github     : https://github.com/QIN2DIM
# Description:
from __future__ import annotations

import time
from typing import Optional

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from loguru import logger

from apis._runtime import Sentinel


def tango(sitekey: str | None = None, timer: int = 300):
    with Sentinel(sitekey=sitekey) as sentinel:
        logger.info("build sentinel", at=sentinel.monitor_site)
        sentinel.tango(sentinel.ctx_session, timer=timer)


def deploy_sentinel():
    scheduler = BackgroundScheduler()
    job_name = "sentinel"
    logger.info("deploy scheduler", job_name=job_name, interval_seconds=600)

    # [⚔] Deploying Sentinel-Monitored Scheduled Tasks
    scheduler.add_job(
        func=tango,
        trigger=IntervalTrigger(seconds=600, timezone="Asia/Shanghai", jitter=5),
        name=job_name,
    )

    # [⚔] Gracefully run scheduler.
    scheduler.start()
    try:
        while True:
            time.sleep(3600)
    except (KeyboardInterrupt, EOFError):
        scheduler.shutdown(wait=False)
        logger.debug("Received keyboard interrupt signal.")


@logger.catch
def run(
    deploy: Optional[bool] = False,
    silence: Optional[bool] = True,
    lang: Optional[str] = "en",
    sitekey: Optional[str] = None,
    timer: Optional[int] = 300,
):
    logger.info("ScaffoldSentinel", silence=silence, lang=lang, deploy=bool(deploy))
    if not deploy:
        tango(sitekey=sitekey, timer=timer)
    else:
        deploy_sentinel()
