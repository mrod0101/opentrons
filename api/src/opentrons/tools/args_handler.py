import argparse
from typing import Tuple, cast

from opentrons.hardware_control import API, Controller
from opentrons.drivers.smoothie_drivers import SmoothieDriver


def root_argparser(description: str = None):
    parse = argparse.ArgumentParser(description=description)
    parse.add_argument(
        "-p", "--port", help="serial port of the smoothie", default="", type=str
    )
    return parse


async def build_driver(port: str = None) -> Tuple[API, SmoothieDriver]:
    hardware = await API.build_hardware_controller(port=port)
    backend: Controller = cast(Controller, hardware._backend)
    return hardware, backend._smoothie_driver
