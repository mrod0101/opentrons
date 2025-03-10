from __future__ import annotations
import asyncio
import contextlib
import logging
from typing import (
    Callable,
    Dict,
    Iterator,
    List,
    Optional,
    Tuple,
    Union,
    TYPE_CHECKING,
    cast,
)
from collections import OrderedDict

from opentrons import types
from opentrons.equipment_broker import EquipmentBroker
from opentrons.hardware_control import SynchronousAdapter, ThreadManager
from opentrons.hardware_control.modules.types import ModuleType
from opentrons.commands import protocol_commands as cmds, types as cmd_types
from opentrons.commands.publisher import CommandPublisher, publish
from opentrons.protocols.api_support.types import APIVersion
from opentrons.protocols.context.protocol_api.instrument_context import (
    InstrumentContextImplementation,
)
from opentrons.protocols.context.simulator.instrument_context import (
    InstrumentContextSimulation,
)
from opentrons.protocols.types import Protocol
from .labware import Labware
from opentrons.protocols.context.labware import AbstractLabware
from opentrons.protocols.context.protocol import AbstractProtocol
from opentrons.protocols.geometry.module_geometry import ModuleGeometry
from opentrons.protocols.geometry.deck import Deck
from opentrons.protocols.api_support.definitions import MAX_SUPPORTED_VERSION
from .instrument_context import InstrumentContext
from .module_contexts import (
    ModuleContext,
    MagneticModuleContext,
    TemperatureModuleContext,
    ThermocyclerContext,
)
from .load_info import LabwareLoadInfo, ModuleLoadInfo, InstrumentLoadInfo
from opentrons.protocols.api_support.util import (
    AxisMaxSpeeds,
    requires_version,
    APIVersionError,
)

if TYPE_CHECKING:
    from opentrons_shared_data.labware.dev_types import LabwareDefinition

logger = logging.getLogger(__name__)

ModuleTypes = Union[
    "TemperatureModuleContext", "MagneticModuleContext", "ThermocyclerContext"
]


class ProtocolContext(CommandPublisher):
    """The Context class is a container for the state of a protocol.

    It encapsulates many of the methods formerly found in the Robot class,
    including labware, instrument, and module loading, as well as core
    functions like pause and resume.

    Unlike the old robot class, it is designed to be ephemeral. The lifetime
    of a particular instance should be about the same as the lifetime of a
    protocol. The only exception is the one stored in
    ``.legacy_api.api.robot``, which is provided only for back
    compatibility and should be used less and less as time goes by.

    .. versionadded:: 2.0

    """

    def __init__(
        self,
        implementation: AbstractProtocol,
        loop: asyncio.AbstractEventLoop = None,
        broker=None,
        api_version: Optional[APIVersion] = None,
    ) -> None:
        """Build a :py:class:`.ProtocolContext`.

        :param loop: An event loop to use. If not specified, this ctor will
                     (eventually) call :py:meth:`asyncio.get_event_loop`.
        :param broker: An optional command broker to link to. If not
                      specified, a dummy one is used.
        :param api_version: The API version to use. If this is ``None``, uses
                            the max supported version.
        """
        super().__init__(broker)

        self._implementation = implementation

        self._api_version = api_version or MAX_SUPPORTED_VERSION
        if self._api_version > MAX_SUPPORTED_VERSION:
            raise RuntimeError(
                f"API version {self._api_version} is not supported by this "
                f"robot software. Please either reduce your requested API "
                f"version or update your robot."
            )
        self._loop = loop or asyncio.get_event_loop()
        self._instruments: Dict[types.Mount, Optional[InstrumentContext]] = {
            mount: None for mount in types.Mount
        }
        self._modules: List[ModuleContext] = []

        self._commands: List[str] = []
        self._unsubscribe_commands: Optional[Callable[[], None]] = None
        self.clear_commands()

        self._labware_load_broker = EquipmentBroker[LabwareLoadInfo]()
        self._instrument_load_broker = EquipmentBroker[InstrumentLoadInfo]()
        self._module_load_broker = EquipmentBroker[ModuleLoadInfo]()

    @property
    def labware_load_broker(self) -> EquipmentBroker[LabwareLoadInfo]:
        """For internal Opentrons use only.

        :meta private:

        Subscribers to this broker will be notified with information about every
        successful labware load.

        Only :py:obj:`ProtocolContext` is allowed to publish to this broker.
        Calling code may only subscribe or unsubscribe.
        """
        return self._labware_load_broker

    @property
    def instrument_load_broker(self) -> EquipmentBroker[InstrumentLoadInfo]:
        """For internal Opentrons use only.

        :meta private:

        Like `labware_load_broker`, but for pipettes.
        """
        return self._instrument_load_broker

    @property
    def module_load_broker(self) -> EquipmentBroker[ModuleLoadInfo]:
        """For internal Opentrons use only.

        :meta private:

        Like `labware_load_broker`, but for modules.
        """
        return self._module_load_broker

    @classmethod
    def build_using(
        cls, implementation: AbstractProtocol, protocol: Protocol, *args, **kwargs
    ) -> ProtocolContext:
        """Build an API instance for the specified parsed protocol

        This is used internally to provision the context with bundle
        contents or api levels.
        """
        kwargs["api_version"] = getattr(protocol, "api_level", MAX_SUPPORTED_VERSION)
        kwargs["implementation"] = implementation
        return cls(*args, **kwargs)

    @property  # type: ignore
    @requires_version(2, 0)
    def api_version(self) -> APIVersion:
        """Return the API version supported by this protocol context.

        The supported API version was specified when the protocol context
        was initialized. It may be lower than the highest version supported
        by the robot software. For the highest version supported by the
        robot software, see ``protocol_api.MAX_SUPPORTED_VERSION``.
        """
        return self._api_version

    @property
    def _hw_manager(self):
        # TODO (lc 01-05-2021) remove this once we have a more
        # user facing hardware control http api.
        logger.warning(
            "This function will be deprecated in later versions."
            "Please use with caution."
        )
        return self._implementation.get_hardware()

    @property  # type: ignore
    @requires_version(2, 0)
    def bundled_data(self) -> Dict[str, bytes]:
        """Accessor for data files bundled with this protocol, if any.

        This is a dictionary mapping the filenames of bundled datafiles, with
        extensions but without paths (e.g. if a file is stored in the bundle as
        ``data/mydata/aspirations.csv`` it will be in the dict as
        ``'aspirations.csv'``) to the bytes contents of the files.
        """
        return self._implementation.get_bundled_data()

    def cleanup(self):
        """Finalize and clean up the protocol context."""
        if self._unsubscribe_commands:
            self._unsubscribe_commands()
            self._unsubscribe_commands = None

    def __del__(self):
        if getattr(self, "_unsubscribe_commands", None):
            self._unsubscribe_commands()  # type: ignore

    @property  # type: ignore
    @requires_version(2, 0)
    def max_speeds(self) -> AxisMaxSpeeds:
        """Per-axis speed limits when moving this instrument.

        Changing this value changes the speed limit for each non-plunger
        axis of the robot, when moving this pipette. Note that this does
        only sets a limit on how fast movements can be; movements can
        still be slower than this. However, it is useful if you require
        the robot to move much more slowly than normal when using this
        pipette.

        This is a dictionary mapping string names of axes to float values
        limiting speeds. To change a speed, set that axis's value. To
        reset an axis's speed to default, delete the entry for that axis
        or assign it to ``None``.

        For instance,

        .. code-block:: py

            def run(protocol):
                protocol.comment(str(right.max_speeds))  # '{}' - all default
                protocol.max_speeds['A'] = 10  # limit max speed of
                                               # right pipette Z to 10mm/s
                del protocol.max_speeds['A']  # reset to default
                protocol.max_speeds['X'] = 10  # limit max speed of x to
                                               # 10 mm/s
                protocol.max_speeds['X'] = None  # reset to default

        """
        return self._implementation.get_max_speeds()

    @requires_version(2, 0)
    def commands(self):
        return self._commands

    @requires_version(2, 0)
    def clear_commands(self):
        self._commands.clear()
        if self._unsubscribe_commands:
            self._unsubscribe_commands()

        def on_command(message):
            payload = message.get("payload")
            text = payload.get("text")
            if text is None:
                return

            if message["$"] == "before":
                self._commands.append(text.format(**payload))

        self._unsubscribe_commands = self.broker.subscribe(
            cmd_types.COMMAND, on_command
        )

    @contextlib.contextmanager
    def temp_connect(self, hardware: Union[ThreadManager, SynchronousAdapter]):
        """Connect temporarily to the specified hardware controller.

        This should be used as a context manager:

        .. code-block :: python

            with ctx.temp_connect(hw):
                # do some tasks
                ctx.home()
            # after the with block, the context is connected to the same
            # hardware control API it was connected to before, even if
            # an error occurred in the code inside the with block

        """
        hardware_manager = self._implementation.get_hardware()
        old_hw = hardware_manager.hardware
        old_tc = None
        tc_context = None
        # Cache the current instrument context implementations.
        old_instrument_impls = {
            k: v._implementation for k, v in self._instruments.items() if v
        }
        try:
            hardware_manager.set_hw(hardware)
            for mod_ctx in self._modules:
                if isinstance(mod_ctx, ThermocyclerContext):
                    tc_context = mod_ctx
                    hw_tc = next(
                        hw_mod
                        for hw_mod in hardware.attached_modules
                        if hw_mod.name() == "thermocycler"
                    )
                    if hw_tc:
                        old_tc = mod_ctx._module
                        mod_ctx._module = hw_tc

            # InstrumentContextSimulation is an implementation that has no
            # interaction with hardware controller. This is our fast
            # simulation.
            # InstrumentContext objects using an InstrumentContextSimulation
            # must create an InstrumentContextImplementation in order to
            # actually connect the InstrumentContext to the hardware
            # connection.
            for instrument_ctx in self._instruments.values():
                if not instrument_ctx:
                    continue
                impl = instrument_ctx._implementation
                if isinstance(impl, InstrumentContextSimulation):
                    instrument_ctx._implementation = InstrumentContextImplementation(
                        protocol_interface=self._implementation,
                        mount=impl.get_mount(),
                        default_speed=impl.get_default_speed(),
                        instrument_name=impl.get_instrument_name(),
                        api_version=self._api_version,
                    )

            yield self
        finally:
            hardware_manager.set_hw(old_hw)
            if tc_context is not None and old_tc is not None:
                tc_context._module = old_tc
            # reset the instrument context implementations.
            for mount, instrument_impl in old_instrument_impls.items():
                instrument_context = self._instruments[mount]
                if instrument_context:
                    instrument_context._implementation = instrument_impl

    @requires_version(2, 0)
    def connect(self, hardware: Union[ThreadManager, SynchronousAdapter]):
        """Connect to a running hardware API.

        This can be either a simulator or a full hardware controller.

        Note that there is no true disconnected state for a
        :py:class:`.ProtocolContext`; :py:meth:`disconnect` simply creates
        a new simulator and replaces the current hardware with it.
        """
        self._implementation.connect(hardware=hardware)

    @requires_version(2, 0)
    def disconnect(self):
        """Disconnect from currently-connected hardware and simulate instead"""
        self._implementation.disconnect()

    @requires_version(2, 0)
    def is_simulating(self) -> bool:
        return self._implementation.is_simulating()

    @requires_version(2, 0)
    def load_labware_from_definition(
        self,
        labware_def: "LabwareDefinition",
        location: types.DeckLocation,
        label: Optional[str] = None,
    ) -> Labware:
        """Specify the presence of a piece of labware on the OT2 deck.

        This function loads the labware definition specified by `labware_def`
        to the location specified by `location`.

        :param labware_def: The labware definition to load
        :param location: The slot into which to load the labware such as
                         1 or '1'
        :type location: int or str
        :param str label: An optional special name to give the labware. If
                          specified, this is the name the labware will appear
                          as in the run log and the calibration view in the
                          Opentrons app.
        """
        implementation = self._implementation.load_labware_from_definition(
            labware_def=labware_def, location=location, label=label
        )
        result = Labware(implementation=implementation)

        result_namespace, result_load_name, result_version = result.uri.split("/")
        self.labware_load_broker.publish(
            LabwareLoadInfo(
                labware_definition=result._implementation.get_definition(),
                labware_namespace=result_namespace,
                labware_load_name=result_load_name,
                labware_version=int(result_version),
                deck_slot=types.DeckSlotName.from_primitive(location),
            )
        )

        return result

    @requires_version(2, 0)
    def load_labware(
        self,
        load_name: str,
        location: types.DeckLocation,
        label: Optional[str] = None,
        namespace: Optional[str] = None,
        version: Optional[int] = None,
    ) -> Labware:
        """Load a labware onto the deck given its name.

        For labware already defined by Opentrons, this is a convenient way
        to collapse the two stages of labware initialization (creating
        the labware and adding it to the protocol) into one.

        This function returns the created and initialized labware for use
        later in the protocol.

        :param load_name: A string to use for looking up a labware definition
        :param location: The slot into which to load the labware such as
                         1 or '1'
        :type location: int or str
        :param str label: An optional special name to give the labware. If
                          specified, this is the name the labware will appear
                          as in the run log and the calibration view in the
                          Opentrons app.
        :param str namespace: The namespace the labware definition belongs to.
            If unspecified, will search 'opentrons' then 'custom_beta'
        :param int version: The version of the labware definition. If
            unspecified, will use version 1.
        """
        implementation = self._implementation.load_labware(
            load_name=load_name,
            location=location,
            label=label,
            namespace=namespace,
            version=version,
        )
        result = Labware(implementation=implementation)

        result_namespace, result_load_name, result_version = result.uri.split("/")
        self.labware_load_broker.publish(
            LabwareLoadInfo(
                labware_definition=result._implementation.get_definition(),
                labware_namespace=result_namespace,
                labware_load_name=result_load_name,
                labware_version=int(result_version),
                deck_slot=types.DeckSlotName.from_primitive(location),
            )
        )

        return result

    @requires_version(2, 0)
    def load_labware_by_name(
        self,
        load_name: str,
        location: types.DeckLocation,
        label: Optional[str] = None,
        namespace: Optional[str] = None,
        version: int = 1,
    ) -> Labware:
        """
        .. deprecated:: 2.0
            Use :py:meth:`load_labware` instead.
        """
        logger.warning("load_labware_by_name is deprecated. Use load_labware instead.")
        return self.load_labware(load_name, location, label, namespace, version)

    @property  # type: ignore
    @requires_version(2, 0)
    def loaded_labwares(self) -> Dict[int, Labware]:
        """Get the labwares that have been loaded into the protocol context.

        Slots with nothing in them will not be present in the return value.

        .. note::

            If a module is present on the deck but no labware has been loaded
            into it with ``module.load_labware()``, there will
            be no entry for that slot in this value. That means you should not
            use ``loaded_labwares`` to determine if a slot is available or not,
            only to get a list of labwares. If you want a data structure of all
            objects on the deck regardless of type, see :py:attr:`deck`.


        :returns: Dict mapping deck slot number to labware, sorted in order of
                  the locations.
        """

        def _only_labwares() -> Iterator[Tuple[int, Labware]]:
            for slotnum, slotitem in self._implementation.get_deck().items():
                if isinstance(slotitem, AbstractLabware):
                    yield slotnum, Labware(implementation=slotitem)
                elif isinstance(slotitem, Labware):
                    yield slotnum, slotitem
                elif isinstance(slotitem, ModuleGeometry):
                    if slotitem.labware:
                        yield slotnum, slotitem.labware

        return dict(_only_labwares())

    @requires_version(2, 0)
    def load_module(
        self,
        module_name: str,
        location: Optional[types.DeckLocation] = None,
        configuration: Optional[str] = None,
    ) -> ModuleTypes:
        """Load a module onto the deck given its name.

        This is the function to call to use a module in your protocol, like
        :py:meth:`load_instrument` is the method to call to use an instrument
        in your protocol. It returns the created and initialized module
        context, which will be a different class depending on the kind of
        module loaded.

        A map of deck positions to loaded modules can be accessed later
        using :py:attr:`loaded_modules`.

        :param str module_name: The name or model of the module.
        :param location: The location of the module. This is usually the
                         name or number of the slot on the deck where you
                         will be placing the module. Some modules, like
                         the Thermocycler, are only valid in one deck
                         location. You do not have to specify a location
                         when loading a Thermocycler - it will always be
                         in Slot 7.
        :param configuration: Used to specify the slot configuration of
                              the Thermocycler. Only Valid in Python API
                              Version 2.4 and later. If you wish to use
                              the non-full plate configuration, you must
                              pass in the key word value `semi`
        :type location: str or int or None
        :returns: The loaded and initialized module---a
                  :py:class:`TemperatureModuleContext`,
                  :py:class:`ThermocyclerContext`, or
                  :py:class:`MagneticModuleContext`,
                  depending on what you requested with ``module_name``.
        """
        if self._api_version < APIVersion(2, 4) and configuration:
            raise APIVersionError(
                f"You have specified API {self._api_version}, but you are"
                "using thermocycler parameters only available in 2.4"
            )

        module = self._implementation.load_module(
            module_name=module_name, location=location, configuration=configuration
        )

        if not module:
            raise RuntimeError(f"Could not find specified module: {module_name}")

        mod_class = {
            ModuleType.MAGNETIC: MagneticModuleContext,
            ModuleType.TEMPERATURE: TemperatureModuleContext,
            ModuleType.THERMOCYCLER: ThermocyclerContext,
        }[module.type]

        module_context = mod_class(
            self, module.module, module.geometry, self.api_version, self._loop
        )
        self._modules.append(module_context)
        module_loc = module.geometry.parent
        assert isinstance(module_loc, (int, str)), "Unexpected labware object parent"
        deck_slot = types.DeckSlotName.from_primitive(module_loc)
        self.module_load_broker.publish(
            ModuleLoadInfo(
                module_name=module_name,
                deck_slot=deck_slot,
                configuration=configuration,
            )
        )
        return module_context

    @property  # type: ignore
    @requires_version(2, 0)
    def loaded_modules(self) -> Dict[int, "ModuleContext"]:
        """Get the modules loaded into the protocol context.

        This is a map of deck positions to modules loaded by previous calls
        to :py:meth:`load_module`. It is not necessarily the same as the
        modules attached to the robot - for instance, if the robot has a
        Magnetic Module and a Temperature Module attached, but the protocol
        has only loaded the Temperature Module with :py:meth:`load_module`,
        only the Temperature Module will be present.

        :returns Dict[str, ModuleContext]: Dict mapping slot name to module
                                           contexts. The elements may not be
                                           ordered by slot number.
        """

        def _modules() -> Iterator[Tuple[int, "ModuleContext"]]:
            for module in self._modules:
                yield int(str(module.geometry.parent)), module

        return OrderedDict(_modules())

    @requires_version(2, 0)
    def load_instrument(
        self,
        instrument_name: str,
        mount: Union[types.Mount, str],
        tip_racks: List[Labware] = None,
        replace: bool = False,
    ) -> "InstrumentContext":
        """Load a specific instrument required by the protocol.

        This value will actually be checked when the protocol runs, to
        ensure that the correct instrument is attached in the specified
        location.

        :param str instrument_name: The name of the instrument model, or a
                                    prefix. For instance, 'p10_single' may be
                                    used to request a P10 single regardless of
                                    the version.
        :param mount: The mount in which this instrument should be attached.
                      This can either be an instance of the enum type
                      :py:class:`.types.Mount` or one of the strings `'left'`
                      and `'right'`.
        :type mount: types.Mount or str
        :param tip_racks: A list of tip racks from which to pick tips if
                          :py:meth:`.InstrumentContext.pick_up_tip` is called
                          without arguments.
        :type tip_racks: List[:py:class:`.Labware`]
        :param bool replace: Indicate that the currently-loaded instrument in
                             `mount` (if such an instrument exists) should be
                             replaced by `instrument_name`.
        """
        if isinstance(mount, str):
            try:
                checked_mount = types.Mount[mount.upper()]
            except KeyError:
                raise ValueError(
                    "If mount is specified as a string, it should be either"
                    "'left' or 'right' (ignoring capitalization, which the"
                    " system strips), not {}".format(mount)
                )
        elif isinstance(mount, types.Mount):
            checked_mount = mount
        else:
            raise TypeError(
                "mount should be either an instance of opentrons.types.Mount"
                " or a string, but is {}.".format(mount)
            )
        logger.info(
            "Trying to load {} on {} mount".format(
                instrument_name, checked_mount.name.lower()
            )
        )

        impl = self._implementation.load_instrument(
            instrument_name=instrument_name, mount=checked_mount, replace=replace
        )

        new_instr = InstrumentContext(
            ctx=self,
            broker=self.broker,
            implementation=impl,
            at_version=self.api_version,
            tip_racks=tip_racks,
        )
        self._instruments[checked_mount] = new_instr

        self.instrument_load_broker.publish(
            InstrumentLoadInfo(
                instrument_load_name=instrument_name,
                mount=checked_mount,
            )
        )

        return new_instr

    @property  # type: ignore
    @requires_version(2, 0)
    def loaded_instruments(self) -> Dict[str, "InstrumentContext"]:
        """Get the instruments that have been loaded into the protocol.

        This is a map of mount name to instruments previously loaded with
        :py:meth:`load_instrument`. It is not necessarily the same as the
        instruments attached to the robot - for instance, if the robot has
        an instrument in both mounts but your protocol has only loaded one
        of them with :py:meth:`load_instrument`, the unused one will not
        be present.

        :returns: A dict mapping mount name
                  (``'left'`` or ``'right'``)
                  to the instrument in that mount.
                  If a mount has no loaded instrument,
                  that key will be missing from the dict.
        """
        return {
            mount.name.lower(): instr
            for mount, instr in self._instruments.items()
            if instr
        }

    @publish(command=cmds.pause)
    @requires_version(2, 0)
    def pause(self, msg=None) -> None:
        """Pause execution of the protocol until it's resumed.

        A human can resume the protocol through the Opentrons App.

        This function returns immediately, but the next function call that
        is blocked by a paused robot (anything that involves moving) will
        not return until the protocol is resumed.

        :param str msg: An optional message to show to connected clients. The
            Opentrons App will show this in the run log.
        """
        self._implementation.pause(msg=msg)

    @publish(command=cmds.resume)
    @requires_version(2, 0)
    def resume(self) -> None:
        """Resume the protocol after :py:meth:`pause`.

        .. deprecated:: 2.12
           The Python Protocol API supports no safe way for a protocol to resume itself.
           See https://github.com/Opentrons/opentrons/issues/8209.
           If you're looking for a way for your protocol to resume automatically
           after a period of time, use :py:meth:`delay`.
        """
        self._implementation.resume()

    @publish(command=cmds.comment)
    @requires_version(2, 0)
    def comment(self, msg) -> None:
        """
        Add a user-readable comment string that will be echoed to the Opentrons
        app.

        The value of the message is computed during protocol simulation,
        so cannot be used to communicate real-time information from the robot's
        actual run.
        """
        self._implementation.comment(msg=msg)

    @publish(command=cmds.delay)
    @requires_version(2, 0)
    def delay(self, seconds=0, minutes=0, msg=None):
        """Delay protocol execution for a specific amount of time.

        :param float seconds: A time to delay in seconds
        :param float minutes: A time to delay in minutes

        If both `seconds` and `minutes` are specified, they will be added.
        """
        delay_time = seconds + minutes * 60
        self._implementation.delay(seconds=delay_time, msg=msg)

    @requires_version(2, 0)
    def home(self):
        """Homes the robot."""
        logger.debug("home")
        self._implementation.home()

    @property
    def location_cache(self) -> Optional[types.Location]:
        """The cache used by the robot to determine where it last was."""
        return self._implementation.get_last_location()

    @location_cache.setter
    def location_cache(self, loc: Optional[types.Location]):
        self._implementation.set_last_location(loc)

    @property  # type: ignore
    @requires_version(2, 0)
    def deck(self) -> Deck:
        """The object holding the deck layout of the robot.

        This object behaves like a dictionary with keys for both numeric
        and string slot numbers (for instance, ``protocol.deck[1]`` and
        ``protocol.deck['1']`` will both return the object in slot 1). If
        nothing is loaded into a slot, ``None`` will be present. This object
        is useful for determining if a slot in the deck is free. Rather than
        filtering the objects in the deck map yourself, you can also use
        :py:attr:`loaded_labwares` to see a dict of labwares and
        :py:attr:`loaded_modules` to see a dict of modules. For advanced
        control you can delete an item of labware from the deck with
        e.g. ``del protocol.deck['1']`` to free a slot for new labware.
        (Note that for each slot only the last labware used in a command will
        be available for calibration in the OpenTrons UI, and that the
        tallest labware on the deck will be calculated using only currently
        loaded labware, meaning that the labware loaded should always
        reflect the labware physically on the deck (or be higher than the
        labware on the deck).
        """
        return self._implementation.get_deck()

    @property  # type: ignore
    @requires_version(2, 0)
    def fixed_trash(self) -> Labware:
        """The trash fixed to slot 12 of the robot deck.

        It has one well and should be accessed like labware in your protocol.
        e.g. ``protocol.fixed_trash['A1']``
        """
        trash = self._implementation.get_fixed_trash()
        # TODO AL 20201113 - remove this when DeckLayout only holds
        #  LabwareInterface instances.
        if isinstance(trash, AbstractLabware):
            return Labware(implementation=trash)
        return cast("Labware", trash)

    @requires_version(2, 5)
    def set_rail_lights(self, on: bool):
        """
        Controls the robot rail lights

        :param bool on: If true, turn on rail lights; otherwise, turn off.
        """
        self._implementation.set_rail_lights(on=on)

    @property  # type: ignore
    @requires_version(2, 5)
    def rail_lights_on(self) -> bool:
        """Returns True if the rail lights are on"""
        return self._implementation.get_rail_lights_on()

    @property  # type: ignore
    @requires_version(2, 5)
    def door_closed(self) -> bool:
        """Returns True if the robot door is closed"""
        return self._implementation.door_closed()
