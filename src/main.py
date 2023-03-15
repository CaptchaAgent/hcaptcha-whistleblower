# -*- coding: utf-8 -*-
# Time       : 2022/7/15 20:41
# Author     : QIN2DIM
# Github     : https://github.com/QIN2DIM
# Description: 👻 哟！Lark飞书人！
# import os
# os.environ["https_proxy"] = "https://127.0.0.1:20891"
from fire import Fire

from services.scaffold import Scaffold

if __name__ == "__main__":
    Fire(Scaffold)
