import { describe, expect, it } from 'vitest'
import { firstFocusable, firstTypable } from '@/utils/focus'

function form(html) {
  const root = document.createElement('div')
  root.innerHTML = html
  return root
}

describe('firstTypable', () => {
  it('passes over a picker to the first place somebody can type', () => {
    const root = form(`
      <button id="salutation">Salutation</button>
      <input id="email" type="email" />
      <input id="first" type="text" />
    `)
    expect(firstTypable(root).id).toBe('email')
  })

  it('does not stop at what cannot be typed into', () => {
    const root = form(`
      <input type="hidden" />
      <input type="checkbox" />
      <input type="radio" />
      <input type="file" />
      <input disabled />
      <input readonly />
      <textarea id="notes"></textarea>
    `)
    expect(firstTypable(root).id).toBe('notes')
  })

  it('skips what is hidden: another tab, a folded section', () => {
    const root = form(`
      <div style="display: none;"><input id="other-tab" /></div>
      <div hidden><input id="folded" /></div>
      <div inert><input id="inert" /></div>
      <input id="visible" />
    `)
    expect(firstTypable(root).id).toBe('visible')
  })

  it('starts at a required field, the one the form cannot be saved without', () => {
    const root = form(`
      <div class="field"><button>Salutation</button></div>
      <div class="field"><input id="email" /></div>
      <div class="field" data-required><input id="first-name" /></div>
    `)
    expect(firstTypable(root).id).toBe('first-name')
  })

  it('takes the first field when none is required', () => {
    const root = form(`
      <div class="field"><input id="website" /></div>
      <div class="field"><input id="phone" /></div>
    `)
    expect(firstTypable(root).id).toBe('website')
  })

  it('does not take a required field it cannot type into', () => {
    const root = form(`
      <div class="field" data-required><button>Status</button></div>
      <div class="field"><input id="notes" /></div>
    `)
    expect(firstTypable(root).id).toBe('notes')
  })

  it('takes an editor too', () => {
    const root = form(`<div id="editor" contenteditable="true"></div>`)
    expect(firstTypable(root).id).toBe('editor')
  })

  it('has nothing to say about a form with nothing to type into', () => {
    expect(firstTypable(form('<button>Only a button</button>'))).toBeNull()
    expect(firstTypable(form(''))).toBeNull()
    expect(firstTypable(null)).toBeNull()
  })
})

describe('firstFocusable', () => {
  it('is the first control of any kind, the way the dialog picks it', () => {
    const root = form(`
      <span>label</span>
      <button id="salutation">Salutation</button>
      <input id="email" />
    `)
    expect(firstFocusable(root).id).toBe('salutation')
  })

  it('skips what is disabled or hidden', () => {
    const root = form(`
      <button disabled>no</button>
      <div style="display:none"><button>hidden</button></div>
      <a id="link" href="#x">link</a>
    `)
    expect(firstFocusable(root).id).toBe('link')
  })

  it('is nothing when there is nothing', () => {
    expect(firstFocusable(form('<p>text</p>'))).toBeNull()
    expect(firstFocusable(null)).toBeNull()
  })
})
