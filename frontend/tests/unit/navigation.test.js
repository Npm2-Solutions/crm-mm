import { describe, it, expect } from 'vitest'
import {
  INBOX_VIEW_TYPE,
  bottomNavTabFor,
  currentNavKey,
  isInboxRoute,
} from '@/utils/navigation'

const inbox = {
  name: 'Leads',
  params: { viewType: INBOX_VIEW_TYPE },
  query: {},
}
const people = { name: 'Leads', params: {}, query: {} }
const person = { name: 'Lead', params: { leadId: 'CRM-LEAD-1' }, query: {} }

describe('isInboxRoute', () => {
  it('recognises the People list read as an inbox', () => {
    expect(isInboxRoute(inbox)).toBe(true)
  })

  it('does not mistake the plain People list for it', () => {
    expect(isInboxRoute(people)).toBe(false)
    expect(isInboxRoute({ name: 'Leads', params: { viewType: 'list' } })).toBe(
      false,
    )
  })

  it('survives a route with nothing on it', () => {
    expect(isInboxRoute(undefined)).toBe(false)
    expect(isInboxRoute({})).toBe(false)
  })
})

describe('currentNavKey', () => {
  it('calls the inbox the Inbox, not Leads', () => {
    expect(currentNavKey(inbox)).toBe('Inbox')
  })

  it('prefers a saved view over the route it is a view of', () => {
    expect(
      currentNavKey({ name: 'Deals', params: {}, query: { view: 'v1' } }),
    ).toBe('v1')
  })

  it('falls back to the route name', () => {
    expect(currentNavKey(people)).toBe('Leads')
  })
})

describe('bottomNavTabFor', () => {
  it('lights the Inbox tab on the inbox, and not the People one', () => {
    expect(bottomNavTabFor(inbox)).toBe('Inbox')
  })

  it('lights People on the People list and on a person', () => {
    expect(bottomNavTabFor(people)).toBe('Leads')
    expect(bottomNavTabFor(person)).toBe('Leads')
  })

  it('keeps the section lit on a detail page', () => {
    expect(bottomNavTabFor({ name: 'Deal', params: { dealId: 'D-1' } })).toBe(
      'Deals',
    )
  })

  // Unlike the sidebar, a saved view must not put the tab bar out: you are
  // still in that list.
  it('keeps the section lit inside a saved view of it', () => {
    expect(
      bottomNavTabFor({ name: 'Leads', params: {}, query: { view: 'v1' } }),
    ).toBe('Leads')
  })

  it('returns nothing for a route with no tab', () => {
    expect(bottomNavTabFor({ name: 'Organizations', params: {} })).toBeNull()
    expect(bottomNavTabFor(undefined)).toBeNull()
  })
})
