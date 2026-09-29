import { describe, expect, it } from 'vitest'
import {
  NAMED_HEX,
  appointmentCalendarColor,
  calendarColorName,
  registerCalendarColors,
} from '@/utils/calendarColors'

describe('calendarColorName', () => {
  it('keeps a name the calendar knows', () => {
    expect(calendarColorName('violet')).toBe('violet')
    expect(calendarColorName('Blue')).toBe('blue')
  })

  it('reads the old hex values as their names', () => {
    for (const [name, hex] of Object.entries(NAMED_HEX)) {
      expect(calendarColorName(hex)).toBe(name)
      expect(calendarColorName(hex.toUpperCase())).toBe(name)
    }
  })

  it('reads what the event panel saved: the variable behind the colour', () => {
    expect(calendarColorName('var(--ink-amber-7)')).toBe('amber')
    expect(calendarColorName('var(--ink-violet-7)')).toBe('violet')
    expect(calendarColorName('var(--surface-teal-2)')).toBe('cyan')
  })

  it('takes any service colour to the nearest one — not green', () => {
    expect(calendarColorName('#3b82f6')).toBe('blue')
    expect(calendarColorName('#8b5cf6')).toBe('violet')
    expect(calendarColorName('#ec4899')).toBe('pink')
    expect(calendarColorName('#f59e0b')).toBe('amber')
    expect(calendarColorName('#10b981')).toBe('green')
    expect(calendarColorName('#ef4444')).toBe('red')
    expect(calendarColorName('#06b6d4')).toBe('cyan')
    expect(calendarColorName('#f97316')).toBe('orange')
  })

  it('makes a colour with hardly any colour grey', () => {
    expect(calendarColorName('#64748b')).toBe('gray')
    expect(calendarColorName('#777')).toBe('gray')
  })

  it('falls back for nothing, or nonsense', () => {
    expect(calendarColorName('')).toBe('green')
    expect(calendarColorName(null, 'blue')).toBe('blue')
    expect(calendarColorName('not a colour', 'blue')).toBe('blue')
  })
})

describe('appointmentCalendarColor', () => {
  const services = { Massage: '#8b5cf6' }

  it('wears its service colour', () => {
    expect(
      appointmentCalendarColor(
        { service: 'Massage', status: 'Scheduled' },
        services,
      ),
    ).toBe('violet')
  })

  it('prefers a colour of its own', () => {
    expect(
      appointmentCalendarColor(
        { service: 'Massage', color: '#f97316', status: 'Confirmed' },
        services,
      ),
    ).toBe('orange')
  })

  it('goes grey once cancelled: the time is free again', () => {
    expect(
      appointmentCalendarColor(
        { service: 'Massage', status: 'Cancelled' },
        services,
      ),
    ).toBe('gray')
  })

  it('takes its status colour when nothing else has one', () => {
    expect(appointmentCalendarColor({ status: 'Scheduled' })).toBe('blue')
  })
})

describe('registerCalendarColors', () => {
  it('adds grey and red, and keeps what is there', () => {
    const map = { green: { color: 'mine' } }
    registerCalendarColors(map)
    expect(map.green).toEqual({ color: 'mine' })
    expect(map.gray.bg).toBe('var(--surface-gray-1)')
    expect(map.red.text).toBe('var(--ink-red-7)')
    // what the calendar matches an unknown hex against
    expect(map.red.color).toBe(NAMED_HEX.red)
    const again = map.gray
    registerCalendarColors(map)
    expect(map.gray).toBe(again)
  })
})
