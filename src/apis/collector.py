# -*- coding: utf-8 -*-
# Time       : 2022/7/15 21:00
# Author     : QIN2DIM
# Github     : https://github.com/QIN2DIM
# Description:
import os
import subprocess
import sys
from typing import Optional

from loguru import logger

from apis._runtime import Collector
from settings import project, firebird
from utils.agents import get_challenge_ctx

GETTER_RETRIES = 500

unpack = Collector().unpack


def label():
    labels = list(firebird.focus_labels.values())
    menu = "".join([f"{i}. {l}\n" for i, l in enumerate(labels)])
    prompt = f"--> Open this focus folder [0-{len(labels) - 1}]/> "
    while True:
        s = input(f"{menu}{prompt}")
        print("".center(48, "-"))
        if not s.isdigit() or not 0 <= int(s) <= len(labels) - 1:
            continue
        filename = os.path.join(project.rainbow_backup_dir, labels[int(s)])
        if sys.platform == "win32":
            os.startfile(filename)
        else:
            opener = "open" if sys.platform == "darwin" else "xdg-open"
            subprocess.call([opener, filename])
        logger.success(f"startfile - {filename=}")
        return


def startup(sitekey: Optional[str] = None, silence=False):
    """根据label定向采集数据集"""
    logger.info("startup collector")

    # 采集数据集 | 自动解包数据集
    cc = Collector(sitekey=sitekey)
    ctx = get_challenge_ctx(lang="en", silence=silence)
    try:
        # 退出任务前执行最后一次解包任务
        # 确保所有任务进度得以同步
        cc.claim(ctx, retries=GETTER_RETRIES)
        cc.unpack()
    finally:
        logger.success("采集器退出")
        ctx.quit()
