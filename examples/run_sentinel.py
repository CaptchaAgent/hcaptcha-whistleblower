# -*- coding: utf-8 -*-
# Time       : 2023/8/16 3:07
# Author     : QIN2DIM
# GitHub     : https://github.com/QIN2DIM
# Description:
from apis import sentinel
from settings import SiteKey


def execute():
    sentinel.run(deploy=False, silence=False, sitekey=SiteKey.user, timer=300)


if __name__ == '__main__':
    execute()
