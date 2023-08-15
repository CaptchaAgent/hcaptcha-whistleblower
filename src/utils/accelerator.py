# -*- coding: utf-8 -*-
# Time       : 2021/12/22 9:05
# Author     : QIN2DIM
# Github     : https://github.com/QIN2DIM
# Description:
from __future__ import annotations

import asyncio
import sys
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Iterable, Any

from httpx import AsyncClient


@dataclass
class AshFramework(ABC):
    """轻量化的协程控件"""

    container: Iterable

    @classmethod
    def from_container(cls, container):
        if sys.platform.startswith("win") or "cygwin" in sys.platform:
            asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
        else:
            asyncio.set_event_loop(asyncio.new_event_loop())
        return cls(container=container)

    @abstractmethod
    async def control_driver(self, context: Any, client: AsyncClient):
        """需要并发执行的代码片段"""
        raise NotImplementedError

    async def subvert(self):
        if not self.container:
            return
        async with AsyncClient() as client:
            task_list = [self.control_driver(context, client) for context in self.container]
            await asyncio.gather(*task_list)

    def execute(self):
        asyncio.run(self.subvert())
