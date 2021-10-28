import { useEffect, useState } from 'react'
import { UseQueryResult, useQuery, useQueryClient } from 'react-query'
import { getProtocol, HostConfig } from '@opentrons/api-client'
import { useHost } from '../api'
import { useCreateProtocolMutation } from '.'
import type { Protocol } from '@opentrons/api-client'

export function useNewProtocolDetails(
  protocolFiles: File[]
): UseQueryResult<Protocol> {
  const host = useHost()
  const queryClient = useQueryClient()
  const [protocolId, setProtocolId] = useState<string | null>(null)
  const [stop, setStop] = useState(false)
  const { data } = useCreateProtocolMutation(protocolFiles)

  useEffect(() => {
    if (data != null) {
      setProtocolId(data.data.id)
    }
  }, [data])

  const query = useQuery(
    [host, 'protocols', protocolId],
    () =>
      // @ts-expect-error protocolId won't be null because it is enabled below
      getProtocol(host as HostConfig, protocolId).then(response => {
        if (response.data.data.analyses.status === 'completed') {
          setStop(true)
          queryClient.setQueryData(
            [host, 'protocols', protocolId],
            response.data
          )
        }
        return response.data
      }),
    {
      // doesn't run this query until the protocolId from the mutation above is available
      enabled: host !== null && protocolId !== null,
      // refetches every 5 seconds until stop is true
      refetchInterval: stop ? false : 5000,
    }
  )

  return query
}
