"""Test the initial state the application with various setups."""
import logging
import os
from pathlib import Path
from selenium import webdriver

from selenium.webdriver.chrome.options import Options

from src.ot_robot import OtRobot
from src.robots_list import RobotsList
from src.robot_page import RobotPage
from src.ot_application import OtApplication

logger = logging.getLogger(__name__)


def test_initial_load_docker_robot(chrome_options: Options) -> None:
    """Test the initail load of the app with docker emulated robot."""
    robot = OtRobot()
    # expecting docker emulated robot
    assert robot.is_alive(), "is a robot available?"
    # use variables to prevent the popup
    os.environ["OT_APP_ANALYTICS__SEEN_OPT_IN"] = "true"
    with webdriver.Chrome(options=chrome_options) as driver:
        logger.info(f"driver capabilities {driver.capabilities}")
        ot_application = OtApplication(
            Path(f"{driver.capabilities['chrome']['userDataDir']}/config.json")
        )
        logger.info(ot_application.config)
        robots_list = RobotsList(driver)
        if not robots_list.is_robot_toggle_active_by_name(RobotsList.DEV):
            robots_list.get_robot_toggle_by_name(RobotsList.DEV).click()
        robot_page = RobotPage(driver)
        robot_page.header(robots_list.DEV)
        robot_page.experimental_protocol_engine_toggle()
