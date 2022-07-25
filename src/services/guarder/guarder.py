# -*- coding: utf-8 -*-
# Time       : 2022/7/16 17:42
# Author     : QIN2DIM
# Github     : https://github.com/QIN2DIM
# Description:
import hashlib
import os
import random
import time
from typing import Optional

import yaml

from .core import Guarder


class RainbowClaimer(Guarder):
    def __init__(
        self,
        dir_rainbow_backup: str,
        focus_labels: Optional[dict] = None,
        pending_labels: Optional[list] = None,
        sitekey: str = None,
        lang: Optional[str] = "en",
        debug: Optional[bool] = None,
        silence: Optional[bool] = None,
    ):
        """
        :param focus_labels: 不在 claiming_label 中的挑战将被跳过，左为 split label 右为编排数据
        :param dir_rainbow_backup: RainbowClaimer 工作空间，需要与普通挑战业务线隔离
        :param sitekey:
        :param lang:
        :param debug:
        :param silence:
        """
        self.dir_rainbow_backup = dir_rainbow_backup
        dir_challenge = os.path.join(self.dir_rainbow_backup, "_challenge")

        super().__init__(dir_workspace=dir_challenge, lang=lang, debug=debug, silence=silence)
        self.sitekey = "adafb813-8b5c-473f-9de3-485b4ad5aa09" if sitekey is None else sitekey
        self.monitor_site = f"https://accounts.hcaptcha.com/demo?sitekey={self.sitekey}"

        # 1. 添加 label_alias
        # ---------------------------------------------------
        # 不在 alias 中的挑战将被跳过
        self.label_alias = {} if not focus_labels else focus_labels

        # 2. 创建彩虹键
        # ---------------------------------------------------
        # 彩虹表中的 rainbow key
        self.pending_labels = [] if not pending_labels else pending_labels
        if self.label_alias:
            pending_labels = set(self.pending_labels)
            for rainbow_key in self.label_alias.values():
                pending_labels.add(rainbow_key)
            self.pending_labels = list(pending_labels)

        # 3. 创建挑战目录
        # ---------------------------------------------------
        # 遇到新挑战时，先手动创建 rainbow_backup/challengeName/
        # 再在这个目录下分别创建 yes 和 bad 两个文件夹
        self.boolean_tags = ["yes", "bad"]
        self.init_rainbow_backup()

    def init_rainbow_backup(self):
        """根据rainbow-key自动初始化数据集存放目录"""
        for tag in self.boolean_tags:
            for label in self.pending_labels:
                os.makedirs(os.path.join(self.dir_rainbow_backup, label, tag), exist_ok=True)

    def download_images(self):
        if self.label_alias.get(self.label):
            super().download_images()

    def claim(self, ctx, retry_times=5):
        """
        定向采集数据集

        :param ctx:
        :param retry_times:
        :return:
        """
        loop_times = -1
        start = time.time()

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
                    loop_times -= 1
                    break

                # 勾取数据集 | 跳过非聚焦挑战
                self.hacking_dataset(ctx)

                # 随机休眠 | 降低请求频率
                if time.time() - start < 180:
                    time.sleep(random.uniform(1, 2))
                    continue

                # 解包数据集 | 1次/3minutes
                self.unpack()
                start = time.time()

        # 退出任务前执行最后一次解包任务
        # 确保所有任务进度得以同步
        self.unpack()

    def _unpack(self, dst_dir, flag):
        """
        將 DIR_CHALLENGE 中的内容解壓到目標路徑

        :param flag: 自定義標簽名
        :param dst_dir: rainbow_backup/<label>/
        :return:
        """
        # rainbow_backup/_challenge
        src_dir = self.dir_workspace

        # 标记已有的内容
        _exists_files = {}
        for _, _, files in os.walk(dst_dir):
            for fn in files:
                _exists_files.update({fn: "*"})

        # 清洗出包含標簽名的文件夾緩存
        # 1. 拼接挑戰圖片的絕對路徑
        # 2. 读取二进制流编成hash文件名
        # 3. 写到目标路径
        samples = set()
        for dir_challenge_cache_name in os.listdir(src_dir):
            if flag != dir_challenge_cache_name.split("_", 1)[
                -1
            ] or dir_challenge_cache_name.endswith(".png"):
                continue
            path_fs = os.path.join(src_dir, dir_challenge_cache_name)
            for img_filename in os.listdir(path_fs):
                path_img = os.path.join(path_fs, img_filename)
                with open(path_img, "rb") as file:
                    data = file.read()
                filename = f"{hashlib.md5(data).hexdigest()}.png"

                # 过滤掉已存在的文件，无论是 yes|bad|pending
                if not _exists_files.get(filename):
                    with open(os.path.join(dst_dir, filename), "wb") as file:
                        file.write(data)
                        samples.add(filename)

        return len(samples)

    def unpack(self):
        """
        解构彩虹表，自动分类，去重，拷贝

        FROM: rainbow_backup/_challenge
        TO: rainbow_backup/[*challengeName]

        :return:
        """
        statistics_ = {}
        for flag in self.pending_labels:
            statistics_[flag] = self._unpack(
                dst_dir=os.path.join(self.dir_rainbow_backup, flag), flag=flag
            )
        return statistics_

    def update(self, path_rainbow_yaml: str) -> Optional[str]:
        """
        更新彩虹表

        FROM: rainbow_backup/_challenge/ --(hook)--> YES/NO
        TO: rainbow.yaml

        :return:
        """
        if not os.path.exists(self.dir_rainbow_backup):
            return

        # 初始化彩虹表数据容器
        _rainbow_table = {}

        # 若已存在历史数据表，载入初始化后的彩虹表数据容器
        if os.path.exists(path_rainbow_yaml):
            with open(path_rainbow_yaml, "r", encoding="utf8") as file:
                stream = yaml.safe_load(file)
                _rainbow_table = stream if isinstance(stream, dict) else {}

        # 遍历数据集 逐层拓展彩虹表
        for label in self.pending_labels:
            if not _rainbow_table.get(label):
                _rainbow_table[label] = {}
            for tag in self.boolean_tags:
                if not _rainbow_table[label].get(tag):
                    _rainbow_table[label][tag] = {}

                # 抽取 Tag 下的所有文件名
                filenames = os.listdir(os.path.join(self.dir_rainbow_backup, label, tag))

                # 初始化彩虹表 | 将 {MD5}.png 中的 `MD5` 抽离出来
                rainbow_hash = {filename.split(".")[0]: "*" for filename in filenames}

                # 拓展彩虹表 | 填充标签下 tag 的实例
                _rainbow_table[label][tag].update(rainbow_hash)

                # 拓展彩虹表 | 填充标签下 tag 的实例
                _rainbow_table[label][tag].update(rainbow_hash)

        # 写回彩虹表
        with open(path_rainbow_yaml, "w", encoding="utf8") as file:
            yaml.safe_dump(_rainbow_table, file)

        # 更新彩虹表 Hash 值
        with open(path_rainbow_yaml, "rb") as file:
            return hashlib.sha256(file.read()).hexdigest()
