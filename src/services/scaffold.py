# -*- coding: utf-8 -*-
# Time       : 2022/7/15 20:48
# Author     : QIN2DIM
# Github     : https://github.com/QIN2DIM
# Description:
from typing import Optional

from apis.scaffold import collector, sentinel, checker


class Scaffold:
    @staticmethod
    def test():
        pass

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
    def collector(
        deploy: Optional[bool] = None,
        silence: Optional[bool] = True,
        lang: Optional[str] = "en",
        debug: Optional[bool] = False,
        sitekey: Optional[str] = None,
        merge: Optional[bool] = False,
        unpack: Optional[bool] = False,
        upto: Optional[int] = None,
    ):
        """
        彩虹表控制接口 數據采集

        :param upto:
        :param unpack:
        :param merge:
        :param sitekey:
        :param deploy:
        :param silence:
        :param lang:
        :param debug:
        :return:
        """
        collector.startup(
            deploy=deploy,
            silence=silence,
            lang=lang,
            debug=debug,
            site_key=sitekey,
            merge=merge,
            unpack=unpack,
            upto=upto,
        )

    @staticmethod
    def sentinel(
        deploy: Optional[bool] = None,
        silence: Optional[bool] = True,
        lang: Optional[str] = "en",
        debug: Optional[bool] = False,
        host: Optional[str] = None,
        sitekey: Optional[str] = None,
        timer: Optional[int] = 300,
    ):
        """
        部署 hCAPTCHA New Challenger 报警哨兵

        :param timer: 定時器，如果不部署，運行多久。默認5分鐘
        :param sitekey:
        :param host: 采集器部署接口
        :param debug:
        :param deploy: Default None. 部署定时任务。每隔 N 分钟发起一次针对高价值站键的挑战扫描，
            当出现新挑战时向研发部门的飞书群组发送报警卡片
        :param silence: Default True.
        :param lang: Default ``en``.
        :return:
        """
        host = host or "127.0.0.1:10819"
        sentinel.run(
            deploy=deploy,
            silence=silence,
            lang=lang,
            debug=debug,
            host=host,
            sitekey=sitekey,
            timer=timer,
        )

    @staticmethod
    def mining(
        silence: Optional[bool] = True,
        debug: Optional[bool] = None,
        sitekey: Optional[str] = None,
        r: int = 5,
    ):
        """
        采集 image area select challenge 数据集

        :param r:
        :param silence:
        :param debug:
        :param sitekey:
        :return:
        """
        # Stable challenge
        sitekey = sitekey or "ace50dd0-0d68-44ff-931a-63b670c7eed7"
        collector.canvas_mining(silence=silence, debug=debug, site_key=sitekey, retry_times=r)
