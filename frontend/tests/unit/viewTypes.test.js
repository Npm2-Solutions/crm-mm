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

  it('does not claim one nobody has', () => {
    // left out of this list, a view type reads as the name of a saved view: the
    // router finds none and sends you back to the list, which looks like the
    // click doing nothing at all. That is how the Inbox was broken.
    expect(isStandardViewType('Leads', 'inbox')).toBe(false)
    expect(isStandardViewType('Leads', 'whatever')).toBe(false)
  })

  it('survives a route it has never heard of', () => {
    expect(standardViewTypesFor(undefined)).toEqual([
      'list',
      'kanban',
      'group_by',
    ])
  })
})
