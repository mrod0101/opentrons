"""Highlight an element."""
import time
from selenium.webdriver.chrome.webdriver import WebDriver
from selenium.webdriver.remote.webelement import WebElement


def highlight(
    element: WebElement, effect_time_sec: int, color: str, border_size_px: int
) -> None:
    """Highlights (blinks) a Selenium Webdriver element."""
    driver: WebDriver = element._parent  # pylint: disable=W0212

    def apply_style(argument: str) -> None:
        """Execute the javascript to apply the style."""
        driver.execute_script(
            "arguments[0].setAttribute('style', arguments[1]);", element, argument
        )

    original_style = element.get_attribute("style")
    apply_style(f"border: {border_size_px}px solid {color};")
    time.sleep(effect_time_sec)
    apply_style(original_style)
