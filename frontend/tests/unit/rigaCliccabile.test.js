import { describe, expect, it, vi } from 'vitest'
import { tastoDellaRiga, vRigaCliccabile } from '@/utils/rigaCliccabile'

describe('v-riga-cliccabile', () => {
  it('makes a row a button the keyboard reaches and opens', () => {
    const riga = document.createElement('div')
    const apri = vi.fn()
    riga.addEventListener('click', apri)
    vRigaCliccabile.mounted(riga)
    expect(riga.getAttribute('role')).toBe('button')
    expect(riga.getAttribute('tabindex')).toBe('0')
    riga.dispatchEvent(new KeyboardEvent('keydown', { key: 'Enter' }))
    riga.dispatchEvent(new KeyboardEvent('keydown', { key: ' ' }))
    expect(apri).toHaveBeenCalledTimes(2)
    vRigaCliccabile.unmounted(riga)
    riga.dispatchEvent(new KeyboardEvent('keydown', { key: 'Enter' }))
    expect(apri).toHaveBeenCalledTimes(2)
  })

  it('leaves a key pressed on a control inside the row to that control', () => {
    const riga = document.createElement('div')
    const cestino = document.createElement('button')
    riga.appendChild(cestino)
    const evento = new KeyboardEvent('keydown', { key: 'Enter' })
    Object.defineProperty(evento, 'target', { value: cestino })
    expect(tastoDellaRiga(evento, riga)).toBe(false)
  })

  it('keeps a role the row already has', () => {
    const riga = document.createElement('div')
    riga.setAttribute('role', 'link')
    vRigaCliccabile.mounted(riga)
    expect(riga.getAttribute('role')).toBe('link')
  })
})
