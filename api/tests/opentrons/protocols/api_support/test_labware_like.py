from unittest.mock import MagicMock

import pytest
from opentrons.protocol_api import labware
from opentrons.protocols.api_support.definitions import MAX_SUPPORTED_VERSION
from opentrons.protocols.api_support.labware_like import LabwareLike, LabwareLikeType
from opentrons.protocols.geometry import module_geometry
from opentrons.protocols.geometry.deck import Deck
from opentrons.types import Location
from opentrons_shared_data.labware.dev_types import LabwareDefinition


@pytest.fixture(scope="session")
def trough_definition() -> LabwareDefinition:
    return labware.get_labware_definition("usascientific_12_reservoir_22ml")


@pytest.fixture(scope="session")
def trough(trough_definition):
    deck = Deck()
    return labware.load_from_definition(trough_definition, deck.position_for(1))


@pytest.fixture(scope="session")
def module(trough):
    deck = Deck()
    mod = module_geometry.load_module(
        module_geometry.TemperatureModuleModel.TEMPERATURE_V2,
        deck.position_for("6"),
        MAX_SUPPORTED_VERSION,
    )
    return mod


@pytest.fixture(scope="session")
def mod_trough(trough_definition, module):
    mod_trough = module.add_labware(
        labware.load_from_definition(trough_definition, module.location)
    )
    return mod_trough


def test_labware(trough, mod_trough, module):
    ll = LabwareLike(trough)
    assert ll.has_parent is True
    assert ll.parent.object == trough.parent
    assert ll.object == trough
    assert ll.object_type == LabwareLikeType.LABWARE


def test_well(trough):
    well = trough["A1"]
    ll = LabwareLike(well)
    assert ll.has_parent is True
    assert ll.parent.object == trough
    assert ll.object == well
    assert ll.object_type == LabwareLikeType.WELL


def test_module(module):
    ll = LabwareLike(module)
    assert ll.has_parent is True
    assert ll.parent.object is module.parent
    assert ll.object is module
    assert ll.object_type == LabwareLikeType.MODULE
    assert ll.is_module
    assert ll.as_module() == module


def test_slot():
    ll = LabwareLike("1")
    assert ll.has_parent is False
    assert ll.parent.object is None
    assert ll.object == "1"
    assert ll.object_type == LabwareLikeType.SLOT


def test_empty():
    ll = LabwareLike(None)
    assert ll.has_parent is False
    assert ll.parent.object is None
    assert ll.object is None
    assert ll.object_type == LabwareLikeType.NONE


def test_module_parent(trough, module, mod_trough):
    assert LabwareLike(mod_trough).module_parent() == module
    assert LabwareLike(mod_trough["A1"]).module_parent() == module
    assert LabwareLike(module).module_parent() == module
    assert LabwareLike(trough).module_parent() is None
    assert LabwareLike("1").module_parent() is None


def test_first_parent(trough, module, mod_trough):
    assert LabwareLike(trough).first_parent() == "1"
    assert LabwareLike(trough["A2"]).first_parent() == "1"
    assert LabwareLike(None).first_parent() is None
    assert LabwareLike("6").first_parent() == "6"

    assert LabwareLike(mod_trough["A5"]).first_parent() == "6"
    assert LabwareLike(mod_trough).first_parent() == "6"
    assert LabwareLike(module).first_parent() == "6"

    # Set up recursion cycle test.
    mock_labware_geometry = MagicMock()
    mock_labware_geometry.parent = Location(point=None, labware=mod_trough)
    mod_trough._implementation.get_geometry = MagicMock(
        return_value=mock_labware_geometry
    )

    with pytest.raises(RuntimeError):
        # make sure we catch cycles
        LabwareLike(mod_trough).first_parent()
