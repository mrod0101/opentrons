from __future__ import annotations

from enum import Enum
import asyncio

from typing import Optional, Dict
from opentrons.drivers import utils
from opentrons.drivers.command_builder import CommandBuilder
from opentrons.drivers.asyncio.communication import SerialConnection
from opentrons.drivers.heater_shaker.abstract import AbstractHeaterShakerDriver
from opentrons.drivers.types import Temperature, RPM, HeaterShakerPlateLockStatus


class GCODE(str, Enum):
    SET_RPM = "M3"
    GET_RPM = "M123"
    SET_TEMPERATURE = "M104"
    GET_TEMPERATURE = "M105"
    HOME = "G28"
    ENTER_BOOTLOADER = "dfu"
    GET_VERSION = "M115"
    OPEN_PLATE_LOCK = "M242"
    CLOSE_PLATE_LOCK = "M243"
    GET_PLATE_LOCK_STATE = "M241"


HS_BAUDRATE = 115200
DEFAULT_HS_TIMEOUT = 40
HS_COMMAND_TERMINATOR = "\n"
HS_ACK = "OK" + HS_COMMAND_TERMINATOR
HS_ERROR_KEYWORD = "err"
DEFAULT_COMMAND_RETRIES = 0


class HeaterShakerDriver(AbstractHeaterShakerDriver):
    @classmethod
    async def create(
        cls, port: str, loop: Optional[asyncio.AbstractEventLoop]
    ) -> HeaterShakerDriver:
        """
        Create a heater-shaker driver.

        Args:
            port: port or url of heater shaker
            loop: optional event loop

        Returns: driver
        """
        connection = await SerialConnection.create(
            port=port,
            baud_rate=HS_BAUDRATE,
            timeout=DEFAULT_HS_TIMEOUT,
            ack=HS_ACK,
            loop=loop,
            error_keyword=HS_ERROR_KEYWORD,
        )
        return cls(connection=connection)

    def __init__(self, connection: SerialConnection) -> None:
        """
        Constructor

        Args:
            connection: SerialConnection to the heater-shaker
        """
        self._connection = connection

    async def connect(self) -> None:
        """Connect to heater-shaker"""
        await self._connection.open()

    async def disconnect(self) -> None:
        """Disconnect from heater-shaker"""
        await self._connection.close()

    async def is_connected(self) -> bool:
        """Check connection"""
        return await self._connection.is_open()

    async def open_plate_lock(self) -> None:
        """Send open-plate-lock command"""
        c = CommandBuilder(terminator=HS_COMMAND_TERMINATOR).add_gcode(
            gcode=GCODE.OPEN_PLATE_LOCK
        )
        await self._connection.send_command(command=c, retries=DEFAULT_COMMAND_RETRIES)

    async def close_plate_lock(self) -> None:
        """Send close-plate-lock command"""
        c = CommandBuilder(terminator=HS_COMMAND_TERMINATOR).add_gcode(
            gcode=GCODE.CLOSE_PLATE_LOCK
        )
        await self._connection.send_command(command=c, retries=DEFAULT_COMMAND_RETRIES)

    async def set_temperature(self, temperature: float) -> None:
        """Set temperature"""
        c = (
            CommandBuilder(terminator=HS_COMMAND_TERMINATOR)
            .add_gcode(gcode=GCODE.SET_TEMPERATURE)
            .add_float(
                prefix="S",
                value=temperature,
                precision=utils.HS_GCODE_ROUNDING_PRECISION,
            )
        )
        await self._connection.send_command(command=c, retries=DEFAULT_COMMAND_RETRIES)

    async def get_temperature(self) -> Temperature:
        c = CommandBuilder(terminator=HS_COMMAND_TERMINATOR).add_gcode(
            gcode=GCODE.GET_TEMPERATURE
        )
        response = await self._connection.send_command(
            command=c, retries=DEFAULT_COMMAND_RETRIES
        )
        return utils.parse_temperature_response(
            temperature_string=response,
            rounding_val=utils.HS_GCODE_ROUNDING_PRECISION,
            zero_target_is_unset=True,
        )

    async def set_rpm(self, rpm: int) -> None:
        """Set RPM"""
        c = (
            CommandBuilder(terminator=HS_COMMAND_TERMINATOR)
            .add_gcode(gcode=GCODE.SET_RPM)
            .add_int(prefix="S", value=int(rpm))
        )
        await self._connection.send_command(command=c, retries=DEFAULT_COMMAND_RETRIES)

    async def get_rpm(self) -> RPM:
        """Get RPM"""
        c = CommandBuilder(terminator=HS_COMMAND_TERMINATOR).add_gcode(
            gcode=GCODE.GET_RPM
        )
        response = await self._connection.send_command(
            command=c, retries=DEFAULT_COMMAND_RETRIES
        )
        return utils.parse_rpm_response(rpm_string=response)

    async def get_plate_lock_status(self) -> HeaterShakerPlateLockStatus:
        """Send get-plate-lock-status command"""
        c = CommandBuilder(terminator=HS_COMMAND_TERMINATOR).add_gcode(
            gcode=GCODE.GET_PLATE_LOCK_STATE
        )
        response = await self._connection.send_command(
            command=c, retries=DEFAULT_COMMAND_RETRIES
        )
        return utils.parse_plate_lock_status_response(status_string=response)

    async def home(self) -> None:
        """Send home command"""
        c = CommandBuilder(terminator=HS_COMMAND_TERMINATOR).add_gcode(gcode=GCODE.HOME)
        await self._connection.send_command(command=c, retries=DEFAULT_COMMAND_RETRIES)

    async def get_device_info(self) -> Dict[str, str]:
        """Send get-device-info command"""
        c = CommandBuilder(terminator=HS_COMMAND_TERMINATOR).add_gcode(
            gcode=GCODE.GET_VERSION
        )
        response = await self._connection.send_command(
            command=c, retries=DEFAULT_COMMAND_RETRIES
        )
        return utils.parse_hs_device_information(device_info_string=response)

    async def enter_programming_mode(self) -> None:
        c = CommandBuilder(terminator=HS_COMMAND_TERMINATOR).add_gcode(
            gcode=GCODE.ENTER_BOOTLOADER
        )
        await self._connection.send_command(command=c, retries=DEFAULT_COMMAND_RETRIES)
        await self._connection.close()
