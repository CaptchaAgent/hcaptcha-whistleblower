# -*- coding: utf-8 -*-
# Time       : 2022/7/15 20:41
# Author     : QIN2DIM
# GitHub     : https://github.com/QIN2DIM
# Description: 👻 哟！Lark飞书人！
from __future__ import annotations

from contextlib import suppress
from typing import Optional

from fire import Fire

from apis import checker, collector, sentinel, mining


class Scaffold:
    @staticmethod
    def check(prompt: str, lang: Optional[str] = None):
        """
        en/zh prompt to model flag

        Usage: python main.py check "请点击每张包含有人打曲棍球的图片"
        or: python main.py check "Please click each image containing red roses in a garden"

        :param lang: zh/en
        :param prompt: Challenge Prompt
        :return:
        """
        checker.launch(prompt, lang)

    @staticmethod
    def collector(sitekey: str | None = None):
        """彩虹表控制接口 數據采集"""
        collector.startup(sitekey=sitekey)

    @staticmethod
    def unpack():
        """
        将 _challenge 的数据集合并到样本数据集中（copy）
        :return:
        """
        collector.unpack()

    @staticmethod
    def label():
        """打开/审查/开始标注 focus 的指定目录"""
        with suppress(KeyboardInterrupt):
            collector.label()

    @staticmethod
    def sentinel(
            deploy: bool | None = None,
            silence: bool | None = True,
            sitekey: str | None = None,
            timer: int = 300,
    ):
        """
        部署 hCAPTCHA New Challenger 报警哨兵

        :param timer: 定時器，如果不部署，運行多久。默認5分鐘
        :param sitekey:
        :param deploy: Default None. 部署定时任务。每隔 N 分钟发起一次针对高价值站键的挑战扫描，
            当出现新挑战时向研发部门的飞书群组发送报警卡片
        :param silence: Default True.
        :return:
        """
        sentinel.run(deploy=deploy, silence=silence, sitekey=sitekey, timer=timer)

    @staticmethod
    def mining(sitekey: str | None = None, r: int = 5):
        """采集 image area select challenge 数据集"""
        mining.run(sitekey, r)


if __name__ == "__main__":
    Fire(Scaffold)
