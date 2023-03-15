import sys

sys.path.append("src")
import typing

import requests
from loguru import logger
from services.settings import CollectorSettings as Config

url = f"http://rn35c.capoo.xyz:10819"
api_create_task = url + Config.API_CREATE_TASK
api_check_task = url + Config.API_CHECK_TASKS
api_download = url + Config.API_DOWNLOAD
headers = {"authentication": f"Bearer {Config.TOKEN}"}


def create_task(prompt: str, sitekey: str, upto: typing.Optional[str] = "300"):
    """

    :param prompt: 原始切片，如：bowl of pasta
    :param sitekey: 如：adafb813-8b5c-473f-9de3-485b4ad5aa09
    :param upto: 定时器，默认 300s
    :return:
    """
    logger.info("Create collector task")
    data = {"prompt": prompt, "sitekey": sitekey, "upto": upto}
    resp = requests.post(api_create_task, headers=headers, json=data)
    logger.debug(resp.json())


def check_task():
    logger.info("Check Tasks")
    resp = requests.get(api_check_task, headers=headers)
    print(headers)
    logger.debug(resp.text)


if __name__ == "__main__":
    check_task()
