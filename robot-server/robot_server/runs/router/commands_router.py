"""Router for /runs commands endpoints."""
from fastapi import APIRouter, Depends, status
from typing import Union
from typing_extensions import Literal

from opentrons.protocol_engine import commands as pe_commands, errors as pe_errors

from robot_server.errors import ErrorDetails, ErrorResponse
from robot_server.service.json_api import (
    RequestModel,
    ResponseModel,
    MultiResponseModel,
)

from ..run_models import Run, RunCommandSummary
from ..engine_store import EngineStore
from ..dependencies import get_engine_store
from .base_router import RunNotFound, RunStopped, get_run

commands_router = APIRouter()


class CommandNotFound(ErrorDetails):
    """An error if a given run command is not found."""

    id: Literal["CommandNotFound"] = "CommandNotFound"
    title: str = "Run Command Not Found"


# todo(mm, 2021-09-23): Should this accept a list of commands, instead of just one?
@commands_router.post(
    path="/runs/{runId}/commands",
    summary="Enqueue a protocol command",
    description=(
        "Add a single protocol command to the run. "
        "The command is placed at the back of the queue."
    ),
    status_code=status.HTTP_200_OK,
    response_model=ResponseModel[pe_commands.Command, None],
    responses={
        status.HTTP_400_BAD_REQUEST: {"model": ErrorResponse[RunStopped]},
        status.HTTP_404_NOT_FOUND: {"model": ErrorResponse[RunNotFound]},
    },
)
async def create_run_command(
    request_body: RequestModel[pe_commands.CommandCreate],
    engine_store: EngineStore = Depends(get_engine_store),
    run: ResponseModel[Run, None] = Depends(get_run),
) -> ResponseModel[pe_commands.Command, None]:
    """Enqueue a protocol command.

    Arguments:
        request_body: The request containing the command that the client wants
            to enqueue.
        engine_store: Used to retrieve the `ProtocolEngine` on which the new
            command will be enqueued.
        run: Run response model, provided by the route handler for
            `GET /runs/{runId}`. Present to ensure 404 if run
            not found.
    """
    if not run.data.current:
        raise RunStopped(detail=f"Run {run.data.id} is not the current run").as_error(
            status.HTTP_400_BAD_REQUEST
        )

    command = engine_store.engine.add_command(request_body.data)
    return ResponseModel(data=command, links=None)


@commands_router.get(
    path="/runs/{runId}/commands",
    summary="Get a list of all protocol commands in the run",
    description=(
        "Get a list of all commands in the run and their statuses. "
        "This endpoint returns command summaries. Use "
        "`GET /runs/{runId}/commands/{commandId}` to get all "
        "information available for a given command."
    ),
    status_code=status.HTTP_200_OK,
    response_model=MultiResponseModel[RunCommandSummary, None],
    responses={
        status.HTTP_404_NOT_FOUND: {"model": ErrorResponse[RunNotFound]},
    },
)
async def get_run_commands(
    run: ResponseModel[Run, None] = Depends(get_run),
) -> MultiResponseModel[RunCommandSummary, None]:
    """Get a summary of all commands in a run.

    Arguments:
        run: Run response model, provided by the route handler for
            `GET /runs/{runId}`
    """
    return MultiResponseModel(data=run.data.commands, links=None)


@commands_router.get(
    path="/runs/{runId}/commands/{commandId}",
    summary="Get full details about a specific command in the run",
    description=(
        "Get a command along with any associated payload, result, and "
        "execution information."
    ),
    status_code=status.HTTP_200_OK,
    response_model=ResponseModel[pe_commands.Command, None],
    responses={
        status.HTTP_404_NOT_FOUND: {
            "model": Union[
                ErrorResponse[RunNotFound],
                ErrorResponse[CommandNotFound],
            ]
        },
    },
)
async def get_run_command(
    commandId: str,
    engine_store: EngineStore = Depends(get_engine_store),
    run: ResponseModel[Run, None] = Depends(get_run),
) -> ResponseModel[pe_commands.Command, None]:
    """Get a specific command from a run.

    Arguments:
        commandId: Command identifier, pulled from route parameter.
        engine_store: Protocol engine and runner storage.
        run: Run response model, provided by the route handler for
            `GET /run/{runId}`. Present to ensure 404 if run
            not found.
    """
    engine_state = engine_store.get_state(run.data.id)
    try:
        command = engine_state.commands.get(commandId)
    except pe_errors.CommandDoesNotExistError as e:
        raise CommandNotFound(detail=str(e)).as_error(status.HTTP_404_NOT_FOUND)

    return ResponseModel(data=command, links=None)
