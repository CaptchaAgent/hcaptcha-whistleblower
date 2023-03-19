# -*- coding: utf-8 -*-
# Time       : 2022/10/19 3:23
# Author     : QIN2DIM
# Github     : https://github.com/QIN2DIM
# Description:
import os
import sys
import typing
from dataclasses import dataclass

import pytz

sys.path.append("src")

from sanic import Sanic
from sanic.response import json, file, text, redirect
from sanic.request import Request, HTTPResponse
import hcaptcha_challenger as solver
from hcaptcha_challenger.core import HolyChallenger
from services.settings import CollectorSettings, DIR_RAINBOW_BACKUP, LarkSettings
import zipfile
from loguru import logger

from services.larker import LarkAPI
from datetime import datetime, timedelta

solver.install(upgrade=False)
app = Sanic("auto-collector")
lark = LarkAPI(LarkSettings.APP_ID, LarkSettings.APP_SECRET)

# prompt to sitekey
hot_key = {}
runtime_collectors = {}

allowed_user_token = {"39015381-c7cd-485e-8f13-3c2a2cecab80"}


@dataclass
class CollectorG:
    prompt: str
    sitekey: str
    upto: typing.Union[int, str]
    token: str

    offline_time = ""
    _prompt = ""

    def __post_init__(self):
        if isinstance(self.upto, str):
            try:
                self.upto = int(self.upto)
            except (ValueError, TypeError):
                self.upto = 60
        # 采集器最少启动时间
        self.upto = 60 if self.upto < 60 else self.upto
        self.offline_time = str(
            datetime.now(pytz.timezone("Asia/Shanghai")) + timedelta(seconds=self.upto)
        ).split(".")[0]

    def join(self):
        self._prompt = self.prompt
        hot_key[self._prompt] = self.sitekey
        runtime_collectors[self.prompt] = self.__dict__
        _from = HolyChallenger.split_prompt_message(self.prompt, lang="en")
        _to = _from.replace("-", "_").replace(" ", "_").replace(",", "_")
        CollectorSettings.FOCUS_LABELS[_from] = _to
        self.prompt = _to
        logger.info(
            f"Join Collector - prompt={self.prompt} sitekey={self.sitekey} offline_time={self.offline_time}"
        )

    def detach(self):
        hot_key.pop(self._prompt)


def _lark_anno_deploy_task(
        collector: CollectorG, sharelink: str, title: str, count: typing.Optional[int] = None
):
    href = f"https://accounts.hcaptcha.com/demo?sitekey={collector.sitekey}"
    content = {
        "zh_cn": {
            "title": title,
            "content": [
                [
                    {"tag": "text", "text": f">> prompt: "},
                    {"tag": "a", "href": href, "text": collector.prompt},
                ],
                [
                    {"tag": "text", "text": f">> backdoor: "},
                    {"tag": "a", "href": sharelink, "text": f"下载数据集({count})"},
                ],
                [{"tag": "text", "text": f">> offline: {collector.offline_time}"}],
            ],
        }
    }
    lark.send_group_msg(LarkSettings.CHAT_ID, content=content, msg_type="post")


def _has_available_auth(request: Request):
    auth = request.headers.get("authentication", request.args.get("authentication", ""))
    return auth.replace("Bearer", "").strip()


def _unzip_dataset(prompt: str, dir_pkg: typing.Optional[str] = 0) -> typing.Tuple[str, int]:
    """

    :param prompt: （多单词）加了下滑线的挑战提示
    :return:
    """
    dir_pkg = dir_pkg or os.path.join(DIR_RAINBOW_BACKUP, prompt)
    count = 0
    # 将 yes/bad 中的图片一并吐出，集中到单个文件夹中
    dir_pkg_zip = os.path.join(DIR_RAINBOW_BACKUP, f"{prompt}.zip")
    os.makedirs(os.path.dirname(dir_pkg_zip), exist_ok=True)
    with zipfile.ZipFile(dir_pkg_zip, "w", zipfile.ZIP_DEFLATED) as zf:
        for root, _, files in os.walk(dir_pkg):
            for fn in files:
                path_img = os.path.join(root, fn)
                zf.write(path_img, fn)
                count += 1
    return dir_pkg_zip, count


@logger.catch()
def job(collector: CollectorG, request: Request):
    collector.join()

    sharelink = f"http://{request.host}/v1/download?authentication={collector.token}&prompt={collector.prompt}"

    try:
        logger.info("已部署采集器")
        _lark_anno_deploy_task(collector, sharelink, "已部署采集器")
        if "linux" in sys.platform:
            os.system(
                f"nohup python3 main.py collector --sitekey={collector.sitekey} --upto={collector.upto} &"
            )
    finally:
        collector.detach()
        logger.info("已撤回采集器")
        _, count = _unzip_dataset(collector.prompt)
        _lark_anno_deploy_task(collector, sharelink, "已撤回采集器", count)


@app.route("/createTask", version="v1", methods=["POST"])
async def create_task(request: Request) -> HTTPResponse:
    """
    请求对象结构
    ------
    prompt      string          request     prompt, 原生/切片
    sitekey     string          request     sitekey
    upto        string          optional    timer/seconds, default 1 minutes
    :return:
    """
    if not (token := _has_available_auth(request)):
        return json({"msg": "Access not allowed"}, status=403)

    data = request.json
    prompt = data.get("prompt", "")
    sitekey = data.get("sitekey", "")
    upto = data.get("upto", "60")

    if not prompt or not isinstance(prompt, str) or not sitekey or not isinstance(sitekey, str):
        return json({"msg": "参数类型错误或为空", "prompt": prompt, "sitekey": sitekey})
    if prompt in CollectorSettings.FOCUS_LABELS:
        return json({"msg": "不能重复创建即时采集任务", "prompt": prompt, "sitekey": sitekey})

    collector = CollectorG(prompt=prompt, sitekey=sitekey, upto=upto, token=token)
    job(collector, request)

    return json({"msg": "调度器已部署", "collector": {**collector.__dict__}})


@app.route("/download", version="v1", methods=["GET"])
async def download(request: Request):
    """
    请求对象结构
    ------
    prompt      string          request     handled prompt
    :return:
    """
    if not _has_available_auth(request):
        return text("Access not allowed", status=403)
    prompt = request.args.get("prompt", "")
    if not prompt or not isinstance(prompt, str):
        logger.debug(f"prompt 类型错误或为空 - access={request.ip}")
        return text("prompt 类型错误或为空")

    prompt = prompt.strip()
    dir_pkg = os.path.join(DIR_RAINBOW_BACKUP, prompt)
    if not os.path.isdir(dir_pkg):
        logger.debug(f"任务未创建 - access={request.ip} prompt={prompt} pkg={dir_pkg}")
        return text(f"任务未创建 - prompt={prompt}")
    # 将 yes/bad 中的图片一并吐出，集中到单个文件夹中
    dir_pkg_zip, _ = _unzip_dataset(prompt, dir_pkg)
    return await file(dir_pkg_zip)


@app.route("/checkTasks", version="v1", methods=["GET"])
async def check_tasks(request: Request):
    if not _has_available_auth(request):
        return text("Access not allowed", status=403)
    # lark.send_group_msg(
    #     LarkSettings.CHAT_ID,
    #     content={"text": f"Access runtimeTask - access={request.ip} tasks={runtime_collectors}"}
    # )
    return json({"msg": "获取任务队列", "runtime": runtime_collectors})


@app.route("/", methods=["GET"])
async def home(request: Request):
    return redirect(to="https://open.spotify.com/album/5lFDNl6WwhLIIl15kyWGxw")


if __name__ == "__main__":
    app.config.TOUCHUP = False
    app.run(port=10819, host="0.0.0.0")
