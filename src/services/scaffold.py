# -*- coding: utf-8 -*-
# Time       : 2022/7/15 20:48
# Author     : QIN2DIM
# Github     : https://github.com/QIN2DIM
# Description:
from typing import Optional

from apis.scaffold import collector, sentinel


class Scaffold:
    @staticmethod
    def test():
        pass

    @staticmethod
    def collector(
        deploy: Optional[bool] = None,
        silence: Optional[bool] = True,
        lang: Optional[str] = "en",
        debug: Optional[bool] = False,
        sitekey: Optional[str] = None,
        merge: Optional[bool] = False,
        unpack: Optional[bool] = False,
    ):
        """
        彩虹表控制接口 數據采集

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
        )

    @staticmethod
    def sentinel(
        deploy: Optional[bool] = None,
        silence: Optional[bool] = True,
        lang: Optional[str] = "en",
        debug: Optional[bool] = False,
    ):
        """
        部署 hCAPTCHA New Challenger 报警哨兵

        :param debug:
        :param deploy: Default None. 部署定时任务。每隔 N 分钟发起一次针对高价值站键的挑战扫描，
            当出现新挑战时向研发部门的飞书群组发送报警卡片
        :param silence: Default True.
        :param lang: Default ``en``.
        :return:
        """
        sentinel.run(deploy=deploy, silence=silence, lang=lang, debug=debug)

    @staticmethod
    def mining(
        silence: Optional[bool] = True,
        debug: Optional[bool] = None,
        site_key: Optional[str] = None,
        r: int = 5,
    ):
        """
        采集 image area select challenge 数据集

        :param r:
        :param silence:
        :param debug:
        :param site_key:
        :return:
        """
        collector.canvas_mining(silence=silence, debug=debug, site_key=site_key, retry_times=r)
