import { useSelector } from 'react-redux'
import { getProtocolData, getProtocolName } from '../../redux/protocol'

import type { ProtocolFileV5 } from '@opentrons/shared-data'
import type { State } from '../../redux/types'

interface ProtocolDetails {
  displayName: string | null
  protocolData: ProtocolFileV5<{}> | null // TODO: IMMEDIATELY update to ProtocolFileV6 once schema is complete
}

export function useProtocolDetails(): ProtocolDetails {
  const protocolData = useSelector((state: State) =>
    getProtocolData(state)
  ) as ProtocolFileV5<{}> | null
  const displayName = useSelector((state: State) => getProtocolName(state))
  return { displayName, protocolData }
}

export function useCommandMessage(): string {
  // MOUNT
  // home
  // LOCATION
  // aspirate, dispense, blow_out, pick_up_tip, drop_tip, move_to
  // VOLUME
  // aspirate, dispense, consolidate, distribute,transfer, mix
  // FLOW
  // aspirate, dispense
  // SOURCE
  // consolidate, distribute, transfer
  // DEST
  // consolidate, distribute, transfer
  // REPETITIONS
  // mix, thermocycler_execute_profile
  // TEMP
  // thermocycler_set_lid_temperature, thermocycler_set_block_temp, tempdeck_set_temp, tempdeck_await_temp
  // STEPS
  // thermocycler_execute_profile
  // COMMENT
  // comment
  // MINUTES
  // delay
  // SECONDS
  // delay
  return ''
}
