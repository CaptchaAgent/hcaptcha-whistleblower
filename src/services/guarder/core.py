# -*- coding: utf-8 -*-
# Time       : 2022/7/16 7:13
# Author     : QIN2DIM
# Github     : https://github.com/QIN2DIM
# Description:
from __future__ import annotations

import os
import re
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Any

from hcaptcha_challenger import HolyChallenger
from httpx import AsyncClient
from loguru import logger
from selenium.common.exceptions import (
    ElementNotVisibleException,
    TimeoutException,
    WebDriverException,
    NoSuchElementException,
    StaleElementReferenceException,
    ElementClickInterceptedException,
    ElementNotInteractableException,
)
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait
from undetected_chromedriver import Chrome

from services.guarder.exceptions import ChallengePassed, LabelNotFoundException
from settings import project, firebird
from utils.accelerator import AshFramework
from utils.agents import get_challenge_ctx


class Guarder:
    """hCAPTCHA challenge drive control"""

    HOOK_CHALLENGE = "//iframe[contains(@title,'content')]"

    # <success> Challenge Passed by following the expected
    CHALLENGE_SUCCESS = "success"
    # <continue> Continue the challenge
    CHALLENGE_CONTINUE = "continue"
    # <crash> Failure of the challenge as expected
    CHALLENGE_CRASH = "crash"
    # <retry> Your proxy IP may have been flagged
    CHALLENGE_RETRY = "retry"
    # <refresh> Skip the specified label as expected
    CHALLENGE_REFRESH = "refresh"
    # <backcall> (New Challenge) Types of challenges not yet scheduled
    CHALLENGE_BACKCALL = "backcall"

    def __init__(self):
        self.silence = False
        # 存储挑战图片的目录
        self.runtime_workspace = ""
        # 挑战截图存储路径
        self.path_screenshot = ""

        # 博大精深！
        self.lang = "en"
        self.label_alias = firebird.focus_labels

        # Store the `element locator` of challenge images {挑战图片1: locator1, ...}
        self.alias2locator = {}
        # Store the `download link` of the challenge image {挑战图片1: url1, ...}
        self.alias2url = {}
        # Store the `directory` of challenge image {挑战图片1: "/images/挑战图片1.png", ...}
        self.alias2path = {}
        # 图像标签
        self.label = ""
        # 挑战提示
        self.prompt = ""
        # 运行缓存
        self.workspace_dir = project.workspace_dir

        self.threat = 0
        self.ctx_session = None

    def __enter__(self):
        self.ctx_session = get_challenge_ctx(silence=self.silence, lang=self.lang)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        try:
            if self.ctx_session:
                self.ctx_session.quit()
        except AttributeError:
            pass

    def flush_firebird(self, label: str):
        if label.lower().startswith("please click on "):
            logger.info("非二分类任务，跳过挑战", label=label)
            return
        map_to = diagnose_task(label)
        firebird.to_json({label: map_to})
        self.label_alias = firebird.flush()

        logger.success("将遇到的新挑战刷入运行时任务队列", label=label, map_to=map_to)

    def _init_workspace(self):
        """初始化工作目录，存放缓存的挑战图片"""
        _prefix = (
            f"{time.time()}" + f"_{self.label_alias.get(self.label, '')}" if self.label else ""
        )
        _workspace = os.path.join(self.workspace_dir, _prefix)
        os.makedirs(_workspace, exist_ok=True)
        return _workspace

    def switch_to_challenge_frame(self, ctx: Chrome) -> str:
        """
        切换挑战框架

        在 ANTI CHECKBOX 之后使用，用于判断点击检查盒后是否直接通过挑战。
        若挑战通过，退出挑战；若检测到挑战框架，则自动切入
        :param ctx:
        :return:
        """
        for _ in range(15):
            try:
                msg_obj = WebDriverWait(ctx, 1).until(
                    EC.presence_of_element_located(
                        (By.XPATH, "//div[@class='hcaptcha-success smsg']")
                    )
                )
                if msg_obj.text:
                    return self.CHALLENGE_SUCCESS
            except TimeoutException:
                pass
            try:
                WebDriverWait(ctx, 1, ignored_exceptions=(ElementNotVisibleException,)).until(
                    EC.frame_to_be_available_and_switch_to_it((By.XPATH, self.HOOK_CHALLENGE))
                )
                return self.CHALLENGE_CONTINUE
            except TimeoutException:
                pass

        # 断言超时，刷新页面
        return self.CHALLENGE_REFRESH

    def get_label(self, ctx: Chrome):
        """
        获取人机挑战需要识别的图片类型（标签）

        :param ctx:
        :return:
        """

        def label_cleaning(raw_label: str) -> str:
            """清洗误码 | 将不规则 UNICODE 字符替换成正常的英文字符"""
            clean_label = raw_label
            for c in HolyChallenger.BAD_CODE:
                clean_label = clean_label.replace(c, HolyChallenger.BAD_CODE[c])
            return clean_label

        # Scan and determine the type of challenge.
        for _ in range(3):
            try:
                label_obj = WebDriverWait(
                    ctx, 5, ignored_exceptions=(ElementNotVisibleException,)
                ).until(EC.presence_of_element_located((By.XPATH, "//h2[@class='prompt-text']")))
            except TimeoutException:
                raise ChallengePassed("Man-machine challenge unexpectedly passed")
            else:
                self.prompt = label_obj.text
                if self.prompt:
                    break
                time.sleep(1)
                continue
        # Skip the `draw challenge`
        else:
            fn = f"{int(time.time())}.image_label_area_select.png"
            logger.debug(
                "Pass challenge",
                challenge="image_label_area_select",
                site_link=ctx.current_url,
                screenshot=self.captcha_screenshot(ctx, fn),
            )
            return self.CHALLENGE_BACKCALL

        # Continue the `click challenge`
        try:
            _label = HolyChallenger.split_prompt_message(self.prompt, self.lang)
        except (AttributeError, IndexError):
            raise LabelNotFoundException("Get the exception label object")
        else:
            self.label = label_cleaning(_label)
            logger.debug("Get label", label=self.label)

    def mark_samples(self, ctx: Chrome):
        """Get the download link and locator of each challenge image"""
        # 等待图片加载完成
        try:
            WebDriverWait(ctx, 5, ignored_exceptions=(ElementNotVisibleException,)).until(
                EC.presence_of_all_elements_located((By.XPATH, "//div[@class='task-image']"))
            )
        except TimeoutException:
            pass

        time.sleep(0.3)

        # DOM 定位元素
        samples = ctx.find_elements(By.XPATH, "//div[@class='task-image']")
        for sample in samples:
            alias = sample.get_attribute("aria-label")
            while True:
                try:
                    image_style = sample.find_element(By.CLASS_NAME, "image").get_attribute("style")
                    url = re.split(r'[(")]', image_style)[2]
                    self.alias2url.update({alias: url})
                    break
                except IndexError:
                    continue
            self.alias2locator.update({alias: sample})

    def download_images(self):
        @dataclass
        class ImageDownloader(AshFramework):
            async def control_driver(self, context: Any, client: AsyncClient):
                (img_path, url) = context
                resp = await client.get(url)
                img_path.write_bytes(resp.content)

        # Initialize the challenge image download directory
        workspace_ = Path(self._init_workspace())

        # Initialize the data container
        docker_ = []
        for alias_, url_ in self.alias2url.items():
            path_challenge_img_ = workspace_.joinpath(f"{alias_}.png")
            self.alias2path.update({alias_: path_challenge_img_})
            docker_.append((path_challenge_img_, url_))

        # Initialize the coroutine-based image downloader
        start = time.time()
        ImageDownloader(docker_).execute()
        logger.debug("Download challenge images", timeit=f"{round(time.time() - start, 2)}s")

        self.runtime_workspace = workspace_

    def captcha_screenshot(self, ctx, name_screenshot: str = None):
        """
        保存挑战截图，需要在 get_label 之后执行

        :param name_screenshot: filename of the Challenge image
        :param ctx: Webdriver 或 Element
        :return:
        """
        _suffix = self.label_alias.get(self.label, self.label)
        _filename = (
            f"{int(time.time())}.{_suffix}.png" if name_screenshot is None else name_screenshot
        )
        _out_dir = os.path.join(os.path.dirname(self.workspace_dir), "captcha_screenshot")
        _out_path = os.path.join(_out_dir, _filename)
        os.makedirs(_out_dir, exist_ok=True)

        # FullWindow screenshot or FocusElement screenshot
        try:
            ctx.screenshot(_out_path)
        except AttributeError:
            ctx.save_screenshot(_out_path)
        except Exception as err:
            logger.exception("挑战截图保存失败，错误的参数类型", type=type(ctx), err=err)

        finally:
            return _out_path

    def tactical_alert(self, ctx):
        """新挑战预警"""
        logger.warning(
            "Types of challenges not yet scheduled", label=self.label, prompt=self.prompt
        )

        # 保存挑战截图 | 返回截图存储路径
        try:
            challenge_container = ctx.find_element(By.XPATH, "//body[@class='no-selection']")
            self.path_screenshot = self.captcha_screenshot(challenge_container)
        except NoSuchElementException:
            pass
        else:
            return self.path_screenshot

    def anti_checkbox(self, ctx: Chrome):
        """处理复选框"""
        for _ in range(8):
            try:
                # [👻] 进入复选框
                WebDriverWait(ctx, 2, ignored_exceptions=(ElementNotVisibleException,)).until(
                    EC.frame_to_be_available_and_switch_to_it(
                        (By.XPATH, "//iframe[contains(@title,'checkbox')]")
                    )
                )
                # [👻] 点击复选框
                WebDriverWait(ctx, 2).until(EC.element_to_be_clickable((By.ID, "checkbox"))).click()
                logger.debug("Handle hCaptcha checkbox")
                return True
            except TimeoutException:
                pass
            finally:
                # [👻] 回到主线剧情
                ctx.switch_to.default_content()

    @staticmethod
    def refresh_hcaptcha(ctx: Chrome) -> Optional[bool]:
        try:
            return ctx.find_element(By.XPATH, "//div[@class='refresh button']").click()
        except (NoSuchElementException, ElementNotInteractableException):
            return False

    def _hacking_dataset(self, ctx):
        self.get_label(ctx)
        self.mark_samples(ctx)
        self.download_images()
        self.refresh_hcaptcha(ctx)

    def hacking_dataset(self, ctx, on_worker_handler=None):
        """
        针对 FocusLabel 进行的数据集下载任务

        :param on_worker_handler:
        :param ctx:
        :return:
        """
        try:
            if on_worker_handler is None:
                self._hacking_dataset(ctx)
            else:
                on_worker_handler(ctx)
        except (ChallengePassed, ElementClickInterceptedException):
            ctx.refresh()
        except StaleElementReferenceException:
            return
        except WebDriverException as err:
            logger.exception(err)
        finally:
            ctx.switch_to.default_content()

    def checking_dataset(self, ctx):
        """
        针对 SkippedLabel 进行的数据集发现任务

        :param ctx:
        :return:
        """
        try:
            # 进入挑战框架 | 开始执行相关检测任务
            self.get_label(ctx)
            # 拉起预警服务
            if not self.label_alias.get(self.label):
                self.mark_samples(ctx)
                self.tactical_alert(ctx)
                self.flush_firebird(self.label)
                return True
            # 在内联框架中刷新挑战
            self.refresh_hcaptcha(ctx)
        except (ChallengePassed, TimeoutException):
            ctx.refresh()
        except WebDriverException as err:
            logger.exception(err)
        finally:
            ctx.switch_to.default_content()


class ArmorUtils:
    @staticmethod
    def fall_in_captcha_runtime(ctx: Chrome) -> Optional[bool]:
        """捕获隐藏在周免游戏订单中的人机挑战"""
        try:
            WebDriverWait(ctx, 5, ignored_exceptions=(WebDriverException,)).until(
                EC.presence_of_element_located((By.XPATH, "//iframe[contains(@title,'content')]"))
            )
            return True
        except TimeoutException:
            return False

    @staticmethod
    def face_the_checkbox(ctx: Chrome) -> Optional[bool]:
        """遇见 hCaptcha checkbox"""
        try:
            WebDriverWait(ctx, 8, ignored_exceptions=(WebDriverException,)).until(
                EC.presence_of_element_located((By.XPATH, "//iframe[contains(@title,'checkbox')]"))
            )
            return True
        except TimeoutException:
            return False


def diagnose_task(words: str) -> str:
    """from challenge prompt to model name"""
    origin = words
    if not words or not isinstance(words, str) or len(words) < 2:
        raise TypeError(f"({words})TASK should be string type data")

    # Filename contains illegal characters
    inv = {"\\", "/", ":", "*", "?", "<", ">", "|"}
    if s := set(words) & inv:
        raise TypeError(f"({words})TASK contains invalid characters({s})")

    # Normalized separator
    rnv = {" ", ",", "-"}
    for s in rnv:
        words = words.replace(s, "_")

    # Convert bad code
    badcode = {
        "а": "a",
        "е": "e",
        "e": "e",
        "i": "i",
        "і": "i",
        "ο": "o",
        "с": "c",
        "ԁ": "d",
        "ѕ": "s",
        "һ": "h",
        "у": "y",
        "р": "p",
    }
    for code, right_code in badcode.items():
        words.replace(code, right_code)

    words = words.strip()
    logger.debug(f"diagnose task", origin=origin, to=words)

    return words
