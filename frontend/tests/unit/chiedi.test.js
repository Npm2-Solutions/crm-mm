// Copyright (c) 2026, NPM2 Solutions Srl and contributors
// A call asked once: a refusal told by its onError leaves no uncaught rejection.
import { chiedi } from '@/utils/chiedi'

const fatte = []
vi.mock('frappe-ui', () => ({
  createResource(opzioni) {
    fatte.push(opzioni)
    return {
      // frappe-ui's own: onError, then the same error thrown again
      fetch: async () => {
        const errore = new Error('refused')
        opzioni.onError?.(errore)
        throw errore
      },
    }
  },
}))

test('a refusal goes to onError, and nothing is left uncaught', async () => {
  const sfuggite = []
  const ascolta = (motivo) => sfuggite.push(motivo)
  process.on('unhandledRejection', ascolta)
  const dette = []
  chiedi({ url: 'x', auto: true, onError: (e) => dette.push(e.message) })
  await new Promise((fatto) => setTimeout(fatto, 10))
  process.off('unhandledRejection', ascolta)
  expect(dette).toEqual(['refused'])
  expect(sfuggite).toEqual([])
  // asked here, never a second time by `auto`
  expect(fatte.at(-1).auto).toBe(false)
})
