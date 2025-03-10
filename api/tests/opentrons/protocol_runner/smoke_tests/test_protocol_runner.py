"""Smoke tests for the ProtocolRunner and ProtocolEngine classes.

These tests construct a ProtocolRunner with a real ProtocolEngine
hooked to a simulating HardwareAPI.

Minimal, but valid and complete, protocol files are then loaded from
disk into the runner, and the protocols are run to completion. From
there, the ProtocolEngine state is inspected to everything was loaded
and ran as expected.
"""
import pytest
from pathlib import Path
from datetime import datetime
from decoy import matchers

from opentrons.types import MountType
from opentrons.protocols.api_support.types import APIVersion
from opentrons.protocol_api_experimental import DeckSlotName

from opentrons.protocol_engine import (
    DeckSlotLocation,
    LoadedLabware,
    LoadedPipette,
    PipetteName,
    commands,
)
from opentrons.protocol_runner import (
    ProtocolSource,
    JsonPreAnalysis,
    PythonPreAnalysis,
    create_simulating_runner,
)


async def test_runner_with_python(python_protocol_file: Path) -> None:
    """It should run a Python protocol on the ProtocolRunner."""
    protocol_source = ProtocolSource(
        files=[python_protocol_file],
        pre_analysis=PythonPreAnalysis(metadata={}, api_version=APIVersion(3, 0)),
    )

    subject = await create_simulating_runner()
    result = await subject.run(protocol_source)
    commands_result = result.commands
    pipettes_result = result.pipettes
    labware_result = result.labware

    pipette_id_captor = matchers.Captor()
    labware_id_captor = matchers.Captor()

    expected_pipette = LoadedPipette.construct(
        id=pipette_id_captor,
        pipetteName=PipetteName.P300_SINGLE,
        mount=MountType.LEFT,
    )

    expected_labware = LoadedLabware.construct(
        id=labware_id_captor,
        location=DeckSlotLocation(slotName=DeckSlotName.SLOT_1),
        loadName="opentrons_96_tiprack_300ul",
        definitionUri="opentrons/opentrons_96_tiprack_300ul/1",
        # fixme(mm, 2021-11-11): We should smoke-test that the engine picks up labware
        # offsets, but it's unclear to me what the best way of doing that is, since
        # we don't have access to the engine here to add offsets to it.
        offsetId=None,
    )

    assert expected_pipette in pipettes_result
    assert expected_labware in labware_result

    expected_command = commands.PickUpTip.construct(
        id=matchers.IsA(str),
        status=commands.CommandStatus.SUCCEEDED,
        createdAt=matchers.IsA(datetime),
        startedAt=matchers.IsA(datetime),
        completedAt=matchers.IsA(datetime),
        params=commands.PickUpTipParams(
            pipetteId=pipette_id_captor.value,
            labwareId=labware_id_captor.value,
            wellName="A1",
        ),
        result=commands.PickUpTipResult(),
    )

    assert expected_command in commands_result


@pytest.mark.xfail(raises=NotImplementedError, strict=True)
async def test_runner_with_json(json_protocol_file: Path) -> None:
    """It should run a JSON protocol on the ProtocolRunner."""
    protocol_source = ProtocolSource(
        files=[json_protocol_file],
        pre_analysis=JsonPreAnalysis(metadata={}, schema_version=6),
    )

    subject = await create_simulating_runner()
    result = await subject.run(protocol_source)
    commands_result = result.commands
    pipettes_result = result.pipettes
    labware_result = result.labware

    expected_pipette = LoadedPipette(
        id="pipette-id",
        pipetteName=PipetteName.P300_SINGLE,
        mount=MountType.LEFT,
    )

    expected_labware = LoadedLabware(
        id="labware-id",
        location=DeckSlotLocation(slotName=DeckSlotName.SLOT_1),
        loadName="opentrons_96_tiprack_300ul",
        definitionUri="opentrons/opentrons_96_tiprack_300ul/1",
        # fixme(mm, 2021-11-11): We should smoke-test that the engine picks up labware
        # offsets, but it's unclear to me what the best way of doing that is, since
        # we don't have access to the engine here to add offsets to it.
        offsetId=None,
    )

    assert expected_pipette in pipettes_result
    assert expected_labware in labware_result

    expected_command = commands.PickUpTip.construct(
        id=matchers.IsA(str),
        status=commands.CommandStatus.SUCCEEDED,
        createdAt=matchers.IsA(datetime),
        startedAt=matchers.IsA(datetime),
        completedAt=matchers.IsA(datetime),
        params=commands.PickUpTipParams(
            pipetteId="pipette-id",
            labwareId="labware-id",
            wellName="A1",
        ),
        result=commands.PickUpTipResult(),
    )

    assert expected_command in commands_result


async def test_runner_with_legacy_python(legacy_python_protocol_file: Path) -> None:
    """It should run a Python protocol on the ProtocolRunner."""
    protocol_source = ProtocolSource(
        files=[legacy_python_protocol_file],
        pre_analysis=PythonPreAnalysis(metadata={}, api_version=APIVersion(2, 11)),
    )

    subject = await create_simulating_runner()
    result = await subject.run(protocol_source)

    commands_result = result.commands
    pipettes_result = result.pipettes
    labware_result = result.labware

    pipette_id_captor = matchers.Captor()
    labware_id_captor = matchers.Captor()

    expected_pipette = LoadedPipette.construct(
        id=pipette_id_captor,
        pipetteName=PipetteName.P300_SINGLE,
        mount=MountType.LEFT,
    )

    expected_labware = LoadedLabware.construct(
        id=labware_id_captor,
        location=DeckSlotLocation(slotName=DeckSlotName.SLOT_1),
        loadName="opentrons_96_tiprack_300ul",
        definitionUri="opentrons/opentrons_96_tiprack_300ul/1",
        # fixme(mm, 2021-11-11): When legacy running supports labware offsets, check
        # for that here.
        offsetId=None,
    )

    assert expected_pipette in pipettes_result
    assert expected_labware in labware_result

    expected_command = commands.PickUpTip.construct(
        id=matchers.IsA(str),
        status=commands.CommandStatus.SUCCEEDED,
        createdAt=matchers.IsA(datetime),
        startedAt=matchers.IsA(datetime),
        completedAt=matchers.IsA(datetime),
        params=commands.PickUpTipParams(
            pipetteId=pipette_id_captor.value,
            labwareId=labware_id_captor.value,
            wellName="A1",
        ),
        result=None,
    )

    assert expected_command in commands_result


async def test_runner_with_legacy_json(legacy_json_protocol_file: Path) -> None:
    """It should run a Python protocol on the ProtocolRunner."""
    protocol_source = ProtocolSource(
        files=[legacy_json_protocol_file],
        pre_analysis=JsonPreAnalysis(metadata={}, schema_version=5),
    )

    subject = await create_simulating_runner()
    result = await subject.run(protocol_source)

    commands_result = result.commands
    pipettes_result = result.pipettes
    labware_result = result.labware

    pipette_id_captor = matchers.Captor()
    labware_id_captor = matchers.Captor()

    expected_pipette = LoadedPipette.construct(
        id=pipette_id_captor,
        pipetteName=PipetteName.P300_SINGLE,
        mount=MountType.LEFT,
    )

    expected_labware = LoadedLabware.construct(
        id=labware_id_captor,
        location=DeckSlotLocation(slotName=DeckSlotName.SLOT_1),
        loadName="opentrons_96_tiprack_300ul",
        definitionUri="opentrons/opentrons_96_tiprack_300ul/1",
        # fixme(mm, 2021-11-11): When legacy running supports labware offsets, check
        # for that here.
        offsetId=None,
    )

    assert expected_pipette in pipettes_result
    assert expected_labware in labware_result

    expected_command = commands.PickUpTip.construct(
        id=matchers.IsA(str),
        status=commands.CommandStatus.SUCCEEDED,
        createdAt=matchers.IsA(datetime),
        startedAt=matchers.IsA(datetime),
        completedAt=matchers.IsA(datetime),
        params=commands.PickUpTipParams(
            pipetteId=pipette_id_captor.value,
            labwareId=labware_id_captor.value,
            wellName="A1",
        ),
        result=None,
    )

    assert expected_command in commands_result
