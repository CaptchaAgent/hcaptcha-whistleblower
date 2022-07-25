# -*- coding: utf-8 -*-
# Time       : 2022/7/16 7:13
# Author     : QIN2DIM
# Github     : https://github.com/QIN2DIM
# Description:
import asyncio
import os
import re
import sys
import time
from typing import Optional

from selenium.common.exceptions import (
    ElementNotVisibleException,
    TimeoutException,
    WebDriverException,
    NoSuchElementException,
    StaleElementReferenceException,
    ElementClickInterceptedException,
)
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait
from undetected_chromedriver import Chrome

from services.settings import logger
from services.utils import AshFramework, ToolBox, get_challenge_ctx
from .exceptions import ChallengePassed, LabelNotFoundException, ChallengeLangException


class Guarder:
    """hCAPTCHA challenge drive control"""

    label_alias = {
        "zh": {
            "自行车": "bicycle",
            "火车": "train",
            "卡车": "truck",
            "公交车": "bus",
            "巴土": "bus",
            "巴士": "bus",
            "飞机": "airplane",
            "ー条船": "boat",
            "一条船": "boat",
            "船": "boat",
            "摩托车": "motorcycle",
            "垂直河流": "vertical river",
            "天空中向左飞行的飞机": "airplane in the sky flying left",
            "请选择天空中所有向右飞行的飞机": "airplanes in the sky that are flying to the right",
            "请选择所有用树叶画的大象": "elephants drawn with leaves",
            "水上飞机": "seaplane",
            "汽车": "car",
            "家猫": "domestic cat",
            "卧室": "bedroom",
            "桥梁": "bridge",
            "狮子": "lion",
            "客厅": "living room",
            "一匹马": "horse",
            "会议室": "conference room",
            "微笑狗": "smiling dog",
            "狗": "dog",
            # "长颈鹿": "giraffe",
        },
        "en": {
            "airplane": "airplane",
            "motorbus": "bus",
            "bus": "bus",
            "truck": "truck",
            "motorcycle": "motorcycle",
            "boat": "boat",
            "bicycle": "bicycle",
            "train": "train",
            "vertical river": "vertical river",
            "airplane in the sky flying left": "airplane in the sky flying left",
            "Please select all airplanes in the sky that are flying to the right": "airplanes in the sky that are flying to the right",
            "Please select all the elephants drawn with leaves": "elephants drawn with leaves",
            "seaplane": "seaplane",
            "car": "car",
            "domestic cat": "domestic cat",
            "bedroom": "bedroom",
            "lion": "lion",
            "bridge": "bridge",
            "living room": "living room",
            "horse": "horse",
            "conference room": "conference room",
            "smiling dog": "smiling dog",
            "dog": "dog",
            # "giraffe": "giraffe",
        },
    }

    # 左错右对
    BAD_CODE = {
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
    }
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

    def __init__(
        self,
        dir_workspace: str = None,
        lang: Optional[str] = "en",
        debug=False,
        silence: Optional[bool] = True,
    ):
        if not isinstance(lang, str) or not self.label_alias.get(lang):
            raise ChallengeLangException(
                f"Challenge language [{lang}] not yet supported."
                f" -lang={list(self.label_alias.keys())}"
            )

        self.action_name = "ArmorCaptcha"
        self.debug = debug
        self.silence = silence

        # 存储挑战图片的目录
        self.runtime_workspace = ""
        # 挑战截图存储路径
        self.path_screenshot = ""

        # 博大精深！
        self.lang = lang
        self.label_alias: dict = self.label_alias[lang]

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
        self.dir_workspace = dir_workspace if dir_workspace else "."

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

        logger.success(
            ToolBox.runtime_report(
                motive="OFFLOAD",
                action_name=self.action_name,
                message=f"Offload {self.action_name} units",
            )
        )

    def _init_workspace(self):
        """初始化工作目录，存放缓存的挑战图片"""
        _prefix = (
            f"{time.time()}" + f"_{self.label_alias.get(self.label, '')}" if self.label else ""
        )
        _workspace = os.path.join(self.dir_workspace, _prefix)
        os.makedirs(_workspace, exist_ok=True)
        return _workspace

    def log(self, message: str, **params) -> None:
        """格式化日志信息"""
        if not self.debug:
            return

        motive = "Challenge"
        flag_ = f">> {motive} [{self.action_name}] {message}"
        if params:
            flag_ += " - "
            flag_ += " ".join([f"{i[0]}={i[1]}" for i in params.items()])
        logger.debug(flag_)

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
                WebDriverWait(ctx, 1, ignored_exceptions=ElementNotVisibleException).until(
                    EC.frame_to_be_available_and_switch_to_it((By.XPATH, self.HOOK_CHALLENGE))
                )
                return self.CHALLENGE_CONTINUE
            except TimeoutException:
                pass

        # 断言超时，刷新页面
        return self.CHALLENGE_REFRESH

    def get_label(self, ctx: Chrome):
        def split_prompt_message(prompt_message: str) -> str:
            """根据指定的语种在提示信息中分离挑战标签"""
            labels_mirror = {
                "zh": re.split(r"[包含 图片]", prompt_message)[2][:-1]
                if "包含" in prompt_message
                else prompt_message,
                "en": re.split(r"containing a", prompt_message)[-1][1:].strip()
                if "containing" in prompt_message
                else prompt_message,
            }
            return labels_mirror[self.lang]

        def label_cleaning(raw_label: str) -> str:
            """清洗误码 | 将不规则 UNICODE 字符替换成正常的英文字符"""
            clean_label = raw_label
            for c in self.BAD_CODE:
                clean_label = clean_label.replace(c, self.BAD_CODE[c])
            return clean_label

        # Necessary.
        time.sleep(0.5)

        # Wait for the element to fully load.
        try:
            label_obj = WebDriverWait(ctx, 5, ignored_exceptions=ElementNotVisibleException).until(
                EC.presence_of_element_located((By.XPATH, "//h2[@class='prompt-text']"))
            )
        except TimeoutException:
            raise ChallengePassed("人机挑战意外通过")
        else:
            self.prompt = label_obj.text

        # Get Challenge Prompt.
        try:
            _label = split_prompt_message(prompt_message=self.prompt)
        except (AttributeError, IndexError):
            raise LabelNotFoundException("获取到异常的标签对象。")
        else:
            self.label = label_cleaning(_label)
            self.log(message="Get label", label=f"「{self.label}」")

    def mark_samples(self, ctx: Chrome):
        # 等待图片加载完成
        WebDriverWait(ctx, 10, ignored_exceptions=ElementNotVisibleException).until(
            EC.presence_of_all_elements_located((By.XPATH, "//div[@class='task-image']"))
        )
        time.sleep(1)

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
        class ImageDownloader(AshFramework):
            """Coroutine Booster - Improve the download efficiency of challenge images"""

            async def control_driver(self, context, session=None):
                path_challenge_img, url = context

                # Download Challenge Image
                async with session.get(url) as response:
                    with open(path_challenge_img, "wb") as file:
                        file.write(await response.read())

        # Initialize the challenge image download directory
        workspace_ = self._init_workspace()

        # Initialize the data container
        docker_ = []
        for alias_, url_ in self.alias2url.items():
            path_challenge_img_ = os.path.join(workspace_, f"{alias_}.png")
            self.alias2path.update({alias_: path_challenge_img_})
            docker_.append((path_challenge_img_, url_))

        # Initialize the coroutine-based image downloader
        start = time.time()
        if sys.platform.startswith("win") or "cygwin" in sys.platform:
            asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
            asyncio.run(ImageDownloader(docker=docker_).subvert(workers="fast"))
        else:
            loop = asyncio.get_event_loop()
            loop.run_until_complete(ImageDownloader(docker=docker_).subvert(workers="fast"))
        self.log(message="Download challenge images", timeit=f"{round(time.time() - start, 2)}s")

        self.runtime_workspace = workspace_

    def captcha_screenshot(self, ctx):
        """
        保存挑战截图，需要在 get_label 之后执行

        :param ctx: Webdriver 或 Element
        :return:
        """
        _suffix = self.label_alias.get(self.label, self.label)
        _filename = f"{int(time.time())}.{_suffix}.png"
        _out_dir = os.path.join(os.path.dirname(self.dir_workspace), "captcha_screenshot")
        _out_path = os.path.join(_out_dir, _filename)
        os.makedirs(_out_dir, exist_ok=True)

        # FullWindow screenshot or FocusElement screenshot
        try:
            ctx.screenshot(_out_path)
        except AttributeError:
            ctx.save_screenshot(_out_path)
        except Exception as err:
            logger.exception(
                ToolBox.runtime_report(
                    motive="SCREENSHOT",
                    action_name=self.action_name,
                    message="挑战截图保存失败，错误的参数类型",
                    type=type(ctx),
                    err=err,
                )
            )
        finally:
            return _out_path

    def tactical_alert(self, ctx):
        """新挑战预警"""
        logger.warning(
            ToolBox.runtime_report(
                motive="ALERT",
                action_name=self.action_name,
                message="Types of challenges not yet scheduled",
                label=f"「{self.label}」",
                prompt=f"「{self.prompt}」",
            )
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
                WebDriverWait(ctx, 2, ignored_exceptions=ElementNotVisibleException).until(
                    EC.frame_to_be_available_and_switch_to_it(
                        (By.XPATH, "//iframe[contains(@title,'checkbox')]")
                    )
                )
                # [👻] 点击复选框
                WebDriverWait(ctx, 2).until(EC.element_to_be_clickable((By.ID, "checkbox"))).click()
                self.log("Handle hCaptcha checkbox")
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
        except NoSuchElementException:
            return False

    def hacking_dataset(self, ctx):
        """
        针对 FocusLabel 进行的数据集下载任务

        :param ctx:
        :return:
        """
        try:
            self.get_label(ctx)
            self.mark_samples(ctx)
            self.download_images()
            self.refresh_hcaptcha(ctx)
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
                return self.tactical_alert(ctx)
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
            WebDriverWait(ctx, 5, ignored_exceptions=WebDriverException).until(
                EC.presence_of_element_located((By.XPATH, "//iframe[contains(@title,'content')]"))
            )
            return True
        except TimeoutException:
            return False

    @staticmethod
    def face_the_checkbox(ctx: Chrome) -> Optional[bool]:
        """遇见 hCaptcha checkbox"""
        try:
            WebDriverWait(ctx, 8, ignored_exceptions=WebDriverException).until(
                EC.presence_of_element_located((By.XPATH, "//iframe[contains(@title,'checkbox')]"))
            )
            return True
        except TimeoutException:
            return False
