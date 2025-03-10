"""Protocol engine module.

The protocol_engine module contains the logic necessary to take a stream of
protocol commands, issued by some arbitrary protocol runner, and turn it into
protocol state and side-effects like robot movements.
"""

from .create_protocol_engine import create_protocol_engine
from .protocol_engine import ProtocolEngine
from .errors import ProtocolEngineError, ErrorOccurrence
from .commands import Command, CommandCreate, CommandStatus, CommandType
from .state import State, StateView
from .plugins import AbstractPlugin

from .types import (
    LabwareOffset,
    LabwareOffsetCreate,
    LabwareOffsetVector,
    DeckSlotLocation,
    ModuleLocation,
    Dimensions,
    EngineStatus,
    LabwareLocation,
    LoadedLabware,
    LoadedPipette,
    PipetteName,
    WellLocation,
    WellOrigin,
    WellOffset,
)

__all__ = [
    # main factory and interface exports
    "create_protocol_engine",
    "ProtocolEngine",
    # error types
    "ProtocolEngineError",
    "ErrorOccurrence",
    # top level command unions and values
    "Command",
    "CommandCreate",
    "CommandStatus",
    "CommandType",
    # state interfaces and models
    "State",
    "StateView",
    # public value interfaces and models
    "LabwareOffset",
    "LabwareOffsetCreate",
    "LabwareOffsetVector",
    "DeckSlotLocation",
    "ModuleLocation",
    "Dimensions",
    "EngineStatus",
    "LabwareLocation",
    "LoadedLabware",
    "LoadedPipette",
    "PipetteName",
    "WellLocation",
    "WellOrigin",
    "WellOffset",
    # plugins
    "AbstractPlugin",
]
