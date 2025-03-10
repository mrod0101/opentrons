import * as React from 'react'

import {
  AlertModal,
  InputField,
  SecondaryBtn,
  useHoverTooltip,
  Tooltip,
  Text,
  FONT_WEIGHT_SEMIBOLD,
  SPACING_1,
  Flex,
  Box,
  DIRECTION_COLUMN,
  FONT_STYLE_ITALIC,
  FONT_SIZE_BODY_1,
  SPACING_2,
} from '@opentrons/components'
import { Portal } from '../../App/portal'
import { THERMOCYCLER_MODULE_TYPE } from '../../redux/modules'
import { getModuleDisplayName } from '@opentrons/shared-data'
import { useFeatureFlag } from '../../redux/config'

import type {
  ThermocyclerModule,
  TemperatureModule,
  ModuleCommand,
} from '../../redux/modules/types'
import type { ModuleModel } from '@opentrons/shared-data'

interface Props {
  module: ThermocyclerModule | TemperatureModule
  sendModuleCommand: (
    moduleId: string,
    command: ModuleCommand,
    args?: unknown[]
  ) => unknown
  isSecondaryTemp: boolean
  disabledReason?: string | null
}

export const TemperatureControl = ({
  module,
  isSecondaryTemp,
  sendModuleCommand,
  disabledReason,
}: Props): JSX.Element => {
  const isNewProtocolRunPanel = useFeatureFlag('preProtocolFlowWithoutRPC')
  const [tempValue, setTempValue] = React.useState<string | null>(null)
  const [isModalOpen, setIsModalOpen] = React.useState<boolean>(false)
  const [targetProps, tooltipProps] = useHoverTooltip()

  const isThermocycler = module.type === THERMOCYCLER_MODULE_TYPE
  const displayName = getModuleDisplayName(module.model)
  const modulePartName = isThermocycler
    ? isSecondaryTemp
      ? ' Lid'
      : ' Block'
    : ''
  const alertHeading = `Set ${modulePartName} Temperature for ${displayName}`
  const alertBody = `Pre heat or cool your ${displayName}${modulePartName}.`
  const primaryFieldLabel = `Set Temp:`
  const tempRanges = getModuleTemperatureRanges(module.model, isSecondaryTemp)
  const note = `enter a whole-number between ${tempRanges.min}°C and ${tempRanges.max}°C`

  const hasTarget =
    module.type === THERMOCYCLER_MODULE_TYPE && isSecondaryTemp
      ? module.data.lidTarget != null
      : module.status !== 'idle'

  const handleClick = (): void => {
    if (hasTarget) {
      sendModuleCommand(
        module.serial,
        isSecondaryTemp ? 'deactivate_lid' : 'deactivate'
      )
    } else {
      setIsModalOpen(true)
    }
  }

  const handleSubmitTemp = (): void => {
    if (tempValue != null) {
      sendModuleCommand(
        module.serial,
        isSecondaryTemp ? 'set_lid_temperature' : 'set_temperature',
        [Number(tempValue)]
      )
    }
    setTempValue(null)
    setIsModalOpen(false)
  }

  const handleCancel = (): void => {
    setIsModalOpen(false)
    setTempValue(null)
  }

  return (
    <Flex flexDirection={DIRECTION_COLUMN}>
      {!hasTarget && isModalOpen && (
        <Portal>
          <AlertModal
            heading={alertHeading}
            iconName={null}
            buttons={[
              {
                children: 'Cancel',
                onClick: handleCancel,
              },
              {
                children: isNewProtocolRunPanel
                  ? 'Set temperature'
                  : 'Set temp',
                disabled: tempValue == null,
                onClick: handleSubmitTemp,
              },
            ]}
            alertOverlay
          >
            <Text>{alertBody}</Text>
            <Box>
              <Text fontWeight={FONT_WEIGHT_SEMIBOLD}>{primaryFieldLabel}</Text>
              <Flex width="6rem" marginTop={SPACING_1}>
                <InputField
                  units="°C"
                  value={tempValue}
                  onChange={e => setTempValue(e.target.value)}
                />
              </Flex>
              <Text
                fontSize={FONT_SIZE_BODY_1}
                fontStyle={FONT_STYLE_ITALIC}
                marginTop={SPACING_1}
              >
                {note}
              </Text>
            </Box>
          </AlertModal>
        </Portal>
      )}
      {isNewProtocolRunPanel ? (
        <SecondaryBtn
          paddingX={SPACING_2}
          width={'11rem'}
          onClick={handleClick}
          disabled={disabledReason != null}
          {...targetProps}
          fontSize={FONT_SIZE_BODY_1}
        >
          {hasTarget === true
            ? `Deactivate${modulePartName}`
            : `Set${modulePartName} Temperature`}
        </SecondaryBtn>
      ) : (
        <SecondaryBtn
          paddingX={SPACING_2}
          width={'11rem'}
          onClick={handleClick}
          disabled={disabledReason != null}
          {...targetProps}
        >
          {hasTarget === true
            ? `Deactivate${modulePartName}`
            : `Set${modulePartName} Temp`}
        </SecondaryBtn>
      )}
      {disabledReason && <Tooltip {...tooltipProps}>{disabledReason}</Tooltip>}
    </Flex>
  )
}

interface TemperatureRanges {
  min: number
  max: number
}

function getModuleTemperatureRanges(
  model: ModuleModel,
  isSecondaryTemp: boolean
): TemperatureRanges {
  if (isSecondaryTemp && TEMPERATURE_RANGES[model].secondary) {
    return TEMPERATURE_RANGES[model].secondary as TemperatureRanges
  } else {
    return TEMPERATURE_RANGES[model].primary as TemperatureRanges
  }
}

// @ts-expect-error key should be optional as not all models are present
const TEMPERATURE_RANGES: {
  [model in ModuleModel]: {
    primary: TemperatureRanges
    secondary?: TemperatureRanges | null
  }
} = {
  temperatureModuleV1: { primary: { min: 4, max: 96 }, secondary: null },
  temperatureModuleV2: { primary: { min: 4, max: 96 }, secondary: null },
  thermocyclerModuleV1: {
    primary: { min: 4, max: 99 },
    secondary: { min: 37, max: 110 },
  },
}
