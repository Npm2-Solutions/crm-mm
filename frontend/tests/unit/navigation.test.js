import { describe, it, expect } from 'vitest'
import { bottomNavTabFor, currentNavKey } from '@/utils/navigation'

describe('currentNavKey', () => {
  it('is the route, so the entry for it lights up', () => {
    expect(currentNavKey({ name: 'Leads' })).toBe('Leads')
    expect(currentNavKey({ name: 'Conversations' })).toBe('Conversations')
  })

  it('lets a saved view win over the list it is a view of', () => {
    expect(
      currentNavKey({ name: 'Leads', query: { view: 'Da chiamare' } }),
    ).toBe('Da chiamare')
  })

  it('survives being asked about nothing', () => {
    expect(currentNavKey(undefined)).toBeUndefined()
    expect(currentNavKey({})).toBeUndefined()
  })
})

describe('bottomNavTabFor', () => {
  it('keeps a tab lit while you are inside its section', () => {
    // a tab going dark because you opened a record would read as broken
    expect(bottomNavTabFor({ name: 'Lead' })).toBe('Leads')
    expect(bottomNavTabFor({ name: 'Deal' })).toBe('Deals')
  })

  it('lights the chat tab on the conversations screen', () => {
    expect(bottomNavTabFor({ name: 'Conversations' })).toBe('Conversations')
  })

  it('answers nothing for the places with no tab', () => {
    expect(bottomNavTabFor({ name: 'Organizations' })).toBeNull()
    expect(bottomNavTabFor(undefined)).toBeNull()
  })
})
