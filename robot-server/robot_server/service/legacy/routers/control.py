import asyncio

from fastapi import APIRouter, Query, Depends
from starlette import status

from opentrons.hardware_control import (
    ThreadManager,
    ThreadedAsyncLock,
    ThreadedAsyncForbidden,
)
from opentrons.hardware_control.types import Axis, CriticalPoint
from opentrons.types import Mount, Point

from robot_server.errors import LegacyErrorResponse
from robot_server.service.dependencies import get_hardware, get_motion_lock
from robot_server.service.legacy.models import V1BasicResponse
from robot_server.service.legacy.models import control

router = APIRouter()


@router.post(
    "/identify",
    description="Blink the OT-2's gantry lights so you can pick it " "out of a crowd",
)
async def post_identify(
    seconds: int = Query(..., description="Time to blink the lights for"),
    hardware: ThreadManager = Depends(get_hardware),
) -> V1BasicResponse:
    identify = hardware.identify
    asyncio.ensure_future(identify(seconds))
    return V1BasicResponse(message="identifying")


@router.get(
    "/robot/positions",
    description="Get a list of useful positions",
    response_model=control.RobotPositionsResponse,
)
async def get_robot_positions() -> control.RobotPositionsResponse:
    """
    Positions determined experimentally by issuing move commands. Change
    pipette position offsets the mount to the left or right such that a user
    can easily access the pipette mount screws with a screwdriver. Attach tip
    position places either pipette roughly in the front-center of the deck area
    """
    robot_positions = control.RobotPositions(
        change_pipette=control.ChangePipette(
            target=control.MotionTarget.mount, left=[300, 40, 30], right=[95, 40, 30]
        ),
        attach_tip=control.AttachTip(
            target=control.MotionTarget.pipette, point=[200, 90, 150]
        ),
    )
    return control.RobotPositionsResponse(positions=robot_positions)


@router.post(
    path="/robot/move",
    description=(
        "Move the robot's gantry to a position (usually to a "
        "position retrieved from GET /robot/positions)"
    ),
    response_model=V1BasicResponse,
    responses={
        status.HTTP_403_FORBIDDEN: {"model": LegacyErrorResponse},
    },
)
async def post_move_robot(
    robot_move_target: control.RobotMoveTarget,
    hardware: ThreadManager = Depends(get_hardware),
    motion_lock: ThreadedAsyncLock = Depends(get_motion_lock),
) -> V1BasicResponse:
    """Move the robot"""
    try:
        async with motion_lock.forbid():
            pos = await _do_move(hardware=hardware, robot_move_target=robot_move_target)
            return V1BasicResponse(message=f"Move complete. New position: {pos}")
    except ThreadedAsyncForbidden as e:
        raise LegacyErrorResponse(message=str(e)).as_error(status.HTTP_403_FORBIDDEN)


@router.post(
    path="/robot/home",
    description="Home the robot",
    response_model=V1BasicResponse,
    responses={
        status.HTTP_400_BAD_REQUEST: {"model": LegacyErrorResponse},
        status.HTTP_403_FORBIDDEN: {"model": LegacyErrorResponse},
    },
)
async def post_home_robot(
    robot_home_target: control.RobotHomeTarget,
    hardware: ThreadManager = Depends(get_hardware),
    motion_lock: ThreadedAsyncLock = Depends(get_motion_lock),
) -> V1BasicResponse:
    """Home the robot or one of the pipettes"""
    try:
        async with motion_lock.forbid():
            mount = robot_home_target.mount
            target = robot_home_target.target

            home = hardware.home
            home_plunger = hardware.home_plunger

            if target == control.HomeTarget.pipette and mount:
                await home([Axis.by_mount(Mount[mount.upper()])])
                await home_plunger(Mount[mount.upper()])
                message = f"Pipette on {mount} homed successfully"
            elif target == control.HomeTarget.robot:
                await home()
                message = "Homing robot."
            else:
                raise LegacyErrorResponse(message=f"{target} is invalid").as_error(
                    status.HTTP_400_BAD_REQUEST
                )

            return V1BasicResponse(message=message)
    except ThreadedAsyncForbidden as e:
        raise LegacyErrorResponse(message=str(e)).as_error(status.HTTP_403_FORBIDDEN)


@router.get(
    "/robot/lights",
    description="Get the current status of the OT-2's rail lights",
    response_model=control.RobotLightState,
)
async def get_robot_light_state(
    hardware: ThreadManager = Depends(get_hardware),
) -> control.RobotLightState:
    light_state = hardware.get_lights()
    return control.RobotLightState(on=light_state.get("rails", False))


@router.post(
    "/robot/lights",
    description="Turn the rail lights on or off",
    response_model=control.RobotLightState,
)
async def post_robot_light_state(
    robot_light_state: control.RobotLightState,
    hardware: ThreadManager = Depends(get_hardware),
) -> control.RobotLightState:
    await hardware.set_lights(rails=robot_light_state.on)
    return robot_light_state


async def _do_move(hardware: ThreadManager, robot_move_target: control.RobotMoveTarget):
    """Perform the move"""

    await hardware.cache_instruments()

    critical_point = None
    if robot_move_target.target == control.MotionTarget.mount:
        critical_point = CriticalPoint.MOUNT

    mount = Mount[robot_move_target.mount.upper()]
    target_pos = Point(*robot_move_target.point)

    # Reset z position
    await hardware.home_z()

    pos = await hardware.gantry_position(mount, critical_point=critical_point)
    # Move to requested x, y and current z position
    await hardware.move_to(
        mount,
        Point(x=target_pos.x, y=target_pos.y, z=pos.z),
        critical_point=critical_point,
    )
    # Move to requested z position
    await hardware.move_to(mount, target_pos, critical_point=critical_point)
    return await hardware.gantry_position(mount)
