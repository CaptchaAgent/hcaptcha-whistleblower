# -*- coding: utf-8 -*-
# Time       : 2022/7/15 20:49
# Author     : QIN2DIM
# Github     : https://github.com/QIN2DIM
# Description:
from __future__ import annotations

import os.path
import random
import time
from contextlib import suppress
from typing import Optional, Union, Tuple

from loguru import logger

from services.guarder import Guarder
from services.guarder import RainbowClaimer
from services.larker import LarkAlert
from settings import config, firebird


class Sentinel(Guarder):
    """hCAPTCHA New Challenge Sentinel"""

    def __init__(self, sitekey: str = None):
        super().__init__()
        self.sitekey = sitekey or "ace50dd0-0d68-44ff-931a-63b670c7eed7"
        self.monitor_site = f"https://accounts.hcaptcha.com/demo?sitekey={sitekey}"

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
        lark = LarkAlert(config.lark.app_id, config.lark.app_secret)

        # 缓存加锁
        key = self.lock_challenge()

        # 检查挑战截图的路径
        challenge_img_key = ""
        if os.path.exists(self.path_screenshot):
            resp_upload_img = lark.upload_img(self.path_screenshot)
            challenge_img_key = resp_upload_img.get("data", {}).get("image_key", "")
            self.path_screenshot = ""

        # 向研发部门群组发送报警卡片
        resp_fire_card = lark.fire_card(
            chat_id=config.lark.chat_id,
            hcaptcha_link=self.monitor_site,
            label_name=self.label_alias.get(self.label, self.label),
            challenge_img_key=challenge_img_key,
        )

        # 推送失败 | 解锁缓存，继续挑战
        if resp_fire_card.get("code", -1) != 0:
            self.unlock_challenge(key)
            return logger.error(
                "Lark 报警消息推送失败",
                challenge_img_key=challenge_img_key,
                path_screenshot=self.path_screenshot,
                response=resp_fire_card,
            )
        # 推送成功 | 保持缓存锁定状态，避免重复警报
        return logger.success("Lark 报警消息推送成功")

    def tango(self, ctx, timer: Optional[int] = None):
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
                # self.broadcast_alert_information()
                firebird.flush()
                if timer and time.time() - trigger > timer:
                    logger.info(f"Drop by outdated - upto={timer}")
                    return


class Collector(RainbowClaimer):
    """hCAPTCHA Focus Challenge Collector"""

    def claim(self, ctx, retries=5):
        if not self.label_alias:
            logger.error("聚焦挑战为空，跳过采集任务")
            return
        logger.debug(f"Focus on --> sitekey::{self.sitekey}")
        logger.debug(f"Focus on --> monitor::{self.monitor_site}")
        logger.debug(f"Focus on --> {set(self.label_alias.values())}")
        with suppress(KeyboardInterrupt):
            super().claim(ctx, retries)

    def unpack(self):
        statistics_: Optional[dict] = super().unpack()
        for flag in statistics_:
            count = statistics_[flag]
            if count:
                logger.success(f"UNPACK [{flag}] --> count={count}")
