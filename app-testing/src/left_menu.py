"""Left Menu Locators."""
from selenium.webdriver.common.by import By


class LeftMenu:
    """Locators for the left side menu."""

    robot: tuple = (By.XPATH, '//a[contains(@href,"#/robots")]')
    protocol: tuple = (By.XPATH, '//a[contains(@href,"#/protocol")]')
    calibrate: tuple = (By.XPATH, '//a[contains(@href,"#/calibrate")]')
    more: tuple = (By.XPATH, '//a[contains(@href,"#/more")]')
