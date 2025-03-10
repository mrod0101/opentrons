"""Smoke tests for the CommandExecutor class."""
import pytest
from datetime import datetime
from decoy import Decoy, matchers
from pydantic import BaseModel
from typing import Any, Optional, Type, cast

from opentrons.protocol_engine import errors
from opentrons.protocol_engine.resources import ModelUtils
from opentrons.protocol_engine.state import StateStore
from opentrons.protocol_engine.actions import (
    ActionDispatcher,
    UpdateCommandAction,
    FailCommandAction,
)

from opentrons.protocol_engine.commands import (
    AbstractCommandImpl,
    BaseCommand,
    CommandStatus,
    Command,
)

from opentrons.protocol_engine.execution import (
    CommandExecutor,
    EquipmentHandler,
    MovementHandler,
    PipettingHandler,
    RunControlHandler,
)


@pytest.fixture
def state_store(decoy: Decoy) -> StateStore:
    """Get a mocked out StateStore."""
    return decoy.mock(cls=StateStore)


@pytest.fixture
def action_dispatcher(decoy: Decoy) -> ActionDispatcher:
    """Get a mocked out ActionDispatcher."""
    return decoy.mock(cls=ActionDispatcher)


@pytest.fixture
def equipment(decoy: Decoy) -> EquipmentHandler:
    """Get a mocked out EquipmentHandler."""
    return decoy.mock(cls=EquipmentHandler)


@pytest.fixture
def movement(decoy: Decoy) -> MovementHandler:
    """Get a mocked out MovementHandler."""
    return decoy.mock(cls=MovementHandler)


@pytest.fixture
def pipetting(decoy: Decoy) -> PipettingHandler:
    """Get a mocked out PipettingHandler."""
    return decoy.mock(cls=PipettingHandler)


@pytest.fixture
def run_control(decoy: Decoy) -> RunControlHandler:
    """Get a mocked out RunControlHandler."""
    return decoy.mock(cls=RunControlHandler)


@pytest.fixture
def model_utils(decoy: Decoy) -> ModelUtils:
    """Get a mocked out ModelUtils."""
    return decoy.mock(cls=ModelUtils)


@pytest.fixture
def subject(
    state_store: StateStore,
    action_dispatcher: ActionDispatcher,
    equipment: EquipmentHandler,
    movement: MovementHandler,
    pipetting: PipettingHandler,
    run_control: RunControlHandler,
    model_utils: ModelUtils,
) -> CommandExecutor:
    """Get a CommandExecutor test subject with its dependencies mocked out."""
    return CommandExecutor(
        state_store=state_store,
        action_dispatcher=action_dispatcher,
        equipment=equipment,
        movement=movement,
        pipetting=pipetting,
        run_control=run_control,
        model_utils=model_utils,
    )


class _TestCommandParams(BaseModel):
    foo: str = "foo"


class _TestCommandResult(BaseModel):
    bar: str = "bar"


class _TestCommandImpl(AbstractCommandImpl[_TestCommandParams, _TestCommandResult]):
    async def execute(self, params: _TestCommandParams) -> _TestCommandResult:
        raise NotImplementedError()


async def test_execute(
    decoy: Decoy,
    state_store: StateStore,
    action_dispatcher: ActionDispatcher,
    equipment: EquipmentHandler,
    movement: MovementHandler,
    pipetting: PipettingHandler,
    run_control: RunControlHandler,
    model_utils: ModelUtils,
    subject: CommandExecutor,
) -> None:
    """It should be able execute a command."""
    TestCommandImplCls = decoy.mock(func=_TestCommandImpl)
    command_impl = decoy.mock(cls=_TestCommandImpl)

    class _TestCommand(BaseCommand[_TestCommandParams, _TestCommandResult]):
        commandType: str = "testCommand"
        params: _TestCommandParams
        result: Optional[_TestCommandResult]

        @property
        def _ImplementationCls(self) -> Type[_TestCommandImpl]:
            return TestCommandImplCls

    command_params = _TestCommandParams()
    command_result = _TestCommandResult()

    queued_command = cast(
        Command,
        _TestCommand(
            id="command-id",
            createdAt=datetime(year=2021, month=1, day=1),
            status=CommandStatus.QUEUED,
            params=command_params,
        ),
    )

    running_command = cast(
        Command,
        _TestCommand(
            id="command-id",
            createdAt=datetime(year=2021, month=1, day=1),
            startedAt=datetime(year=2022, month=2, day=2),
            status=CommandStatus.RUNNING,
            params=command_params,
        ),
    )

    completed_command = cast(
        Command,
        _TestCommand(
            id="command-id",
            createdAt=datetime(year=2021, month=1, day=1),
            startedAt=datetime(year=2022, month=2, day=2),
            completedAt=datetime(year=2023, month=3, day=3),
            status=CommandStatus.SUCCEEDED,
            params=command_params,
            result=command_result,
        ),
    )

    decoy.when(state_store.commands.get(command_id="command-id")).then_return(
        queued_command
    )

    decoy.when(
        queued_command._ImplementationCls(
            equipment=equipment,
            movement=movement,
            pipetting=pipetting,
            run_control=run_control,
        )
    ).then_return(
        command_impl  # type: ignore[arg-type]
    )

    decoy.when(await command_impl.execute(command_params)).then_return(command_result)

    decoy.when(model_utils.get_timestamp()).then_return(
        datetime(year=2022, month=2, day=2),
        datetime(year=2023, month=3, day=3),
    )

    await subject.execute("command-id")

    decoy.verify(
        action_dispatcher.dispatch(UpdateCommandAction(command=running_command)),
        action_dispatcher.dispatch(UpdateCommandAction(command=completed_command)),
    )


@pytest.mark.parametrize(
    ["command_error", "expected_error"],
    [
        (
            errors.ProtocolEngineError("oh no"),
            matchers.ErrorMatching(errors.ProtocolEngineError, match="oh no"),
        ),
        (
            RuntimeError("oh no"),
            matchers.ErrorMatching(errors.UnexpectedProtocolError, match="oh no"),
        ),
    ],
)
async def test_execute_raises_protocol_engine_error(
    decoy: Decoy,
    state_store: StateStore,
    action_dispatcher: ActionDispatcher,
    equipment: EquipmentHandler,
    movement: MovementHandler,
    pipetting: PipettingHandler,
    run_control: RunControlHandler,
    model_utils: ModelUtils,
    subject: CommandExecutor,
    command_error: Exception,
    expected_error: Any,
) -> None:
    """It should handle an error occuring during execution."""
    TestCommandImplCls = decoy.mock(func=_TestCommandImpl)
    command_impl = decoy.mock(cls=_TestCommandImpl)

    class _TestCommand(BaseCommand[_TestCommandParams, _TestCommandResult]):
        commandType: str = "testCommand"
        params: _TestCommandParams
        result: Optional[_TestCommandResult]

        @property
        def _ImplementationCls(self) -> Type[_TestCommandImpl]:
            return TestCommandImplCls

    command_params = _TestCommandParams()

    queued_command = cast(
        Command,
        _TestCommand(
            id="command-id",
            createdAt=datetime(year=2021, month=1, day=1),
            status=CommandStatus.QUEUED,
            params=command_params,
        ),
    )

    running_command = cast(
        Command,
        _TestCommand(
            id="command-id",
            createdAt=datetime(year=2021, month=1, day=1),
            startedAt=datetime(year=2022, month=2, day=2),
            status=CommandStatus.RUNNING,
            params=command_params,
        ),
    )

    decoy.when(state_store.commands.get(command_id="command-id")).then_return(
        queued_command
    )

    decoy.when(
        queued_command._ImplementationCls(
            equipment=equipment,
            movement=movement,
            pipetting=pipetting,
            run_control=run_control,
        )
    ).then_return(
        command_impl  # type: ignore[arg-type]
    )

    decoy.when(await command_impl.execute(command_params)).then_raise(command_error)

    decoy.when(model_utils.generate_id()).then_return("error-id")
    decoy.when(model_utils.get_timestamp()).then_return(
        datetime(year=2022, month=2, day=2),
        datetime(year=2023, month=3, day=3),
    )

    await subject.execute("command-id")

    decoy.verify(
        action_dispatcher.dispatch(UpdateCommandAction(command=running_command)),
        action_dispatcher.dispatch(
            FailCommandAction(
                command_id="command-id",
                error_id="error-id",
                failed_at=datetime(year=2023, month=3, day=3),
                error=expected_error,
            )
        ),
    )
