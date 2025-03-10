import _protocolWithMagTempTC from '@opentrons/shared-data/protocol/fixtures/6/transferSettings.json'
import _standardDeckDef from '@opentrons/shared-data/deck/definitions/2/ot2_standard.json'
import { getLabwareRenderInfo } from '../utils/getLabwareRenderInfo'
import { ProtocolFile } from '@opentrons/shared-data'

const protocolWithMagTempTC = (_protocolWithMagTempTC as unknown) as ProtocolFile<{}>
const standardDeckDef = _standardDeckDef as any

describe('getLabwareRenderInfo', () => {
  it('should gather labware coordinates with module offsets', () => {
    // these are just taken from the ot-2 deck def for readability
    const SLOT_2_COORDS = [132.5, 0.0, 0.0]
    const SLOT_4_COORDS = [0.0, 90.5, 0.0]
    const SLOT_5_COORDS = [132.5, 90.5, 0.0]
    const SLOT_6_COORDS = [265.0, 90.5, 0.0]
    const SLOT_9_COORDS = [265.0, 181.0, 0.0]

    // module ids come from the fixture protocol, they are just here for readability
    const OPENTRONS_96_TIPRACK_1000UL_TIPRACK_ID =
      '3e047fb0-3412-11eb-ad93-ed232a2337cf:opentrons/opentrons_96_tiprack_1000ul/1'
    const NEST_1_RESEVOIR_195ML_ID =
      '5ae317e0-3412-11eb-ad93-ed232a2337cf:opentrons/nest_1_reservoir_195ml/1'
    const CORNING_24_WELLPLATE_1_ID = '53d3b350-a9c0-11eb-bce6-9f1d5b9c1a1b'
    const CORNING_24_WELLPLATE_2_ID =
      '60e8b050-3412-11eb-ad93-ed232a2337cf:opentrons/corning_24_wellplate_3.4ml_flat/1'
    const OPENTRONS_96_TIPRACK_20UL_TIPRACK_ID =
      'faa13a50-a9bf-11eb-bce6-9f1d5b9c1a1b:opentrons/opentrons_96_tiprack_20ul/1'
    const expected = {
      // slot 1 has mag mod
      // slot 2
      [OPENTRONS_96_TIPRACK_1000UL_TIPRACK_ID]: {
        labwareDef: expect.anything(),
        x: SLOT_2_COORDS[0],
        y: SLOT_2_COORDS[1],
        z: SLOT_2_COORDS[2],
      },
      // slot 3 has temp mod
      // slot 4
      [NEST_1_RESEVOIR_195ML_ID]: {
        labwareDef: expect.anything(),
        x: SLOT_4_COORDS[0],
        y: SLOT_4_COORDS[1],
        z: SLOT_4_COORDS[2],
      },
      // slot 5
      [CORNING_24_WELLPLATE_2_ID]: {
        labwareDef: expect.anything(),
        x: SLOT_5_COORDS[0],
        y: SLOT_5_COORDS[1],
        z: SLOT_5_COORDS[2],
      },
      // slot 6
      [CORNING_24_WELLPLATE_1_ID]: {
        labwareDef: expect.anything(),
        x: SLOT_6_COORDS[0],
        y: SLOT_6_COORDS[1],
        z: SLOT_6_COORDS[2],
      },
      // slot 7 has TC
      // slot 9
      [OPENTRONS_96_TIPRACK_20UL_TIPRACK_ID]: {
        labwareDef: expect.anything(),
        x: SLOT_9_COORDS[0],
        y: SLOT_9_COORDS[1],
        z: SLOT_9_COORDS[2],
      },
    }

    expect(
      getLabwareRenderInfo(protocolWithMagTempTC, standardDeckDef)
    ).toEqual(expected)
  })
})
