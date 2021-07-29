"""Test the initial state the application with various setups."""
import logging
import os
from typing import Any
import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

from src.menus.left_menu import LeftMenu
from src.menus.robots_list import RobotsList
from src.menus.protocol_file import ProtocolFile
from src.resources.ot_robot import OtRobot
from src.pages.overview import Overview
from src.resources.system_file_dialog import input_file_source

logger = logging.getLogger(__name__)


def test_calibrate(
    calibrate: Any, chrome_options: Options, protocols: dict  # pylint: disable=W0613
) -> None:
    """Upload a protocol."""
    robot = OtRobot()
    # expecting docker emulated robot
    assert robot.is_alive(), "is a robot available?"
    # use variable to prevent the popup
    os.environ["OT_APP_ANALYTICS__SEEN_OPT_IN"] = "true"
    with webdriver.Chrome(options=chrome_options) as driver:
        robots_list = RobotsList(driver)
        if not robots_list.is_robot_toggle_active(RobotsList.DEV):
            robots_list.get_robot_toggle(RobotsList.DEV).click()
        left_menu = LeftMenu(driver)
        left_menu.click_protocol_upload_button()
        protocol_file = ProtocolFile(driver)
        protocol_file.get_open_button().click()
        time.sleep(1)
        logger.info(f"uploading protocol: {protocols['python1'].resolve()}")
        input_file_source(protocols["python1"])
        time.sleep(1)
        overview = Overview(driver)
        overview.click_continue_if_present()
        overview.get_filename_header(protocols["python1"].name)
