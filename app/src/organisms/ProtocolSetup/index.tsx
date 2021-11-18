import * as React from 'react'
import {
  DIRECTION_COLUMN,
  SPACING_3,
  Flex,
  AlertItem,
  SPACING_1,
  SPACING_2,
} from '@opentrons/components'
import { RunSetupCard } from './RunSetupCard'
import { MetadataCard } from './MetadataCard'
import { useTranslation } from 'react-i18next'

export function ProtocolSetup(): JSX.Element {
  const { t } = useTranslation('protocol_info')
  const [dismissed, setDismissed] = React.useState(false)

  return (
    <>
      <Flex
        flexDirection={DIRECTION_COLUMN}
        padding={`${SPACING_1} ${SPACING_2} ${SPACING_1} ${SPACING_2}`}
      >
        {!dismissed && (
          <AlertItem
            type="success"
            onCloseClick={() => setDismissed(true)}
            title={t('labware_positon_check_complete_toast', {
              num_offsets: 2, //  TODO wire up num_offsets!
            })}
          />
        )}
      </Flex>
      <Flex
        flexDirection={DIRECTION_COLUMN}
        padding={`${SPACING_1} ${SPACING_3} ${SPACING_3} ${SPACING_3}`}
      >
        <MetadataCard />
        <RunSetupCard />
      </Flex>
    </>
  )
}
