import { describe, it, expect } from 'vitest'
import { isStandardViewType, standardViewTypesFor } from '@/utils/viewTypes'

describe('which views a list has built in', () => {
  it('gives every list the three it has always had', () => {
    for (const where of ['Leads', 'Deals', 'Contacts', 'Tasks']) {
      expect(standardViewTypesFor(where)).toEqual(
        expect.arrayContaining(['list', 'kanban', 'group_by']),
      )
    }
  })

  it('knows the Inbox is a view of People', () => {
    // left out of this list, the router reads «inbox» as the name of a saved
    // view, finds none, and sends you back to the list — which is what made
    // clicking the Inbox look like nothing happening at all
    expect(isStandardViewType('Leads', 'inbox')).toBe(true)
  })

  it('does not offer it to lists with no conversation on them', () => {
    expect(isStandardViewType('Deals', 'inbox')).toBe(false)
    expect(isStandardViewType('Tasks', 'inbox')).toBe(false)
  })

  it('survives a route it has never heard of', () => {
    expect(standardViewTypesFor(undefined)).toEqual([
      'list',
      'kanban',
      'group_by',
    ])
  })
})
