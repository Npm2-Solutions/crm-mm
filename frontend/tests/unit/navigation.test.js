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

  it('lights the section a page lives in', () => {
    expect(currentNavKey({ name: 'Lead' })).toBe('Leads')
    expect(currentNavKey({ name: 'Organizations' })).toBe('Leads')
    expect(currentNavKey({ name: 'Notes' })).toBe('Tasks')
    expect(currentNavKey({ name: 'Waiting List' })).toBe('Calendar')
    // the reception desk is a view of the agenda, not an entry of its own
    expect(currentNavKey({ name: 'Today' })).toBe('Calendar')
    expect(currentNavKey({ name: 'Deal' })).toBe('Deals')
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
    // a person's form being filled
    expect(bottomNavTabFor({ name: 'FormFill' })).toBe('Leads')
    expect(bottomNavTabFor({ name: 'Deal' })).toBe('Deals')
  })

  it('lights the chat tab on the conversations screen', () => {
    expect(bottomNavTabFor({ name: 'Conversations' })).toBe('Conversations')
  })

  it('keeps people lit on their companies', () => {
    expect(bottomNavTabFor({ name: 'Organizations' })).toBe('Leads')
    expect(bottomNavTabFor({ name: 'Notes' })).toBe('Tasks')
  })

  it('answers nothing for the places with no tab', () => {
    expect(bottomNavTabFor({ name: 'Invoices' })).toBeNull()
    expect(bottomNavTabFor(undefined)).toBeNull()
  })
})

describe('bottomNavTabFor, with the bar the menu gives', () => {
  const tabs = ['Calendar', 'Leads', 'Conversations', 'Invoices']

  it('lights the agenda on its reception desk and people inside a person', () => {
    expect(bottomNavTabFor({ name: 'Today' }, tabs)).toBe('Calendar')
    expect(bottomNavTabFor({ name: 'Calendar' }, tabs)).toBe('Calendar')
    expect(bottomNavTabFor({ name: 'Waiting List' }, tabs)).toBe('Calendar')
    expect(bottomNavTabFor({ name: 'Lead' }, tabs)).toBe('Leads')
    expect(bottomNavTabFor({ name: 'Contact' }, tabs)).toBe('Leads')
  })

  it('answers nothing for a page that has no tab in this bar', () => {
    expect(bottomNavTabFor({ name: 'Deal' }, tabs)).toBeNull()
    expect(bottomNavTabFor({ name: 'Tasks' }, tabs)).toBeNull()
  })
})
