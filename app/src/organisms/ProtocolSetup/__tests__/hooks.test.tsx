// tests for the HostConfig context and hook
import * as React from 'react'
import { when } from 'jest-when'
import { Provider } from 'react-redux'
import { createStore } from 'redux'
import { renderHook } from '@testing-library/react-hooks'
import { useProtocolMetadata } from '../hooks'
import { useCurrentProtocolRun } from '../../ProtocolUpload/hooks'

import type { Store } from 'redux'
import type { State } from '../../../redux/types'

jest.mock('../../ProtocolUpload/hooks')

const mockUseCurrentProtocolRun = useCurrentProtocolRun as jest.MockedFunction<
  typeof useCurrentProtocolRun
>

describe('useProtocolMetadata', () => {
  const store: Store<State> = createStore(jest.fn(), {})

  when(mockUseCurrentProtocolRun)
    .calledWith()
    .mockReturnValue({
      protocolRecord: {
        data: {
          protocolType: 'json',
          metadata: {
            author: 'AUTHOR',
            description: 'DESCRIPTION',
            lastModified: 123456,
          },
        },
      },
      runRecord: {},
      createProtocolRun: jest.fn(),
    } as any)

  beforeEach(() => {
    store.dispatch = jest.fn()
  })

  afterEach(() => {
    jest.restoreAllMocks()
  })

  it('should return author, lastUpdated, method, and description from redux selectors', () => {
    const wrapper: React.FunctionComponent<{}> = ({ children }) => (
      <Provider store={store}>{children}</Provider>
    )
    const { result } = renderHook(useProtocolMetadata, { wrapper })
    const { author, lastUpdated, creationMethod, description } = result.current

    expect(author).toBe('AUTHOR')
    expect(lastUpdated).toBe(123456)
    expect(creationMethod).toBe('json')
    expect(description).toBe('DESCRIPTION')
  })
})
