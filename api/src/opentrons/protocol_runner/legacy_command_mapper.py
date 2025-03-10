"""Translate events from a legacy ``ProtocolContext`` into Protocol Engine commands."""

from collections import defaultdict
from datetime import datetime
from typing import Dict, List, Union

from opentrons.types import MountType, DeckSlotName
from opentrons.commands import types as legacy_command_types
from opentrons.protocol_engine import (
    ProtocolEngineError,
    actions as pe_actions,
    commands as pe_commands,
    types as pe_types,
)
from opentrons.protocol_engine.resources import ModelUtils
from opentrons.protocols.models.labware_definition import LabwareDefinition

from .legacy_wrappers import (
    LegacyInstrumentLoadInfo,
    LegacyLabwareLoadInfo,
    LegacyModuleLoadInfo,
    LegacyPipetteContext,
    LegacyWell,
)


class LegacyCommandParams(pe_commands.CustomParams):
    """Custom command data payload for mapped legacy commands."""

    legacyCommandType: str
    legacyCommandText: str


class LegacyContextCommandError(ProtocolEngineError):
    """An error returned when a PAPIv2 ProtocolContext command fails."""


class LegacyCommandMapper:
    """Map broker commands to protocol engine commands.

    Each protocol should use its own instance of this class.
    """

    def __init__(self) -> None:
        """Initialize the command mapper."""
        self._running_commands: Dict[str, List[pe_commands.Command]] = defaultdict(list)
        self._command_count: Dict[str, int] = defaultdict(lambda: 0)
        self._labware_id_by_slot: Dict[DeckSlotName, str] = {}
        self._pipette_id_by_mount: Dict[MountType, str] = {}
        self._module_id_by_slot: Dict[DeckSlotName, str] = {}

    def map_command(
        self,
        command: legacy_command_types.CommandMessage,
    ) -> Union[pe_actions.UpdateCommandAction, pe_actions.FailCommandAction]:
        """Map a legacy Broker command to a ProtocolEngine command.

        A "before" message from the Broker
        is mapped to a ``RUNNING`` ProtocolEngine command.

        An "after" message from the Broker
        is mapped to a ``SUCCEEDED`` ProtocolEngine command.
        It has the same ID as the original ``RUNNING`` command,
        so when you send it to the ProtocolEngine, it will update the original
        command's status in-place.
        """
        command_type = command["name"]
        command_error = command["error"]
        stage = command["$"]

        command_id = f"{command_type}-0"
        now = ModelUtils.get_timestamp()

        if stage == "before":
            count = self._command_count[command_type]
            command_id = f"{command_type}-{count}"
            engine_command = self._build_initial_command(command, command_id, now)

            self._command_count[command_type] = count + 1
            self._running_commands[command_type].append(engine_command)

            return pe_actions.UpdateCommandAction(engine_command)

        elif command_error is None:
            running_command = self._running_commands[command_type].pop()
            completed_command = running_command.copy(
                update={
                    "status": pe_commands.CommandStatus.SUCCEEDED,
                    "completedAt": now,
                }
            )
            return pe_actions.UpdateCommandAction(completed_command)

        else:
            return pe_actions.FailCommandAction(
                command_id=command_id,
                error_id=ModelUtils.generate_id(),
                failed_at=now,
                error=LegacyContextCommandError(str(command_error)),
            )

    def map_labware_load(
        self, labware_load_info: LegacyLabwareLoadInfo
    ) -> pe_commands.Command:
        """Map a legacy labware load to a ProtocolEngine command."""
        now = ModelUtils.get_timestamp()
        count = self._command_count["LOAD_LABWARE"]
        slot = labware_load_info.deck_slot
        location: pe_types.LabwareLocation
        if labware_load_info.on_module:
            location = pe_types.ModuleLocation(moduleId=self._module_id_by_slot[slot])
        else:
            location = pe_types.DeckSlotLocation(slotName=slot)

        command_id = f"commands.LOAD_LABWARE-{count}"
        labware_id = f"labware-{count}"

        load_labware_command = pe_commands.LoadLabware(
            id=command_id,
            status=pe_commands.CommandStatus.SUCCEEDED,
            createdAt=now,
            startedAt=now,
            completedAt=now,
            params=pe_commands.LoadLabwareParams(
                location=location,
                loadName=labware_load_info.labware_load_name,
                namespace=labware_load_info.labware_namespace,
                version=labware_load_info.labware_version,
            ),
            result=pe_commands.LoadLabwareResult(
                labwareId=labware_id,
                definition=LabwareDefinition.parse_obj(
                    labware_load_info.labware_definition
                ),
                # fixme(mm, 2021-11-11): Labware offsets added to the ProtocolEngine
                # need to apply to the legacy protocol somehow, and get fed back here.
                offsetId=None,
            ),
        )

        self._command_count["LOAD_LABWARE"] = count + 1
        if isinstance(location, pe_types.DeckSlotLocation):
            # TODO (spp, 2021-11-16): Account for labware on modules when mapping legacy
            #  pipetting commands; either in self._labware_id_by_slot or something else
            self._labware_id_by_slot[location.slotName] = labware_id
        return load_labware_command

    def map_instrument_load(
        self,
        instrument_load_info: LegacyInstrumentLoadInfo,
    ) -> pe_commands.Command:
        """Map a legacy instrument (pipette) load to a ProtocolEngine command."""
        now = ModelUtils.get_timestamp()
        count = self._command_count["LOAD_PIPETTE"]
        command_id = f"commands.LOAD_PIPETTE-{count}"
        pipette_id = f"pipette-{count}"
        mount = MountType(str(instrument_load_info.mount).lower())

        load_pipette_command = pe_commands.LoadPipette(
            id=command_id,
            status=pe_commands.CommandStatus.SUCCEEDED,
            createdAt=now,
            startedAt=now,
            completedAt=now,
            params=pe_commands.LoadPipetteParams(
                pipetteName=pe_types.PipetteName(
                    instrument_load_info.instrument_load_name
                ),
                mount=mount,
            ),
            result=pe_commands.LoadPipetteResult(pipetteId=pipette_id),
        )

        self._command_count["LOAD_PIPETTE"] = count + 1
        self._pipette_id_by_mount[mount] = pipette_id
        return load_pipette_command

    def map_module_load(
        self, module_load_info: LegacyModuleLoadInfo
    ) -> pe_commands.Command:
        """Map a legacy module load to a Protocol Engine command."""
        now = ModelUtils.get_timestamp()

        count = self._command_count["LOAD_MODULE"]
        module_id = f"module-{count}"

        load_module_command = pe_commands.LoadModule(
            id=f"commands.LOAD_MODULE-{count}",
            status=pe_commands.CommandStatus.SUCCEEDED,
            createdAt=now,
            startedAt=now,
            completedAt=now,
            params=pe_commands.LoadModuleParams(
                model=module_load_info.module_name,
                location=pe_types.DeckSlotLocation(
                    slotName=module_load_info.deck_slot,
                ),
                moduleId=module_id,
            ),
            result=pe_commands.LoadModuleResult(
                moduleId=module_id,
            ),
        )
        self._command_count["LOAD_MODULE"] = count + 1
        self._module_id_by_slot[module_load_info.deck_slot] = module_id
        return load_module_command

    def _build_initial_command(
        self,
        command: legacy_command_types.CommandMessage,
        command_id: str,
        now: datetime,
    ) -> pe_commands.Command:
        engine_command: pe_commands.Command

        if (
            command["name"] == legacy_command_types.PICK_UP_TIP
            and "instrument" in command["payload"]
            and "location" in command["payload"]
            and isinstance(command["payload"]["location"], LegacyWell)  # type: ignore  # noqa: E501
        ):
            pipette: LegacyPipetteContext = command["payload"]["instrument"]  # type: ignore  # noqa: E501
            well: LegacyWell = command["payload"]["location"]  # type: ignore  # noqa: E501
            mount = MountType(pipette.mount)
            slot = DeckSlotName.from_primitive(well.parent.parent)  # type: ignore[arg-type] # noqa: E501
            well_name = well.well_name

            labware_id = self._labware_id_by_slot[slot]
            pipette_id = self._pipette_id_by_mount[mount]

            engine_command = pe_commands.PickUpTip(
                id=command_id,
                status=pe_commands.CommandStatus.RUNNING,
                createdAt=now,
                startedAt=now,
                params=pe_commands.PickUpTipParams(
                    pipetteId=pipette_id,
                    labwareId=labware_id,
                    wellName=well_name,
                ),
            )

        else:
            engine_command = pe_commands.Custom(
                id=command_id,
                status=pe_commands.CommandStatus.RUNNING,
                createdAt=now,
                startedAt=now,
                params=LegacyCommandParams(
                    legacyCommandType=command["name"],
                    legacyCommandText=command["payload"]["text"],
                ),
            )

        return engine_command
