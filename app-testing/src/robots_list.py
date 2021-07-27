"""Model for the list of robots."""
import os
from selenium.webdriver.chrome.webdriver import WebDriver
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from src.highlight import highlight


def get_robot_toggle_selector_by_name(name: str) -> tuple:
    """Get the locator tuple for a robot's toggle by name of the robot."""
    return (By.XPATH, f"//a[contains(@href,{name})]//button")


class RobotsList:
    """All elements and actions for the Robots List."""

    DEV = "dev"
    spinner: tuple = (By.CSS_SELECTOR, "svg[class*=spin]")
    header: tuple = (By.XPATH, '//h2[text()="Robots"]')
    refresh_list: tuple = (By.CSS_SELECTOR, '//button[text()="refresh list"]')

    def __init__(self, driver: WebDriver) -> None:
        """Initialize with driver."""
        self.driver: WebDriver = driver

    def is_robot_toggle_active_by_name(self, name: str) -> bool:
        """Is a toggle for a robot 'on' using the name of the robot."""
        return (
            self.get_robot_toggle_by_name(name).get_attribute("class").find("_on_")
            != -1
        )

    def get_robot_toggle_by_name(self, name: str) -> WebElement:
        """Retrieve the Webelement toggle buttone for a robot by name."""
        toggle_locator: tuple = get_robot_toggle_selector_by_name(name)
        toggle: WebElement = WebDriverWait(self.driver, 5000).until(
            EC.element_to_be_clickable(toggle_locator)
        )
        if os.getenv("SLOWMO"):
            highlight(toggle, 3, "blue", 3)
        return toggle
