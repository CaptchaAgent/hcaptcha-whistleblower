# -*- coding: utf-8 -*-
# Time       : 2022/7/16 7:13
# Author     : QIN2DIM
# Github     : https://github.com/QIN2DIM
# Description:
from typing import Optional, Sequence


class ArmorException(Exception):
    """Armor module basic exception"""

    def __init__(self, msg: Optional[str] = None, stacktrace: Optional[Sequence[str]] = None):
        self.msg = msg
        self.stacktrace = stacktrace
        super().__init__()

    def __str__(self) -> str:
        exception_msg = f"Message: {self.msg}\n"
        if self.stacktrace:
            stacktrace = "\n".join(self.stacktrace)
            exception_msg += f"Stacktrace:\n{stacktrace}"
        return exception_msg


class ChallengeException(ArmorException):
    """hCAPTCHA Challenge basic exceptions"""


class ChallengePassed(ChallengeException):
    """挑战未弹出"""


class LabelNotFoundException(ChallengeException):
    """获取到空的图像标签名"""


class ChallengeLangException(ChallengeException):
    """指定了不兼容的挑战语言"""
