# -*- coding: utf-8 -*-
# Time       : 2022/7/15 20:49
# Author     : QIN2DIM
# Github     : https://github.com/QIN2DIM
# Description:
import os.path
import random
import time
from datetime import timedelta, datetime
from typing import Optional, Union, Tuple

import pytz
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger

from services.guarder import Guarder
from services.guarder import RainbowClaimer
from services.larker import LarkAlert
from services.settings import (
    LarkSettings,
    logger,
    DIR_CHALLENGE,
    DIR_RAINBOW_BACKUP,
    SentinelSettings,
    CollectorSettings,
    TOP_LEVEL_SITEKEY,
)
from services.utils import ToolBox


class ChallengeScheduler:
    def __init__(
        self,
        silence: Optional[bool] = True,
        lang: Optional[str] = "en",
        debug: Optional[bool] = False,
    ):
        self.silence = silence
        self.lang = lang
        self.debug = debug

        self.action_name = "SentinelScheduler"
        self.end_date = datetime.now(pytz.timezone("Asia/Shanghai")) + timedelta(days=360)

        # 服务注册
        self.scheduler = BackgroundScheduler()
        self.services_settings = {self.tango: SentinelSettings, self.waltz: CollectorSettings}

    def deploy_on_vps(self, self_func, job_name: str):
        settings_ = self.services_settings[self_func]
        interval_seconds = settings_.INTERVAL_SECONDS

        logger.info(
            ToolBox.runtime_report(
                motive="JOB",
                action_name=self.action_name,
                job_name=job_name,
                message="deployment task scheduler",
                interval_seconds=interval_seconds,
            )
        )

        # [⚔] Deploying Sentinel-Monitored Scheduled Tasks
        self.scheduler.add_job(
            func=self_func,
            trigger=IntervalTrigger(seconds=interval_seconds, timezone="Asia/Shanghai", jitter=5),
            name=job_name,
        )

        # [⚔] Gracefully run scheduler.
        try:
            self.scheduler.start()
            while True:
                time.sleep(3600)
        except (KeyboardInterrupt, EOFError):
            self.scheduler.shutdown()
            logger.debug(
                ToolBox.runtime_report(
                    motive="EXITS",
                    action_name=self.action_name,
                    message="Received keyboard interrupt signal.",
                )
            )

    def tango(self):
        with ChallengeSentinel(
            dir_challenge=DIR_CHALLENGE,
            sitekey=random.choice(TOP_LEVEL_SITEKEY),
            silence=self.silence,
            lang=self.lang,
            debug=self.debug,
        ) as sentinel:
            logger.info(
                ToolBox.runtime_report(
                    motive="BUILD", action_name=sentinel.action_name, monitor=sentinel.monitor_site
                )
            )
            sentinel.tango(sentinel.ctx_session)

    def waltz(self):
        with ChallengeCollector(
            dir_rainbow_backup=DIR_RAINBOW_BACKUP,
            focus_labels=CollectorSettings.FOCUS_LABELS,
            pending_labels=CollectorSettings.PENDING_LABELS,
            sitekey=random.choice(TOP_LEVEL_SITEKEY),
            debug=self.debug,
            silence=self.silence,
        ) as collector:
            logger.info(
                ToolBox.runtime_report(
                    motive="BUILD",
                    action_name=collector.action_name,
                    monitor=collector.monitor_site,
                )
            )
            collector.claim(collector.ctx_session)


class ChallengeSentinel(Guarder):
    """hCAPTCHA New Challenge Sentinel"""

    def __init__(
        self,
        dir_challenge: str,
        sitekey: str = None,
        silence: Optional[bool] = True,
        lang: Optional[str] = "en",
        skipped_labels: dict = None,
        debug: Optional[bool] = None,
    ):
        """
        :param dir_challenge:
        :param skipped_labels: 英文停用词映射
        :param sitekey: 监控站键
        :param silence:
        :param lang:
        """
        super().__init__(dir_workspace=dir_challenge, lang=lang, debug=debug, silence=silence)
        sitekey = "ace50dd0-0d68-44ff-931a-63b670c7eed7" if sitekey is None else sitekey
        self.monitor_site = f"https://accounts.hcaptcha.com/demo?sitekey={sitekey}"

        # 直接对目标语种的别名映射表进行人工补充
        if skipped_labels:
            self.label_alias.update(skipped_labels)

        # 服务注册
        self.action_name = "ChallengeSentinel"
        self.lark = LarkAlert(LarkSettings.APP_ID, LarkSettings.APP_SECRET)

    def lock_challenge(self):
        """缓存加锁，防止新挑战的重复警报"""
        self.label_alias[self.label] = self.label

        # TODO: {{<- MongoDB Sync ->}}

        return self.label

    def unlock_challenge(self, keys: Union[Tuple[str, str], str]):
        """
        弹出缓存锁，允许新挑战的重复警报
        :param keys: 需要弹出的 label，通常需要传入 clean_label 以及 raw_label
        :return:
        """
        if isinstance(keys, str):
            keys = [keys]
        for key in keys:
            self.label_alias.pop(key)

        # TODO: {{<- MongoDB Offload ->}}

    def broadcast_alert_information(self):
        """广播预警信息"""
        # 缓存加锁
        key = self.lock_challenge()

        # 检查挑战截图的路径
        challenge_img_key = ""
        if os.path.exists(self.path_screenshot):
            resp_upload_img = self.lark.upload_img(self.path_screenshot)
            challenge_img_key = resp_upload_img.get("data", {}).get("image_key", "")
            self.path_screenshot = ""

        # 向研发部门群组发送报警卡片
        resp_fire_card = self.lark.fire_card(
            chat_id=LarkSettings.CHAT_ID,
            hcaptcha_link=self.monitor_site,
            label_name=self.label_alias.get(self.label, self.label),
            challenge_img_key=challenge_img_key,
        )

        # 推送失败 | 解锁缓存，继续挑战
        if resp_fire_card.get("code", -1) != 0:
            self.unlock_challenge(key)
            return logger.error(
                ToolBox.runtime_report(
                    motive="ALERT",
                    action_name=self.action_name,
                    message="Lark 报警消息推送失败",
                    challenge_img_key=challenge_img_key,
                    path_screenshot=self.path_screenshot,
                    response=resp_fire_card,
                )
            )

        # 推送成功 | 保持缓存锁定状态，避免重复警报
        return logger.success(
            ToolBox.runtime_report(
                motive="ALERT", action_name=self.action_name, message="Lark 报警消息推送成功"
            )
        )

    def tango(self, ctx):
        """
        一轮检测不能超过 5min

        :param ctx:
        :return:
        """
        loop_times = -1
        retry_times = 3

        while loop_times < retry_times:
            loop_times += 1

            # 有头模式下自动最小化
            ctx.get(self.monitor_site)
            ctx.minimize_window()

            # 激活 Checkbox challenge
            self.anti_checkbox(ctx)

            for _ in range(random.randint(5, 8)):
                # 更新挑战框架 | 任务提前结束或进入失败
                if self.switch_to_challenge_frame(ctx) in [
                    self.CHALLENGE_SUCCESS,
                    self.CHALLENGE_REFRESH,
                ]:
                    break

                # 正常响应 | 已标记的挑战标签
                if not self.checking_dataset(ctx):
                    time.sleep(random.uniform(3, 5))
                    continue

                # 拉响警报 | 出现新的挑战
                self.broadcast_alert_information()


class ChallengeCollector(RainbowClaimer):
    """hCAPTCHA Focus Challenge Collector"""

    def __init__(
        self,
        dir_rainbow_backup: str,
        focus_labels: Optional[dict] = None,
        pending_labels: Optional[list] = None,
        sitekey: str = None,
        debug: Optional[bool] = None,
        silence: Optional[bool] = None,
    ):
        super().__init__(
            dir_rainbow_backup=dir_rainbow_backup,
            focus_labels=focus_labels,
            pending_labels=pending_labels,
            sitekey=sitekey,
            debug=debug,
            silence=silence,
        )

    def claim(self, ctx, retry_times=5):
        if not self.label_alias:
            logger.error(
                ToolBox.runtime_report(
                    motive="CLAIM", action_name=self.action_name, message="聚焦挑战为空，无法启动采集器任务"
                )
            )
            return
        logger.info(
            ToolBox.runtime_report(
                motive="CLAIM",
                action_name=self.action_name,
                message="启动采集器",
                focus=[self.label_alias.keys()],
                sitekey=self.sitekey,
            )
        )
        super().claim(ctx, retry_times)

    def unpack(self):
        statistics_: Optional[dict] = super().unpack()
        for flag in statistics_:
            count = statistics_[flag]
            if count:
                logger.success(f"UNPACK [{flag}] --> count={count}")

    def update(self, path_rainbow_yaml: str):
        if not self.pending_labels:
            logger.error(
                ToolBox.runtime_report(
                    motive="RAINBOW", action_name=self.action_name, message="预设的彩虹键为空，无法启动采集器任务"
                )
            )
            return
        rainbow_hash = super().update(path_rainbow_yaml)
        if rainbow_hash:
            logger.success(f"RAINBOW_HASH: {rainbow_hash}")
        else:
            logger.error(
                ToolBox.runtime_report(
                    motive="RAINBOW",
                    action_name=self.action_name,
                    message="彩虹表数据库不存在",
                    path=path_rainbow_yaml,
                )
            )
