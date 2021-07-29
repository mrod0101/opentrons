"""Test the initial state the application with various setups."""
import logging
import os
from pathlib import Path

from selenium import webdriver
from selenium.webdriver.chrome.options import Options

from src.menus.left_menu import LeftMenu
from src.menus.robots_list import RobotsList
from src.menus.more_menu import MoreMenu
from src.menus.more_menu import MenuItems
from src.pages.robot_page import RobotPage
from src.resources.ot_robot import OtRobot
from src.resources.ot_application import OtApplication

logger = logging.getLogger(__name__)


def test_initial_load_docker_robot(chrome_options: Options) -> None:
    """Test the initail load of the app with docker emulated robot."""
    robot = OtRobot()
    # expecting docker emulated robot
    assert robot.is_alive(), "is a robot available?"
    # use variable to prevent the popup
    os.environ["OT_APP_ANALYTICS__SEEN_OPT_IN"] = "true"
    with webdriver.Chrome(options=chrome_options) as driver:
        logger.info(f"driver capabilities {driver.capabilities}")
        ot_application = OtApplication(
            Path(f"{driver.capabilities['chrome']['userDataDir']}/config.json")
        )
        logger.info(ot_application.config)
        robots_list = RobotsList(driver)
        if not robots_list.is_robot_toggle_active(RobotsList.DEV):
            robots_list.get_robot_toggle(RobotsList.DEV).click()
        robot_page = RobotPage(driver)
        robot_page.header(robots_list.DEV)
        robot_page.experimental_protocol_engine_toggle()
        robots_list.get_robot_pipettes_link(RobotsList.DEV).click()
        robots_list.get_robot_modules_link(RobotsList.DEV).click()


def test_initial_load_no_robot(chrome_options: Options) -> None:
    """Test the initail load of the app with NO docker emulated robot.

    Note that this test takes > 30 seconds to validate spinner stops after 30.
    """
    # app cannot see docker robot
    os.environ["OT_APP_DISCOVERY__CANDIDATES"] = ""
    # use variable to prevent the popup
    os.environ["OT_APP_ANALYTICS__SEEN_OPT_IN"] = "true"
    with webdriver.Chrome(options=chrome_options) as driver:
        logger.info(f"driver capabilities {driver.capabilities}")
        ot_application = OtApplication(
            Path(f"{driver.capabilities['chrome']['userDataDir']}/config.json")
        )
        logger.info(ot_application.config)
        robots_list = RobotsList(driver)
        robots_list.wait_for_spinner_visible()
        robots_list.wait_for_spinner_invisible()
        robots_list.get_no_robots_found()
        robots_list.get_try_again_button()


def test_more_menu_no_robot(chrome_options: Options) -> None:
    """Test the more menu with no docker emulated robot."""
    # app cannot see docker robot
    os.environ["OT_APP_DISCOVERY__CANDIDATES"] = ""
    # use variable to prevent the popup
    os.environ["OT_APP_ANALYTICS__SEEN_OPT_IN"] = "true"
    with webdriver.Chrome(options=chrome_options) as driver:
        logger.info(f"driver capabilities {driver.capabilities}")
        ot_application = OtApplication(
            Path(f"{driver.capabilities['chrome']['userDataDir']}/config.json")
        )
        logger.info(ot_application.config)
        left_menu = LeftMenu(driver)
        left_menu.click_more_button()
        more_menu = MoreMenu(driver)
        for link in MenuItems.__reversed__():
            more_menu.click_menu_link(link)
