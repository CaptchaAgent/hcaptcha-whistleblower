# -*- coding: utf-8 -*-
# Time       : 2022/7/15 20:49
# Author     : QIN2DIM
# Github     : https://github.com/QIN2DIM
# Description:
import os.path
import random
import time
import typing
from contextlib import suppress
from typing import Optional, Union, Tuple
from urllib.request import getproxies

import requests
import yaml
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
        self.scheduler.start()

        try:
            while True:
                time.sleep(3600)
        except (KeyboardInterrupt, EOFError):
            self.scheduler.shutdown(wait=False)
            logger.debug(
                ToolBox.runtime_report(
                    motive="EXITS",
                    action_name=self.action_name,
                    message="Received keyboard interrupt signal.",
                )
            )

    def tango(self, sitekey=None, timer: Optional[int] = 300):
        with ChallengeSentinel(
            dir_challenge=DIR_CHALLENGE,
            sitekey=sitekey or random.choice(TOP_LEVEL_SITEKEY),
            silence=self.silence,
            lang=self.lang,
            debug=self.debug,
        ) as sentinel:
            logger.info(
                ToolBox.runtime_report(
                    motive="BUILD", action_name=sentinel.action_name, monitor=sentinel.monitor_site
                )
            )
            sentinel.tango(sentinel.ctx_session, timer=timer)

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
        debug: Optional[bool] = None,
    ):
        """
        :param dir_challenge:
        :param sitekey: 监控站键
        :param silence:
        :param lang:
        """
        super().__init__(dir_workspace=dir_challenge, lang=lang, debug=debug, silence=silence)
        self.sitekey = "ace50dd0-0d68-44ff-931a-63b670c7eed7" if sitekey is None else sitekey
        self.monitor_site = f"https://accounts.hcaptcha.com/demo?sitekey={sitekey}"

        # 服务注册
        self.action_name = "ChallengeSentinel"
        self.lark = LarkAlert(LarkSettings.APP_ID, LarkSettings.APP_SECRET)

        # 同步上游挑战进度
        self.pull_skipped_prompts()

    def pull_skipped_prompts(self):
        url_remote_objects = (
            "https://raw.githubusercontent.com/QIN2DIM/hcaptcha-challenger/main/src/objects.yaml"
        )
        fn = "_remote_objects.yaml"
        path_objects_yaml = os.path.join("database", "skipped_prompts", fn)
        os.makedirs(os.path.dirname(path_objects_yaml), exist_ok=True)

        try:
            _request_asset(url_remote_objects, path_objects_yaml, fn)
        except Exception as err:
            logger.exception(err)
        else:
            if not os.path.exists(path_objects_yaml) or not os.path.getsize(path_objects_yaml):
                logger.warning("objects 配置文件不存在或为空")
                return
            with open(path_objects_yaml, "r", encoding="utf8") as file:
                data: typing.Dict[str, dict] = yaml.safe_load(file.read())

            label_to_i18ndict = data.get("label_alias", {})
            if not label_to_i18ndict:
                return

            for model_label, i18n_to_raw_labels in label_to_i18ndict.items():
                for lang, prompt_labels in i18n_to_raw_labels.items():
                    for prompt_label in prompt_labels:
                        if lang == self.lang:
                            self.label_alias[prompt_label.strip()] = model_label
                        Guarder.label_alias[lang][prompt_label.strip()] = model_label

            logger.success(f"Prompts sync successfully - total={len(label_to_i18ndict)}")

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

    def deploy_remote_collector(self):
        """部署遠程任務"""
        with suppress(Exception):
            logger.info("Create collector task")
            api_create_task = f"http://{CollectorSettings.HOST}{CollectorSettings.API_CREATE_TASK}"
            headers = {"authentication": f"Bearer {CollectorSettings.TOKEN}"}
            data = {"prompt": self.prompt, "sitekey": self.sitekey, "upto": "1800"}
            resp = requests.post(api_create_task, headers=headers, json=data)
            logger.debug(resp.json())

            logger.info("Check collector tasks")
            api_check_task = f"http://{CollectorSettings.HOST}{CollectorSettings.API_CHECK_TASKS}"
            headers = {"authentication": f"Bearer {CollectorSettings.TOKEN}"}
            resp = requests.get(api_check_task, headers=headers)
            logger.debug(resp.text)

    def tango(self, ctx, timer: Optional[int] = None):
        """

        :param ctx:
        :param timer:
        :return:
        """
        loop_times = -1
        retry_times = 3 if not timer else 100
        trigger = time.time()
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
                # 自動部署采集任務 | 呈遞上下文
                self.deploy_remote_collector()
                if timer and time.time() - trigger > timer:
                    logger.info(f"Drop by outdated - upto={timer}")
                    return


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

    def claim(self, ctx, retries=5, on_outdated=None):
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
                on_outdated=on_outdated,
            )
        )
        with suppress(KeyboardInterrupt):
            super().claim(ctx, retries, on_outdated)
        # 退出任务前执行最后一次解包任务
        # 确保所有任务进度得以同步
        self.unpack()
        logger.success(
            ToolBox.runtime_report(motive="SHUTDOWN", action_name=self.action_name, message="采集器退出")
        )

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


def _request_asset(asset_download_url: str, asset_path: str, fn_tag: str):
    headers = {
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/105.0.0.0 Safari/537.36 Edg/105.0.1343.27"
    }
    logger.debug(f"Downloading {fn_tag} from {asset_download_url}")

    with open(asset_path, "wb") as file, requests.get(
        asset_download_url, headers=headers, stream=True, proxies=getproxies()
    ) as response:
        for chunk in response.iter_content(chunk_size=1024):
            if chunk:
                file.write(chunk)
