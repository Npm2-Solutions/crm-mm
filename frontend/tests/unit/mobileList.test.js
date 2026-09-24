import { describe, it, expect } from 'vitest'
import { splitColumnsForCard } from '@/utils/mobileList'

// The shape the server sends for the default People list.
const leadColumns = [
  { label: 'Name', key: 'lead_name', width: '12rem' },
  { label: 'Organization', key: 'organization', width: '10rem' },
  { label: 'Status', key: 'status', width: '8rem' },
  { label: 'Email', key: 'email', width: '12rem' },
  { label: 'Mobile No', key: 'mobile_no', width: '11rem' },
  { label: 'Assigned To', key: '_assign', width: '10rem' },
  { label: 'Last Modified', key: 'modified', width: '8rem' },
]

describe('splitColumnsForCard', () => {
  it('makes the first column the card title', () => {
    const { title } = splitColumnsForCard(leadColumns)
    expect(title.key).toBe('lead_name')
  })

  it('pulls `modified` out as the trailing timestamp', () => {
    const { trailing, details } = splitColumnsForCard(leadColumns)
    expect(trailing.key).toBe('modified')
    expect(details.map((c) => c.key)).not.toContain('modified')
  })

  it('leaves every other column as a labelled detail, in order', () => {
    const { details } = splitColumnsForCard(leadColumns)
    expect(details.map((c) => c.key)).toEqual([
      'organization',
      'status',
      'email',
      'mobile_no',
      '_assign',
    ])
  })

  // `idx` is handed back to the *ListView cell renderers, which pass it up in
  // `applyFilter` — so it has to be the column's position in the original list,
  // not its position in the card.
  it('tags each column with its index in the original list', () => {
    const { title, trailing, details } = splitColumnsForCard(leadColumns)
    expect(title._idx).toBe(0)
    expect(trailing._idx).toBe(6)
    expect(details.map((c) => c._idx)).toEqual([1, 2, 3, 4, 5])
  })

  it('copes with a list that has no `modified` column', () => {
    const { title, trailing, details } = splitColumnsForCard([
      { label: 'Subject', key: 'subject' },
      { label: 'Priority', key: 'priority' },
    ])
    expect(title.key).toBe('subject')
    expect(trailing).toBeNull()
    expect(details.map((c) => c.key)).toEqual(['priority'])
  })

  it('copes with no columns at all', () => {
    expect(splitColumnsForCard()).toEqual({
      title: null,
      trailing: null,
      details: [],
    })
  })

  it('does not mutate the columns it is given', () => {
    const columns = [{ label: 'Name', key: 'name' }]
    splitColumnsForCard(columns)
    expect(columns[0]).toEqual({ label: 'Name', key: 'name' })
  })

  // A single-column list is all title and nothing else.
  it('leaves no details when the only column is the title', () => {
    const { title, details } = splitColumnsForCard([
      { label: 'Name', key: 'name' },
    ])
    expect(title.key).toBe('name')
    expect(details).toEqual([])
  })
})
