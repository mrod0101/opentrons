"""Model for the Robot page that displays info and settings for the robot."""
import os
from selenium.webdriver.chrome.webdriver import WebDriver
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains

from src.highlight import highlight


class RobotPage:
    """Elements and actions for the robot detail page."""

    experimental_protocol_engine_toggle_locator = (
        By.CSS_SELECTOR,
        "button[aria-label='Enable Experimental Protocol Engine']",
    )

    def __init__(self, driver: WebDriver) -> None:
        """Initialize with driver."""
        self.driver: WebDriver = driver

    def header(self, name: str) -> WebElement:
        """Get the header of the page by robot name."""
        header: WebElement = WebDriverWait(self.driver, 5000).until(
            EC.element_to_be_clickable((By.XPATH, f"//h1[text()='{name}']"))
        )
        if os.getenv("SLOWMO"):
            highlight(header, 3, "blue", 3)
        return header

    def experimental_protocol_engine_toggle(self) -> WebElement:
        """Toggle button element for the experimental protocol engine."""
        toggle: WebElement = WebDriverWait(self.driver, 5000).until(
            EC.element_to_be_clickable(
                RobotPage.experimental_protocol_engine_toggle_locator
            )
        )
        actions = ActionChains(self.driver)
        actions.move_to_element(toggle).perform()
        if os.getenv("SLOWMO"):
            highlight(toggle, 3, "blue", 3)
        return toggle
