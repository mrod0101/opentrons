For more details about this release, please see the full [technical change
log][]. For a list of currently known issues, please see the [Opentrons issue tracker][].

[technical change log]: https://github.com/Opentrons/opentrons/blob/edge/CHANGELOG.md
[opentrons issue tracker]: https://github.com/Opentrons/opentrons/issues?q=is%3Aopen+is%3Aissue+label%3Abug

---

# OT-2 Software Changes in 4.6.2

## New Features

- The `opentrons_simulate` command-line application can now estimate protocol duration using the `-e` option. This feature is experimental, but very cool!

## Bug Fixes

- If a protocol is canceled mid-run while there is a tip on a pipette, the tip will be dropped prior to resetting the plunger to avoid contaminating the pipette internals with liquids.
- Fixed a movement planning issue that could cause multi-channel pipettes to collide with the deck when changing pipettes.
- Fixed an issue that could cause the protocol to proceed before an awaited temperature module target was actually hit.
- Fixed a few issues with the faster protocol analysis method added in the 4.5.0 release.
- Fixed type annotations of the `ProtocolContext` classes.

## 4.6.1 to 4.6.2

The 4.6.2 hotfix release contains a small bug fix for an issue where the OT-2's max speed settings within a protocol will be ignored.

## 4.6.0 to 4.6.1

The 4.6.1 hotfix release contains a small configuration change to fix an issue with installing the `opentrons` PyPI package on computers running Python 3.8 and later. It does not affect the software running on your OT-2.

## Known Issues

In 4.6.0 and previous releases, the OT-2 will only use TLS 1.0 for WPA2 Enterprise association. Some RADIUS servers have disabled this version of TLS; it must be enabled to connect the OT-2 to a RADIUS-secured network.

Since version 4.5.0, if a thermocycler encounters an error, the robot will be unable to recognize the error state. If your thermocycler starts blinking its yellow LED, you should cancel your protocol. See issue [8393][] for more details.

[8393]: https://github.com/Opentrons/opentrons/issues/8393

---

## OT-2 Software Changes in 4.5.0

The 4.5.0 release of the OT-2 Software improves the speed of protocol uploads and fixes a handful of regressions and bugs.

### New Features

- The OT-2 now uses a faster analysis method on protocol upload
  - Thanks to everyone who beta tested this feature over the last few months!
  - You may revert to the old analysis method with the **Use Older Protocol Analysis Method** in your OT-2's advanced settings
  - If you encounter any issues (e.g. protocol run errors not caught during upload) please reach out to Opentrons Support or [open an issue][] in GitHub so we can continue to improve this feature

### Bug Fixes

- Fixed a regression that prevented use of OT-2 Modules in Jupyter notebook ([#8009][])
- Fixed an uncaught import error on macOS and Windows ([#8154][], thanks to [Maksim Rakitin][] for the fix!)
- Fixed a crash caused by invalid calibration data ([#7962][])

### Known Issues

In 4.5.0 and previous releases, the OT-2 will only use TLS 1.0 for WPA2 Enterprise association. Some RADIUS servers have disabled this version of TLS; it must be enabled to connect the OT-2 to a RADIUS-secured network.

[#7962]: https://github.com/Opentrons/opentrons/issues/7962
[#8009]: https://github.com/Opentrons/opentrons/issues/8009
[#8154]: https://github.com/Opentrons/opentrons/issues/8154
[maksim rakitin]: https://github.com/mrakitin
[open an issue]: https://github.com/Opentrons/opentrons/issues

---

## OT-2 Software Changes in 4.4.0

### New Features

- Triggering a `move_to` to a labware will now count the labware as "used" in the protocol, allowing it to show up in the calibration list ([#7812][])
- Various documentation and error message improvements

### Bug Fixes

- A new Protocol API version was added - `2.11` - to ensure that liquid handling commands like `aspirate` and `dispense` will reject if the source or destination labware is a tip rack (thanks to [@andeecode] for reporting [#7552][]!)
- The robot's built-in HTTP server now sends the correct headers for CORS (thanks to [Benedict Diederich][] for reporting [#7599]!)
- Added guards to prevent resumptions from a delay overriding higher priority pauses ([#7773][])
- Fixed several memory leaks in module handling that could lead to spurious error logs and other issues ([#7641][] and [#7690][])

### Known Issues

In 4.4.0 and previous releases, the OT-2 will only use TLS 1.0 for WPA2 Enterprise association. Some RADIUS servers have disabled this version of TLS; it must be enabled to connect the OT-2 to a RADIUS-secured network.

[@andeecode]: https://github.com/andeecode
[benedict diederich]: https://github.com/beniroquai
[#7552]: https://github.com/Opentrons/opentrons/issues/7552
[#7599]: https://github.com/Opentrons/opentrons/issues/7599
[#7641]: https://github.com/Opentrons/opentrons/issues/7641
[#7690]: https://github.com/Opentrons/opentrons/issues/7690
[#7773]: https://github.com/Opentrons/opentrons/issues/7773
[#7812]: https://github.com/Opentrons/opentrons/issues/7812

---

## OT-2 Software Changes in 4.3.1

OT-2 software 4.3.0 brings a major new feature: the ability to use multiple modules of the same type in a protocol. For instance, you can use two Opentrons Temperature modules in a protocol at the same time. There are also several bugfixes.

### New Features

- The OT-2 now supports the use of two Magnetic Modules or two Temperature Modules in the same Python API protocol. See our Help Center article on [using modules of the same type](https://support.opentrons.com/en/articles/5167312-using-modules-of-the-same-type-on-the-ot-2) for an overview of how this feature should be configured.
- New API level: 2.10. This API level contains a bugfix for an issue where pipettes would move diagonally when accessing the same well one after another ([#7156](https://github.com/Opentrons/opentrons/issues/7156)). The fix is only applied when API Level 2.10 is requested in a protocol to avoid changing the behavior of existing protocols.

### Bugfixes

- Fixes an issue causing slow protocol uploads in protocols using Thermocycler Modules or Temperature Modules ([#7506](https://github.com/Opentrons/opentrons/issues/7506))
- Fixes an issue where labware could not have a 0 column. You can now once again create custom labware with a column 0 ([#7531](https://github.com/Opentrons/opentrons/issues/7531))
- Fixes an issue where tip length calibration would not be applied during labware calibration, so calibrating labware would cause incorrect movement during protocol runes ([#7765](https://github.com/Opentrons/opentrons/issues/7765))

### Known Issues

In 4.3.1 and previous releases, the OT-2 will only use TLS 1.0 for WPA2 Enterprise association. Some RADIUS servers have disabled this version of TLS; it must be enabled to connect the OT-2 to a RADIUS-secured network.

---

## OT-2 Software Changes in 4.2.1

This is a hotfix to prevent crashing in the Z axis with one pipette. You must re-calibrate your pipette offset and your labware before proceeding to a run if you are
experiencing this issue.

### Bugfixes

- Fixed an issue where tip length calibration was not being accessed correctly during a protocol run, and labware calibration.
  - If you performed pipette calibration in 4.2.0, you will need to re-do that calibration upon this update.

### Known Issues

In 4.2.1 and previous releases, the OT-2 will only use TLS 1.0 for WPA2 Enterprise association. Some RADIUS servers have disabled this version of TLS; it must be enabled to connect the OT-2 to a RADIUS-secured network.

---

## OT-2 Software Changes in 4.2.0

### Bugfixes

- Fixed an issue where the pipette or pipette mount would not descend far enough to access the mounting screws when changing the pipette
- Fixed an issue that would cause the left and right pipettes to be at different heights, even after executing pipette calibration
  - If you are experiencing this issue, you should recalibrate your pipettes after updating.
- Fixed an issue where the OT-2 would be unable to connect to Wi-Fi networks using 802.1x Fast Migration.

### Known Issues

In 4.2.0 and previous releases, the OT-2 will only use TLS 1.0 for WPA2 Enterprise association. Some RADIUS servers have disabled this version of TLS; it must be enabled to connect the OT-2 to a RADIUS-secured network.

---

## OT-2 Software Changes in 4.1.1

This is a hotfix for an issue with package installation; it does not include any behavioral changes for the OT-2.

### Bugfixes

- Fixed an issue where the version of the pyserial dependency in the `opentrons` package metadata did not match the version installed on the OT-2, which would cause installation of Python packages that depend on the `opentrons` package to the robot to fail ([#7250](https://github.com/Opentrons/opentrons/pull/7250))

---

## OT-2 Software Changes in 4.1.0

Opentrons Robot Software 4.1.0 brings support for some new robot calibration features and some bugfixes. It also brings a new Protocol API level.

### Calibration Changes

- You can now choose any standard or custom tiprack of appropriate volume to use when calibrating your pipette
- You can now jog in Z when calibrating to deck markings

### Protocol API Level 2.9

- In Python Protocol API Level 2.9, we added accessors for well properties that had previously been undocumented. To see more details, see [the documentation](http://docs.opentrons.com/v2/new_labware.html#new-labware-well-properties).

## Bug Fixes

- Fixed an issue that prevented calibration of labware in slots 10 and 11 while using a single channel pipette ([#6886](https://github.com/opentrons/opentrons/issues/6886))
- Protocol upload should be much faster

---

## OT-2 Software Changes in 4.0.0

Opentrons Robot Software 4.0.0 is a major software release, bringing an entirely overhauled robot calibration process for the OT-2; a full switch to Opentrons Protocol API Version 2; and improvements to the OT-2's HTTP API.

**After you install this update, you must calibrate your OT-2's pipette offsets and tip lengths before running a protocol.** This will take approximately fifteen minutes, but you will not be able to run a protocol until your OT-2 is calibrated.

In addition, **after you install this update, Opentrons Apps on version 3.21.2 or earlier will not be able to interact with this OT-2 beyond downgrading its software**. This is due to the HTTP API changes described below. Opentrons App Version 4.0.0 is designed to work with the changes, but 3.21.2 and previous cannot interact with an OT-2 on Robot Software 4.0.0 other than downgrading its software.

### OT-2 Calibration Changes

In Opentrons App and Robot Software 4.0.0, the calibration process for the OT-2 is different and improved from major version 3. With these changes, you'll calibrate less often; the calibration processes are shorter, easier, and more reliable; and you can finally use different kinds of tips on the same pipette in the same protocol accurately.

For more in-depth information on the changes, [click here](https://support.opentrons.com/en/articles/3499692-how-calibration-works-on-the-ot-2).

### Full Use of Python Protocol API Version 2

We released Python Protocol API Version 2 almost a year ago, and have been continuously improving it since, with 8 new intermediate API levels, each containing bugfixes, improvements, or support for new hardware. It's ready to be the only way Python protocols are written for the OT-2. Accordingly, in 4.0.0 and subsequent releases, **the OT-2 will not accept Python Protocol API Version 1 protocols**.

### HTTP API Changes

Robot Software 4.0.0 is a big step forward in a well-defined, stable, HTTP API for the OT-2. This API is what the Opentrons App uses to communicate with the OT-2, and documentation for it is available on the OT-2's IP address, port 31950 at `/docs`. In Robot Software 4.0.0, interaction with this API now requires use of the `Opentrons-Version` header, set to either `*` (to accept any version) or `2`.

We consider the HTTP API a core part of the OT-2's API, and changes to it will be documented in release notes just like Python Protocol API changes.

### Other Changes

- New Python Protocol API version: 2.8
  - You can now specify blow out locations in `transfer`, `consolidate`, and `distribute` to be the source well, destination well, or trash
  - `Well` now has the method `from_center_cartesian`, which allows you to calculate positions relative to the well center in X, Y, and Z
  - For more information, see [the Python Protocol API documentation](https://docs.opentrons.com/v2/versioning.html#version-2-8)
- Protocol Designer protocols will now always be executed with API Version 2.8 behaviors
  - Future changes to the behavior executed in Protocol Designer protocols will be communicated here
- `transfer`, `consolidate`, and `distribute` will now do nothing if passed a 0 transfer volume.
