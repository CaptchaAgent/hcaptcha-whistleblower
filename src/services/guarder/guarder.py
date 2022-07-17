# -*- coding: utf-8 -*-
# Time       : 2022/7/16 17:42
# Author     : QIN2DIM
# Github     : https://github.com/QIN2DIM
# Description:
import hashlib
import os
import random
import time

import yaml

from services.settings import logger
from .core import Guarder


class RainbowClaimer(Guarder):
    TOP_LEVEL_SITEKEY = [
        "f5561ba9-8f1e-40ca-9b5b-a0b3f719ef34",  # discord
        "91e4137f-95af-4bc9-97af-cdcedce21c8c",  # epic
        "adafb813-8b5c-473f-9de3-485b4ad5aa09",  # top level
        "ace50dd0-0d68-44ff-931a-63b670c7eed7",  # top level
    ]

    def __init__(self, focus_labels: dict, dir_rainbow_backup: str, sitekey: str = None):
        """

        :param sitekey:
        :param focus_labels: 不在 claiming_label 中的挑战将被跳过，左为 split label 右为编排数据
        :param dir_rainbow_backup: RainbowClaimer 工作空间，需要与普通挑战业务线隔离
        """
        self.dir_rainbow_backup = dir_rainbow_backup
        dir_challenge = os.path.join(self.dir_rainbow_backup, "_challenge")

        super().__init__(dir_workspace=dir_challenge, lang="en", debug=True)
        sitekey = random.choice(self.TOP_LEVEL_SITEKEY) if sitekey is None else sitekey
        self.claim_site = f"https://accounts.hcaptcha.com/demo?sitekey={sitekey}"

        # 1. 添加 label_alias
        # ---------------------------------------------------
        # 不在 alias 中的挑战将被跳过
        self.label_alias = focus_labels

        # 2. 创建彩虹键
        # ---------------------------------------------------
        # 彩虹表中的 rainbow key
        self.pending_labels = [
            "domestic cat",
            "vertical river",
            "airplane in the sky flying left",
            "airplanes in the sky that are flying to the right",
            "elephants drawn with leaves",
            "seaplane",
            "airplane",
            "bicycle",
            "train",
            "bedroom",
            "lion",
            "bridge",
            "lion yawning with open mouth",
            "lion with closed eyes",
            "horse with white legs",
        ]
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

        # 启动一个协程的 challenger 任务
        # 总共访问网页 retry_times 次，单词访问中连续刷新5次挑战
        while loop_times < retry_times:
            loop_times += 1

            # 有头模式下自动最小化
            ctx.get(self.claim_site)
            ctx.minimize_window()

            # 激活 Checkbox challenge
            self.anti_checkbox(ctx)

            for _ in range(5):
                # 更新挑战框架 | 任务提前结束或进入失败
                if self.switch_to_challenge_frame(ctx) in [
                    self.CHALLENGE_SUCCESS,
                    self.CHALLENGE_REFRESH,
                ]:
                    break

                # 勾取数据集 | 跳过非聚焦挑战
                self.hacking_dataset(ctx)

                # 随机休眠 | 降低请求频率
                if time.time() - start < 180:
                    time.sleep(random.uniform(2, 4))
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
        count = 0
        for dir_challenge_cache_name in os.listdir(src_dir):
            if flag not in dir_challenge_cache_name or dir_challenge_cache_name.endswith(".png"):
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
                        count += 1

        logger.success(f"UNPACK [{flag}] - {count=}")

    def unpack(self):
        """
        解构彩虹表，自动分类，去重，拷贝

        FROM: rainbow_backup/_challenge
        TO: rainbow_backup/[*challengeName]

        :return:
        """
        for flag in self.pending_labels:
            self._unpack(dst_dir=os.path.join(self.dir_rainbow_backup, flag), flag=flag)

    def update(self, path_rainbow_yaml: str):
        """
        更新彩虹表

        FROM: rainbow_backup/_challenge/ --(hook)--> YES/NO
        TO: rainbow.yaml

        :return:
        """

        if not os.path.exists(self.dir_rainbow_backup):
            logger.error("彩虹表数据库不存在")
            return False

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
            data = file.read()
        logger.success(f"RAINBOW_HASH: {hashlib.sha256(data).hexdigest()}")
