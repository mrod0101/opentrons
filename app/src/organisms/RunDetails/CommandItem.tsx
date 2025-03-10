import * as React from 'react'
import { useTranslation } from 'react-i18next'
import {
  DIRECTION_ROW,
  Flex,
  Text,
  C_DARK_GRAY,
  COLOR_ERROR,
  FONT_SIZE_BODY_1,
  C_NEAR_WHITE,
  C_AQUAMARINE,
  C_MINT,
  SPACING_2,
  C_ERROR_LIGHT,
  C_POWDER_BLUE,
  ALIGN_CENTER,
  DIRECTION_COLUMN,
  FONT_SIZE_CAPTION,
  FONT_WEIGHT_BOLD,
  Icon,
  SPACING_1,
  SPACING_3,
  TEXT_TRANSFORM_UPPERCASE,
} from '@opentrons/components'
import { css } from 'styled-components'
import { CommandTimer } from './CommandTimer'
import { CommandText } from './CommandText'
import {
  RUN_STATUS_IDLE,
  RUN_STATUS_PAUSE_REQUESTED,
  RUN_STATUS_PAUSED,
} from '@opentrons/api-client'
import { useCommandQuery } from '@opentrons/react-api-client'
import { useCurrentRunId } from '../ProtocolUpload/hooks/useCurrentRunId'
import type { RunStatus, RunCommandSummary } from '@opentrons/api-client'

import type {
  Command,
  CommandStatus,
} from '@opentrons/shared-data/protocol/types/schemaV6/command'

export interface CommandItemProps {
  commandOrSummary: Command | RunCommandSummary
  runStatus?: RunStatus
}

const WRAPPER_STYLE_BY_STATUS: {
  [status in CommandStatus]: { border: string; backgroundColor: string }
} = {
  queued: { border: 'none', backgroundColor: C_NEAR_WHITE },
  running: {
    border: `1px solid ${C_MINT}`,
    backgroundColor: C_POWDER_BLUE,
  },
  succeeded: {
    border: 'none',
    backgroundColor: C_AQUAMARINE,
  },
  failed: {
    border: `1px solid ${COLOR_ERROR}`,
    backgroundColor: C_ERROR_LIGHT,
  },
}
export function CommandItem(props: CommandItemProps): JSX.Element | null {
  const { commandOrSummary, runStatus } = props
  const commandStatus =
    runStatus !== RUN_STATUS_IDLE && commandOrSummary.status != null
      ? commandOrSummary.status
      : 'queued'

  const currentRunId = useCurrentRunId()
  const {
    data: commandDetails,
    refetch: refetchCommandDetails,
  } = useCommandQuery(currentRunId, commandOrSummary.id)

  React.useEffect(() => {
    refetchCommandDetails()
  }, [commandStatus])

  const WRAPPER_STYLE = css`
    font-size: ${FONT_SIZE_BODY_1};
    background-color: ${WRAPPER_STYLE_BY_STATUS[commandStatus].backgroundColor};
    border: ${WRAPPER_STYLE_BY_STATUS[commandStatus].border};
    padding: ${SPACING_2};
    color: ${C_DARK_GRAY};
    flex-direction: ${DIRECTION_COLUMN};
  `
  return (
    <Flex css={WRAPPER_STYLE}>
      {commandStatus === 'running' ? (
        <CurrentCommandLabel runStatus={runStatus} />
      ) : null}
      <Flex flexDirection={DIRECTION_ROW}>
        {['running', 'failed', 'succeeded'].includes(commandStatus) ? (
          <CommandTimer
            commandStartedAt={commandDetails?.data.startedAt}
            commandCompletedAt={commandDetails?.data.completedAt}
          />
        ) : null}
        {commandStatus === 'failed' ? <CommandFailedMessage /> : null}
        <CommandText
          commandOrSummary={commandDetails?.data ?? commandOrSummary}
        />
      </Flex>
    </Flex>
  )
}

interface CurrentCommandLabelProps {
  runStatus?: RunStatus
}

function CurrentCommandLabel(props: CurrentCommandLabelProps): JSX.Element {
  const { t } = useTranslation('run_details')
  return (
    <Text
      fontWeight={FONT_WEIGHT_BOLD}
      marginBottom={SPACING_1}
      marginTop={SPACING_1}
      textTransform={TEXT_TRANSFORM_UPPERCASE}
      fontSize={FONT_SIZE_CAPTION}
    >
      {props.runStatus === RUN_STATUS_PAUSED ||
      props.runStatus === RUN_STATUS_PAUSE_REQUESTED
        ? t('current_step_pause')
        : t('current_step')}
    </Text>
  )
}

function CommandFailedMessage(): JSX.Element {
  const { t } = useTranslation('run_details')
  return (
    <Flex flexDirection={DIRECTION_ROW} color={COLOR_ERROR}>
      <Flex margin={SPACING_1} width={SPACING_3}>
        <Icon name="information" />
      </Flex>
      <Flex alignItems={ALIGN_CENTER}>{t('step_failed')}</Flex>
    </Flex>
  )
}
