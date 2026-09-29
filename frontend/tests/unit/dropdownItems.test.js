import { describe, it, expect } from 'vitest'
import feather from 'feather-icons'
import FEATHER_ICONS from '../../../crm/fcrm/doctype/crm_dropdown_item/feather_icons.json'
import {
  DEFAULT_DROPDOWN_ICON,
  isAllowedDropdownIcon,
  safeDropdownIcon,
  safeDropdownRoute,
} from '@/utils/dropdownItems'

const MARKUP_ICON = '<svg><image href=x onerror=alert(document.cookie)>'

describe('isAllowedDropdownIcon', () => {
  it('takes the Feather names the standard items use', () => {
    for (const icon of ['settings', 'info', 'log-out', 'external-link']) {
      expect(isAllowedDropdownIcon(icon)).toBe(true)
    }
  })

  it('never takes markup, however harmless it looks', () => {
    expect(isAllowedDropdownIcon(MARKUP_ICON)).toBe(false)
    expect(isAllowedDropdownIcon('<svg onload=alert(1)></svg>')).toBe(false)
    expect(
      isAllowedDropdownIcon(
        '<svg viewBox="0 0 24 24"><path d="M0 0h24v24H0z"/></svg>',
      ),
    ).toBe(false)
  })

  it('refuses class names, which the menu would paste into class=""', () => {
    expect(isAllowedDropdownIcon('lucide-settings')).toBe(false)
    expect(isAllowedDropdownIcon('settings fixed inset-0 z-50')).toBe(false)
  })

  it('survives being handed something that is not a string', () => {
    for (const icon of [undefined, null, 42, {}, ['settings']]) {
      expect(isAllowedDropdownIcon(icon)).toBe(false)
    }
  })
})

describe('safeDropdownIcon', () => {
  it('keeps a Feather name, trimmed', () => {
    expect(safeDropdownIcon('book-open')).toBe('book-open')
    expect(safeDropdownIcon('  info ')).toBe('info')
  })

  it('draws the default icon for anything else', () => {
    expect(safeDropdownIcon(MARKUP_ICON)).toBe(DEFAULT_DROPDOWN_ICON)
    expect(safeDropdownIcon('')).toBe(DEFAULT_DROPDOWN_ICON)
    expect(safeDropdownIcon(undefined)).toBe(DEFAULT_DROPDOWN_ICON)
    expect(DEFAULT_DROPDOWN_ICON).toBe('external-link')
  })
})

describe('the icon list', () => {
  it('is exactly what FeatherIcon can draw', () => {
    // a name missing from feather would render as a circle; one missing from
    // the list would be refused although an admin may already use it
    expect([...FEATHER_ICONS].sort()).toEqual(Object.keys(feather.icons).sort())
  })
})

describe('safeDropdownRoute', () => {
  it.each([
    '/crm/leads',
    '/app/todo?status=Open#top',
    '#',
    '?tab=1',
    'crm/leads',
    'https://docs.frappe.io/crm',
    'http://example.com',
    'HTTPS://EXAMPLE.COM/A',
    // scheme-relative: the page's own http(s), so just another link
    '//cdn.example.com/page',
  ])('opens %j', (route) => {
    expect(safeDropdownRoute(route)).toBe(route)
  })

  it('opens the trimmed route', () => {
    expect(safeDropdownRoute('  /crm/leads  ')).toBe('/crm/leads')
  })

  it.each([
    'javascript:alert(document.cookie)',
    'JavaScript:alert(1)',
    '  javascript:alert(1)',
    '\njavascript:alert(1)',
    ' javascript:alert(1)',
    // browsers drop tabs and newlines anywhere, so these still read javascript:
    'java\tscript:alert(1)',
    'java\nscript:alert(1)',
    'java\rscript:alert(1)',
    '\u0000javascript:alert(1)',
    '\u0001javascript:alert(1)',
    'data:text/html,<script>alert(1)</script>',
    'data:image/svg+xml;base64,PHN2ZyBvbmxvYWQ9YWxlcnQoMSk+',
    'vbscript:msgbox(1)',
    'file:///etc/passwd',
    'mailto:someone@example.com',
    'blob:https://example.com/0f0e',
    'about:blank',
    'https://[::1',
  ])('refuses %j', (route) => {
    expect(safeDropdownRoute(route)).toBeNull()
  })

  it('has nothing to open for an empty or missing route', () => {
    for (const route of ['', '   ', undefined, null, 7]) {
      expect(safeDropdownRoute(route)).toBeNull()
    }
  })
})
