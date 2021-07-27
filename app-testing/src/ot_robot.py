"""Model the the Opentrons Robot."""
import logging
import os
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import requests

logger = logging.getLogger(__name__)


class OtRobot:
    """Opentrons Robot."""

    RETRIES = 5
    BACK_OFF_FACTOR = 0.3
    TIME_BETWEEN_RETRIES = 1000
    ERROR_CODES = (500, 502, 503, 504)

    def __init__(
        self,
        ip_address: str = os.getenv("ROBOT_IP"),
        port: str = os.getenv("ROBOT_PORT"),
    ) -> None:
        """Initialize the robot."""
        self.ip_address: str = ip_address
        self.port: str = port
        self.alive: bool = None
        session = requests.session()
        retry = Retry(
            total=OtRobot.RETRIES,
            read=OtRobot.RETRIES,
            connect=OtRobot.RETRIES,
            backoff_factor=OtRobot.BACK_OFF_FACTOR,
            status_forcelist=OtRobot.ERROR_CODES,
        )
        adapter = HTTPAdapter(max_retries=retry)
        session.mount("http://", adapter)
        self.session: requests.Session = session

    def is_alive(self) -> bool:
        """Is a robot available by http - request the openapi.json."""
        try:
            response: requests.Response = self.session.get(
                f"http://{self.ip_address}:{self.port}/openapi.json"
            )
            if response.status_code == 200:
                self.alive = True
                return self.alive
        except requests.exceptions.ConnectionError as error:
            logger.error(error)
        self.alive = False
        return self.alive
