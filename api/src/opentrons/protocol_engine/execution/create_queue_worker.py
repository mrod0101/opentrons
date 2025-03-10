"""QueueWorker and dependency factory."""
from opentrons.hardware_control.api import API as HardwareAPI

from ..state import StateStore
from ..actions import ActionDispatcher
from .equipment import EquipmentHandler
from .movement import MovementHandler
from .pipetting import PipettingHandler
from .run_control import RunControlHandler
from .command_executor import CommandExecutor
from .queue_worker import QueueWorker


def create_queue_worker(
    hardware_api: HardwareAPI,
    state_store: StateStore,
    action_dispatcher: ActionDispatcher,
) -> QueueWorker:
    """Create a ready-to-use QueueWorker instance.

    Arguments:
        hardware_api: Hardware control API to pass down to dependencies.
        state_store: StateStore to pass down to dependencies.
        action_dispatcher: ActionDispatcher to pass down to dependencies.
    """
    equipment_handler = EquipmentHandler(
        hardware_api=hardware_api,
        state_store=state_store,
    )

    movement_handler = MovementHandler(
        hardware_api=hardware_api,
        state_store=state_store,
    )

    pipetting_handler = PipettingHandler(
        hardware_api=hardware_api,
        state_store=state_store,
        movement_handler=movement_handler,
    )

    run_control_handler = RunControlHandler(
        state_store=state_store,
        action_dispatcher=action_dispatcher,
    )

    command_executor = CommandExecutor(
        state_store=state_store,
        action_dispatcher=action_dispatcher,
        equipment=equipment_handler,
        movement=movement_handler,
        pipetting=pipetting_handler,
        run_control=run_control_handler,
    )

    return QueueWorker(
        state_store=state_store,
        command_executor=command_executor,
    )
