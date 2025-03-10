# noqa: D100

from __future__ import annotations

from typing import Any, Optional, Union, Sequence, List

from .labware import Labware
from .well import Well

from opentrons import types
from opentrons.protocols.api_support.types import APIVersion
from opentrons.hardware_control.dev_types import PipetteDict

# todo(mm, 2021-04-09): Duplicate these classes in this package to
# decouple from the v2 opentrons.protocol_api?
from opentrons.protocol_api import PairedInstrumentContext
from opentrons.protocol_api.instrument_context import AdvancedLiquidHandling
from opentrons.protocol_engine import WellLocation, WellOrigin, WellOffset
from opentrons.protocol_engine.clients import SyncClient as ProtocolEngineClient

# todo(mm, 2021-04-09): How customer-facing are these classes? Should they be
# accessible and documented as part of this package?
from opentrons.protocols.api_support.util import PlungerSpeeds, FlowRates, Clearances


# todo(mm, 2021-04-09): Can/should we remove the word "Context" from the name?
class PipetteContext:  # noqa: D101
    def __init__(
        self,
        engine_client: ProtocolEngineClient,
        pipette_id: str,
    ) -> None:
        """Initialize a PipetteContext API provider.

        You should not need to call this constructor yourself. The system will
        create a PipetteContext for you when you call :py:meth:`load_pipette`.

        Args:
            engine_client: A client to access protocol state and execute commands.
            pipette_id: The pipette's identifier in commands and protocol state.
        """
        self._engine_client = engine_client
        self._pipette_id = pipette_id

    def __hash__(self) -> int:
        """Get hash.

        Uses the pipette instance's unique identifier in protocol state.
        """
        return hash(self._pipette_id)

    def __eq__(self, other: object) -> bool:
        """Compare for object equality.

        Checks that other object is a `PipetteContext` and has the same identifier.
        """
        return (
            isinstance(other, PipetteContext) and self._pipette_id == other._pipette_id
        )

    def __repr__(self) -> str:  # noqa: D105
        raise NotImplementedError()

    def __str__(self) -> str:  # noqa: D105
        raise NotImplementedError()

    @property
    def api_version(self) -> APIVersion:  # noqa: D102
        raise NotImplementedError()

    @property
    def starting_tip(self) -> Optional[Well]:  # noqa: D102
        raise NotImplementedError()

    @starting_tip.setter
    def starting_tip(self, location: Optional[Well]) -> None:
        raise NotImplementedError()

    def reset_tipracks(self) -> None:  # noqa: D102
        raise NotImplementedError()

    @property
    def default_speed(self) -> float:  # noqa: D102
        raise NotImplementedError()

    @default_speed.setter
    def default_speed(self, speed: float) -> None:
        raise NotImplementedError()

    def aspirate(  # noqa: D102
        self,
        volume: Optional[float] = None,
        location: Optional[Union[types.Location, Well]] = None,
        rate: float = 1.0,
    ) -> PipetteContext:

        if volume is None or volume == 0:
            # todo(mm, 2021-04-14): If None or 0, use highest volume possible.
            raise NotImplementedError("volume must be specified.")

        if rate != 1:
            raise NotImplementedError(
                "Protocol Engine does not yet support adjusting flow rates."
            )

        if isinstance(location, Well):
            self._engine_client.aspirate(
                pipette_id=self._pipette_id,
                labware_id=location.parent.labware_id,
                well_name=location.well_name,
                well_location=WellLocation(
                    origin=WellOrigin.BOTTOM,
                    # todo(mm, 2021-04-14): Get default offset in well via
                    # self.well_bottom_clearance.aspirate, instead of hard-coding.
                    offset=WellOffset(x=0, y=0, z=1),
                ),
                volume=volume,
            )
        else:
            # todo(mm, 2021-04-14):
            #   * If location is None, use current location.
            #   * If location is a Location (possibly deck coords, or possibly
            #     something like well.top()), use that.
            raise NotImplementedError(
                "locations other than Wells are currently unsupported."
            )

        return self

    def dispense(  # noqa: D102
        self,
        volume: Optional[float] = None,
        location: Optional[Union[types.Location, Well]] = None,
        rate: float = 1.0,
    ) -> PipetteContext:

        if rate != 1:
            raise NotImplementedError("Flow rate adjustment not yet supported in PE.")

        if volume is None or volume == 0:
            raise NotImplementedError("Volume tracking not yet supported in PE.")

        # TODO (spp:
        #  - Disambiguate location. Cases in point:
        #       1. location not specified; use current labware & well
        #       2. specified location is a Point)
        #  - Use well_bottom_clearance as offset for well_location(?)
        if isinstance(location, Well):
            self._engine_client.dispense(
                pipette_id=self._pipette_id,
                labware_id=location.parent.labware_id,
                well_name=location.well_name,
                well_location=WellLocation(
                    origin=WellOrigin.BOTTOM,
                    offset=WellOffset(x=0, y=0, z=1),
                ),
                volume=volume,
            )
        else:
            raise NotImplementedError(
                "Dispensing to a non-well location not yet supported in PE."
            )
        return self

    def mix(  # noqa: D102
        self,
        repetitions: int = 1,
        volume: Optional[float] = None,
        location: Optional[Union[types.Location, Well]] = None,
        rate: float = 1.0,
    ) -> PipetteContext:
        raise NotImplementedError()

    def blow_out(  # noqa: D102
        self,
        location: Optional[Union[types.Location, Well]] = None,
    ) -> PipetteContext:
        raise NotImplementedError()

    def touch_tip(  # noqa: D102
        self,
        location: Optional[Well] = None,
        radius: float = 1.0,
        v_offset: float = -1.0,
        speed: float = 60.0,
    ) -> PipetteContext:
        raise NotImplementedError()

    def air_gap(  # noqa: D102
        self,
        volume: Optional[float] = None,
        height: Optional[float] = None,
    ) -> PipetteContext:
        raise NotImplementedError()

    def return_tip(self, home_after: bool = True) -> PipetteContext:  # noqa: D102
        raise NotImplementedError()

    def pick_up_tip(  # noqa: D102
        self,
        location: Optional[Union[types.Location, Well]] = None,
        presses: Optional[int] = None,
        increment: Optional[float] = None,
    ) -> PipetteContext:
        # TODO(al, 2021-04-12): What about presses and increment? They are not
        #  supported by PE command. They are also not supported by PD protocols
        #  either.
        if presses is not None or increment is not None:
            raise NotImplementedError()
        if isinstance(location, Well):
            self._engine_client.pick_up_tip(
                pipette_id=self._pipette_id,
                labware_id=location.parent.labware_id,
                well_name=location.well_name,
            )
        else:
            # TODO(al, 2021-04-12): Support for picking up next tip in a labware
            #  and in tipracks associated with a pipette
            raise NotImplementedError()

        return self

    def drop_tip(  # noqa: D102
        self,
        location: Optional[Union[types.Location, Well]] = None,
        home_after: bool = True,
    ) -> PipetteContext:
        # TODO(al, 2021-04-12): What about home_after?
        if not home_after:
            raise NotImplementedError()
        if isinstance(location, Well):
            self._engine_client.drop_tip(
                pipette_id=self._pipette_id,
                labware_id=location.parent.labware_id,
                well_name=location.well_name,
            )
        else:
            # TODO(al, 2021-04-12): Support for dropping tip in trash.
            raise NotImplementedError()

        return self

    def home(self) -> PipetteContext:  # noqa: D102
        raise NotImplementedError()

    def home_plunger(self) -> PipetteContext:  # noqa: D102
        raise NotImplementedError()

    # TODO(mc, 2021-09-12): explicitely type kwargs, remove args
    def distribute(  # noqa: D102
        self,
        volume: Union[float, Sequence[float]],
        source: Well,
        dest: List[Well],
        *args: Any,
        **kwargs: Any,
    ) -> PipetteContext:
        raise NotImplementedError()

    # TODO(mc, 2021-09-12): explicitely type kwargs, remove args
    def consolidate(  # noqa: D102
        self,
        volume: Union[float, Sequence[float]],
        source: List[Well],
        dest: Well,
        *args: Any,
        **kwargs: Any,
    ) -> PipetteContext:
        raise NotImplementedError()

    # TODO(mc, 2021-09-12): explicitely type kwargs
    def transfer(  # noqa: D102
        self,
        volume: Union[float, Sequence[float]],
        source: AdvancedLiquidHandling,
        dest: AdvancedLiquidHandling,
        trash: bool = True,
        **kwargs: Any,
    ) -> PipetteContext:
        raise NotImplementedError()

    def delay(self) -> None:  # noqa: D102
        raise NotImplementedError()

    def move_to(  # noqa: D102
        self,
        location: types.Location,
        force_direct: bool = False,
        minimum_z_height: Optional[float] = None,
        speed: Optional[float] = None,
    ) -> PipetteContext:
        raise NotImplementedError()

    @property
    def mount(self) -> str:  # noqa: D102
        raise NotImplementedError()

    @property
    def speed(self) -> PlungerSpeeds:  # noqa: D102
        raise NotImplementedError()

    @property
    def flow_rate(self) -> FlowRates:  # noqa: D102
        raise NotImplementedError()

    @property
    def type(self) -> str:  # noqa: D102
        raise NotImplementedError()

    @property
    def tip_racks(self) -> List[Labware]:  # noqa: D102
        raise NotImplementedError()

    @tip_racks.setter
    def tip_racks(self, racks: List[Labware]) -> None:
        raise NotImplementedError()

    @property
    def trash_container(self) -> Labware:  # noqa: D102
        raise NotImplementedError()

    @trash_container.setter
    def trash_container(self, trash: Labware) -> None:
        raise NotImplementedError()

    @property
    def name(self) -> str:  # noqa: D102
        raise NotImplementedError()

    @property
    def model(self) -> str:  # noqa: D102
        raise NotImplementedError()

    @property
    def min_volume(self) -> float:  # noqa: D102
        raise NotImplementedError()

    @property
    def max_volume(self) -> float:  # noqa: D102
        raise NotImplementedError()

    @property
    def current_volume(self) -> float:  # noqa: D102
        raise NotImplementedError()

    @property
    def has_tip(self) -> bool:  # noqa: D102
        raise NotImplementedError()

    @property
    def hw_pipette(self) -> PipetteDict:  # noqa: D102
        raise NotImplementedError()

    @property
    def channels(self) -> int:  # noqa: D102
        raise NotImplementedError()

    @property
    def return_height(self) -> float:  # noqa: D102
        raise NotImplementedError()

    @property
    def well_bottom_clearance(self) -> Clearances:  # noqa: D102
        raise NotImplementedError()

    def pair_with(  # noqa: D102
        self, instrument: PipetteContext
    ) -> PairedInstrumentContext:
        raise NotImplementedError()
