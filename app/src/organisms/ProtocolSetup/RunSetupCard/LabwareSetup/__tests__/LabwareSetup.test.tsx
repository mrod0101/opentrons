import * as React from 'react'
import { when, resetAllWhenMocks } from 'jest-when'
import { StaticRouter } from 'react-router-dom'
import {
  renderWithProviders,
  componentPropsMatcher,
  partialComponentPropsMatcher,
  LabwareRender,
  RobotWorkSpace,
  Module,
} from '@opentrons/components'
import {
  inferModuleOrientationFromXCoordinate,
  LabwareDefinition2,
  ModuleModel,
  ModuleType,
} from '@opentrons/shared-data'
import fixture_tiprack_300_ul from '@opentrons/shared-data/labware/fixtures/2/fixture_tiprack_300_ul.json'
import standardDeckDef from '@opentrons/shared-data/deck/definitions/2/ot2_standard.json'
import { fireEvent, screen } from '@testing-library/react'
import { i18n } from '../../../../../i18n'
import { LabwarePositionCheck } from '../../../LabwarePositionCheck'
import {
  useModuleRenderInfoById,
  useLabwareRenderInfoById,
} from '../../../hooks'
import { LabwareSetup } from '..'
import { LabwareOffsetModal } from '../LabwareOffsetModal'
import { LabwareInfoOverlay } from '../LabwareInfoOverlay'
import { ExtraAttentionWarning } from '../ExtraAttentionWarning'
import { getModuleTypesThatRequireExtraAttention } from '../utils/getModuleTypesThatRequireExtraAttention'

jest.mock('../../../../../redux/modules')
jest.mock('../../../../../redux/pipettes/selectors')
jest.mock('../LabwareOffsetModal')
jest.mock('../../../LabwarePositionCheck')
jest.mock('../LabwareInfoOverlay')
jest.mock('../ExtraAttentionWarning')
jest.mock('../../../hooks')
jest.mock('../utils/getModuleTypesThatRequireExtraAttention')
jest.mock('@opentrons/components', () => {
  const actualComponents = jest.requireActual('@opentrons/components')
  return {
    ...actualComponents,
    Module: jest.fn(() => <div>mock Module</div>),
    RobotWorkSpace: jest.fn(() => <div>mock RobotWorkSpace</div>),
    LabwareRender: jest.fn(() => <div>mock LabwareRender</div>),
  }
})
jest.mock('@opentrons/shared-data', () => {
  const actualSharedData = jest.requireActual('@opentrons/shared-data')
  return {
    ...actualSharedData,
    inferModuleOrientationFromXCoordinate: jest.fn(),
  }
})
const mockLabwareInfoOverlay = LabwareInfoOverlay as jest.MockedFunction<
  typeof LabwareInfoOverlay
>

const mockModule = Module as jest.MockedFunction<typeof Module>
const mockInferModuleOrientationFromXCoordinate = inferModuleOrientationFromXCoordinate as jest.MockedFunction<
  typeof inferModuleOrientationFromXCoordinate
>

const mockRobotWorkSpace = RobotWorkSpace as jest.MockedFunction<
  typeof RobotWorkSpace
>
const mockLabwareRender = LabwareRender as jest.MockedFunction<
  typeof LabwareRender
>
const mockLabwareOffsetModal = LabwareOffsetModal as jest.MockedFunction<
  typeof LabwareOffsetModal
>
const mockGetModuleTypesThatRequireExtraAttention = getModuleTypesThatRequireExtraAttention as jest.MockedFunction<
  typeof getModuleTypesThatRequireExtraAttention
>
const mockExtraAttentionWarning = ExtraAttentionWarning as jest.MockedFunction<
  typeof ExtraAttentionWarning
>
const mockUseLabwareRenderInfoById = useLabwareRenderInfoById as jest.MockedFunction<
  typeof useLabwareRenderInfoById
>
const mockUseModuleRenderInfoById = useModuleRenderInfoById as jest.MockedFunction<
  typeof useModuleRenderInfoById
>
const mockLabwarePostionCheck = LabwarePositionCheck as jest.MockedFunction<
  typeof LabwarePositionCheck
>

const deckSlotsById = standardDeckDef.locations.orderedSlots.reduce(
  (acc, deckSlot) => ({ ...acc, [deckSlot.id]: deckSlot }),
  {}
)

const render = () => {
  return renderWithProviders(
    <StaticRouter>
      <LabwareSetup />
    </StaticRouter>,
    {
      i18nInstance: i18n,
    }
  )[0]
}

const STUBBED_ORIENTATION_VALUE = 'left'
const MOCK_300_UL_TIPRACK_ID = '300_ul_tiprack_id'
const MOCK_MAGNETIC_MODULE_COORDS = [10, 20, 0]
const MOCK_TC_COORDS = [20, 30, 0]
const MOCK_300_UL_TIPRACK_COORDS = [30, 40, 0]

const mockMagneticModule = {
  labwareOffset: { x: 5, y: 5, z: 5 },
  moduleId: 'someMagneticModule',
  model: 'magneticModuleV2' as ModuleModel,
  type: 'magneticModuleType' as ModuleType,
}

const mockTCModule = {
  labwareOffset: { x: 3, y: 3, z: 3 },
  moduleId: 'TCModuleId',
  model: 'thermocyclerModuleV1' as ModuleModel,
  type: 'thermocyclerModuleType' as ModuleType,
}

describe('LabwareSetup', () => {
  beforeEach(() => {
    when(mockInferModuleOrientationFromXCoordinate)
      .calledWith(expect.anything())
      .mockReturnValue(STUBBED_ORIENTATION_VALUE)

    when(mockGetModuleTypesThatRequireExtraAttention)
      .calledWith(expect.anything())
      .mockReturnValue([])

    when(mockLabwareOffsetModal)
      .calledWith(
        componentPropsMatcher({
          onCloseClick: expect.anything(),
        })
      )
      .mockImplementation(({ onCloseClick }) => (
        <div onClick={onCloseClick}>mock LabwareOffsetModal </div>
      ))

    when(mockLabwareRender)
      .mockReturnValue(<div></div>) // this (default) empty div will be returned when LabwareRender isn't called with expected labware definition
      .calledWith(
        componentPropsMatcher({
          definition: fixture_tiprack_300_ul,
        })
      )
      .mockReturnValue(
        <div>
          mock labware render of {fixture_tiprack_300_ul.metadata.displayName}
        </div>
      )

    when(mockLabwareInfoOverlay)
      .mockReturnValue(<div></div>) // this (default) empty div will be returned when LabwareInfoOverlay isn't called with expected props
      .calledWith(componentPropsMatcher({ definition: fixture_tiprack_300_ul }))
      .mockReturnValue(
        <div>
          mock labware info overlay of{' '}
          {fixture_tiprack_300_ul.metadata.displayName}
        </div>
      )

    when(mockRobotWorkSpace)
      .mockReturnValue(<div></div>) // this (default) empty div will be returned when RobotWorkSpace isn't called with expected props
      .calledWith(
        partialComponentPropsMatcher({
          deckDef: standardDeckDef,
          children: expect.anything(),
        })
      )
      .mockImplementation(({ children }) => (
        <svg>
          {/* @ts-expect-error children won't be null since we checked for expect.anything() above */}
          {children({
            deckSlotsById,
            getRobotCoordsFromDOMCoords: {} as any,
          })}
        </svg>
      ))

    mockLabwarePostionCheck.mockReturnValue(
      <div>mock Labware Position Check</div>
    )
  })

  afterEach(() => {
    resetAllWhenMocks()
    jest.restoreAllMocks()
  })

  describe('See How Labware Offsets Work link', () => {
    it('opens up the See How Labware Offsets Work modal when clicked', () => {
      const { getByText } = render()

      expect(screen.queryByText('mock LabwareOffsetModal')).toBeNull()
      const helpLink = getByText('See How Labware Offsets Work')
      fireEvent.click(helpLink)
      getByText('mock LabwareOffsetModal')
    })
    it('closes the See How Labware Offsets Work when closed', () => {
      const { getByText } = render()

      const helpLink = getByText('See How Labware Offsets Work')
      fireEvent.click(helpLink)
      const mockModal = getByText('mock LabwareOffsetModal')
      fireEvent.click(mockModal)
      expect(screen.queryByText('mock LabwareOffsetModal')).toBeNull()
    })
  })

  it('should render a deck WITHOUT labware and WITHOUT modules', () => {
    when(mockUseLabwareRenderInfoById).calledWith().mockReturnValue({})
    when(mockUseModuleRenderInfoById).calledWith().mockReturnValue({})

    render()
    expect(mockModule).not.toHaveBeenCalled()
    expect(mockLabwareRender).not.toHaveBeenCalled()
    expect(mockLabwareInfoOverlay).not.toHaveBeenCalled()
  })
  it('should render a deck WITH labware and WITHOUT modules', () => {
    when(mockUseLabwareRenderInfoById)
      .calledWith()
      .mockReturnValue({
        '300_ul_tiprack_id': {
          labwareDef: fixture_tiprack_300_ul as LabwareDefinition2,
          x: MOCK_300_UL_TIPRACK_COORDS[0],
          y: MOCK_300_UL_TIPRACK_COORDS[1],
          z: MOCK_300_UL_TIPRACK_COORDS[2],
        },
      })

    when(mockUseModuleRenderInfoById).calledWith().mockReturnValue({})

    const { getByText } = render()
    expect(mockModule).not.toHaveBeenCalled()
    expect(mockLabwareRender).toHaveBeenCalled()
    expect(mockLabwareInfoOverlay).toHaveBeenCalled()
    getByText('mock labware render of 300ul Tiprack FIXTURE')
    getByText('mock labware info overlay of 300ul Tiprack FIXTURE')
  })

  it('should render a deck WITH labware and WITH modules', () => {
    when(mockUseLabwareRenderInfoById)
      .calledWith()
      .mockReturnValue({
        [MOCK_300_UL_TIPRACK_ID]: {
          labwareDef: fixture_tiprack_300_ul as LabwareDefinition2,
          x: MOCK_300_UL_TIPRACK_COORDS[0],
          y: MOCK_300_UL_TIPRACK_COORDS[1],
          z: MOCK_300_UL_TIPRACK_COORDS[2],
        },
      })

    when(mockUseModuleRenderInfoById)
      .calledWith()
      .mockReturnValue({
        [mockMagneticModule.moduleId]: {
          x: MOCK_MAGNETIC_MODULE_COORDS[0],
          y: MOCK_MAGNETIC_MODULE_COORDS[1],
          z: MOCK_MAGNETIC_MODULE_COORDS[2],
          moduleDef: mockMagneticModule as any,
          nestedLabwareDef: null,
          nestedLabwareId: null,
        },
        [mockTCModule.moduleId]: {
          x: MOCK_TC_COORDS[0],
          y: MOCK_TC_COORDS[1],
          z: MOCK_TC_COORDS[2],
          moduleDef: mockTCModule,
          nestedLabwareDef: null,
          nestedLabwareId: null,
        },
      })

    when(mockModule)
      .calledWith(
        partialComponentPropsMatcher({
          def: mockMagneticModule,
          x: MOCK_MAGNETIC_MODULE_COORDS[0],
          y: MOCK_MAGNETIC_MODULE_COORDS[1],
        })
      )
      .mockReturnValue(<div>mock module viz {mockMagneticModule.type} </div>)

    when(mockModule)
      .calledWith(
        partialComponentPropsMatcher({
          def: mockTCModule,
          x: MOCK_TC_COORDS[0],
          y: MOCK_TC_COORDS[1],
        })
      )
      .mockReturnValue(<div>mock module viz {mockTCModule.type} </div>)

    const { getByText } = render()
    getByText('mock module viz magneticModuleType')
    getByText('mock module viz thermocyclerModuleType')
    getByText('mock labware render of 300ul Tiprack FIXTURE')
    getByText('mock labware info overlay of 300ul Tiprack FIXTURE')
  })
  it('should render the Labware Position Check and Labware Offset Data text', () => {
    const { getByText } = render()

    getByText('Labware Position Check and Labware Offset Data')
    getByText(
      'Labware Position Check is an optional workflow that helps you verify the position of each labware on the deck. During this check, you can create Labware Offsets that adjust how the robot moves to each labware in the X, Y and Z directions.'
    )
  })
  it('should render button and click it', () => {
    const { getByRole, getByText } = render()
    const button = getByRole('button', {
      name: 'run labware position check',
    })
    fireEvent.click(button)
    getByText('mock Labware Position Check')
  })
  it('should render the extra attention warning when there are modules/labware that need extra attention', () => {
    when(mockGetModuleTypesThatRequireExtraAttention)
      .calledWith([])
      .mockReturnValue(['magneticModuleType', 'thermocyclerModuleType'])

    when(mockExtraAttentionWarning)
      .calledWith(
        componentPropsMatcher({
          moduleTypes: ['magneticModuleType', 'thermocyclerModuleType'],
        })
      )
      .mockReturnValue(
        <div>mock extra attention warning with magnetic module and TC</div>
      )

    const { getByText } = render()
    getByText('mock extra attention warning with magnetic module and TC')
  })
})
