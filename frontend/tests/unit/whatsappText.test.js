import { describe, it, expect } from 'vitest'
import { whatsAppBlocks } from '@/utils/whatsappText'

describe('a list in a WhatsApp message', () => {
  it('is a list, not loose items', () => {
    // a bare <li> is what put the bullets outside the bubble: with no list
    // around it the browser draws the marker in whatever lies to the left
    const html = whatsAppBlocks('* uno\n* due')
    expect(html).toBe('<ul class="wa-list"><li>uno</li><li>due</li></ul>')
  })

  it('reads a dash the same way, because WhatsApp does', () => {
    expect(whatsAppBlocks('- uno\n- due')).toBe(
      '<ul class="wa-list"><li>uno</li><li>due</li></ul>',
    )
  })

  it('numbers a numbered list', () => {
    expect(whatsAppBlocks('1. uno\n2) due')).toBe(
      '<ol class="wa-list"><li>uno</li><li>due</li></ol>',
    )
  })

  it('keeps a bulleted run and a numbered run apart', () => {
    const html = whatsAppBlocks('* uno\n1. primo')
    expect(html).toBe(
      '<ul class="wa-list"><li>uno</li></ul>' +
        '<ol class="wa-list"><li>primo</li></ol>',
    )
  })

  it('closes the list when the text goes on', () => {
    expect(whatsAppBlocks('cose:\n* uno\nfine')).toBe(
      'cose:<ul class="wa-list"><li>uno</li></ul>fine',
    )
  })

  it('reads the marks inside an item', () => {
    expect(whatsAppBlocks('* *molto* importante')).toBe(
      '<ul class="wa-list"><li><b>molto</b> importante</li></ul>',
    )
  })
})

describe('the rest of a WhatsApp message', () => {
  it('separates the lines of one run with a single break', () => {
    expect(whatsAppBlocks('una\ndue')).toBe('una<br>due')
  })

  it('reads the five inline marks', () => {
    expect(whatsAppBlocks('_a_ *b* ~c~ `d`')).toBe(
      '<i>a</i> <b>b</b> <s>c</s> <code>d</code>',
    )
  })

  it('reads a fence as one block of code, not three backticks', () => {
    expect(whatsAppBlocks('```codice```')).toBe('<code>codice</code>')
  })

  it('quotes a quoted line', () => {
    expect(whatsAppBlocks('> detto\nrisposta')).toBe(
      '<blockquote>detto</blockquote>risposta',
    )
  })

  it('leaves bold alone when it starts a line', () => {
    // `*testo*` is an emphasis, `* testo` is a bullet: the space is the whole
    // difference, and reading it wrong turns every bold opening into a list
    expect(whatsAppBlocks('*importante*')).toBe('<b>importante</b>')
  })

  it('survives nothing at all', () => {
    expect(whatsAppBlocks('')).toBe('')
    expect(whatsAppBlocks(null)).toBe('')
    expect(whatsAppBlocks(undefined)).toBe('')
  })
})
