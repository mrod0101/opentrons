import * as React from 'react'
import { when, resetAllWhenMocks } from 'jest-when'
import { QueryClient, QueryClientProvider } from 'react-query'
import { renderHook } from '@testing-library/react-hooks'
import { getProtocol } from '@opentrons/api-client'
import { useHost } from '../../api'
import {
  useCreateProtocolMutation,
  UseCreateProtocolMutationResult,
} from '../useCreateProtocolMutation'
import { useNewProtocolDetails } from '..'

import type { HostConfig, Protocol } from '@opentrons/api-client'

jest.mock('@opentrons/api-client')
jest.mock('../../api/useHost')
jest.mock('../useCreateProtocolMutation')
jest.mock('../useProtocolQuery')

const contents = JSON.stringify({
  metadata: {
    protocolName: 'Multi select banner test protocol',
    author: '',
    description: '',
    created: 1606853851893,
    lastModified: 1621690582736,
    category: null,
    subcategory: null,
    tags: [],
  },
})
const jsonFile = new File([contents], 'valid.json')

const mockGetProtocol = getProtocol as jest.MockedFunction<typeof getProtocol>
const mockUseCreateProtocolMutation = useCreateProtocolMutation as jest.MockedFunction<
  typeof useCreateProtocolMutation
>
const mockUseHost = useHost as jest.MockedFunction<typeof useHost>

const HOST_CONFIG: HostConfig = { hostname: 'localhost' }
const PROTOCOL_ID = '1'
const PROTOCOL_RESPONSE = {
  data: {
    protocolType: 'json',
    createdAt: 'now',
    id: '1',
    metaData: {},
    analyses: {},
  },
} as Protocol

describe('useNewProtocolDetails hook', () => {
  let wrapper: React.FunctionComponent<{}>

  beforeEach(() => {
    const queryClient = new QueryClient()
    const clientProvider: React.FunctionComponent<{}> = ({ children }) => (
      <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
    )

    wrapper = clientProvider
  })
  afterEach(() => {
    resetAllWhenMocks()
  })

  it('should not call useProtocolQuery when createProtocolMutation fails', async () => {
    when(mockUseHost).calledWith().mockReturnValue(HOST_CONFIG)
    when(mockUseCreateProtocolMutation)
      .calledWith([jsonFile])
      .mockReturnValue({} as UseCreateProtocolMutationResult)

    const { result } = renderHook(useNewProtocolDetails, {
      wrapper,
    })
    expect(mockGetProtocol).not.toHaveBeenCalled()
  })

  it('should create a call useProtocolQuery when createProtocolMutation returns id', async () => {
    when(mockUseHost).calledWith().mockReturnValue(HOST_CONFIG)
    when(mockUseCreateProtocolMutation)
      .calledWith([jsonFile])
      .mockReturnValue({
        data: PROTOCOL_RESPONSE,
      } as UseCreateProtocolMutationResult)

    renderHook(useNewProtocolDetails, {
      wrapper,
    })
    expect(mockGetProtocol).toHaveBeenCalled()
  })
})
