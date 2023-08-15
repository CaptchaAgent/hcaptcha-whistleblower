# -*- coding: utf-8 -*-
# Time       : 2023/8/16 3:15
# Author     : QIN2DIM
# GitHub     : https://github.com/QIN2DIM
# Description:
from apis import collector
from settings import SiteKey


def execute():
    collector.startup(sitekey=SiteKey.epic, silence=False)


if __name__ == '__main__':
    execute()
