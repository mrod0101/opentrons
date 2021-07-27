"""Test the initial state the application with various setups."""
import logging
import os
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options

from src.ot_robot import OtRobot

logger = logging.getLogger(__name__)


def test_initial_load(chrome_options: Options) -> None:
    """Test the initail load of the app with docker emulated robot."""
    robot = OtRobot()
    # expecting docker emulated robot
    assert robot.is_alive(), "is a robot available?"
    # use variables to prevent the popup
    os.environ["OT_APP_ANALYTICS__SEEN_OPT_IN"] = "true"
    with webdriver.Chrome(options=chrome_options) as driver:
        print(driver.current_window_handle)
        element = WebDriverWait(driver, 5000).until(
            EC.element_to_be_clickable((By.XPATH, '//a[contains(@href,"dev")]//button'))
        )
        element.click()
        driver.find_element(By.XPATH, '//a[contains(@href,"dev")]//button')
        element = WebDriverWait(driver, 5000).until(
            EC.element_to_be_clickable((By.XPATH, '//a[contains(@href,"#/more")]'))
        )
        element.click()
        time.sleep(5)
