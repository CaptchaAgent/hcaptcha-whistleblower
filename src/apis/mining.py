# -*- coding: utf-8 -*-
# Time       : 2023/8/16 2:27
# Author     : QIN2DIM
# GitHub     : https://github.com/QIN2DIM
# Description:
from services.guarder.canvas_mining import CollectorT
from utils.agents import get_challenge_ctx


def run(sitekey: str = "ace50dd0-0d68-44ff-931a-63b670c7eed7", r: int = 5):
    ct = CollectorT(sitekey=sitekey)
    with get_challenge_ctx(silence=False, lang="en") as ctx:
        ct.claim(ctx, retries=r)
