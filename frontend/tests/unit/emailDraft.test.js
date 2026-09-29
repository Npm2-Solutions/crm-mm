import { describe, expect, it } from 'vitest'
import {
  quotes,
  replyAddresses,
  replyDraft,
  replySubject,
  signatureHTML,
  signaturePreview,
  signed,
  written,
} from '@/utils/emailDraft'

const REPLY =
  '<p>Grazie, confermo.</p><p class="reply-to-content"></p><blockquote><p>Mi confermate giovedì?</p></blockquote>'

describe('signed', () => {
  it('puts the signature under what was written', () => {
    expect(signed('<p>Ciao</p>', '<p>Mario Rossi</p>')).toBe(
      '<p>Ciao</p><p><br></p><div class="signature"><p>Mario Rossi</p></div>',
    )
  })

  it('puts it above the email being answered, not under it', () => {
    const out = signed(REPLY, '<p>Mario Rossi</p>')
    const signature = out.indexOf('Mario Rossi')
    expect(signature).toBeGreaterThan(out.indexOf('Grazie, confermo.'))
    expect(signature).toBeLessThan(out.indexOf('reply-to-content'))
    expect(out).toContain(
      '<blockquote><p>Mi confermate giovedì?</p></blockquote>',
    )
  })

  it('does not sign twice: an old draft, a template, already carry it', () => {
    const draft = '<p>Ciao</p><p>Mario   Rossi</p>'
    expect(signed(draft, '<p>Mario Rossi</p>')).toBe(draft)
  })

  it('adds nothing when there is no signature', () => {
    expect(signed('<p>Ciao</p>', null)).toBe('<p>Ciao</p>')
    expect(signed('<p>Ciao</p>', '   ')).toBe('<p>Ciao</p>')
    expect(signed('<p>Ciao</p>', '<p> </p>')).toBe('<p>Ciao</p>')
  })

  it('keeps the lines of a signature written as plain text', () => {
    expect(signed('<p>Ciao</p>', 'Mario Rossi\nMM Web Agency')).toContain(
      'Mario Rossi<br>MM Web Agency',
    )
  })
})

describe('written', () => {
  it('is what was written above the quote', () => {
    expect(written(REPLY)).toBe('<p>Grazie, confermo.</p>')
  })

  it('is empty for a reply nobody has written yet', () => {
    expect(
      written(
        '<p></p><p class="reply-to-content"></p><blockquote>x</blockquote>',
      ),
    ).toBe('<p></p>')
  })

  it('is the whole draft when it answers nothing', () => {
    expect(written('<p>Ciao</p>')).toBe('<p>Ciao</p>')
    expect(written('')).toBe('')
    expect(written(null)).toBe('')
  })
})

describe('quotes', () => {
  it('knows a reply from a new email', () => {
    expect(quotes(REPLY)).toBe(true)
    expect(quotes('<p>Ciao</p>')).toBe(false)
    expect(quotes('')).toBe(false)
  })
})

describe('signatureHTML', () => {
  it('leaves HTML alone and breaks text into its lines', () => {
    expect(signatureHTML('<p>a</p>\n<p>b</p>')).toBe('<p>a</p>\n<p>b</p>')
    expect(signatureHTML('a\nb')).toBe('a<br>b')
    expect(signatureHTML('')).toBe('')
    expect(signatureHTML(null)).toBe('')
  })
})

describe('signaturePreview', () => {
  it('says the signature in one line', () => {
    expect(
      signaturePreview(
        '<p>Mario Rossi</p><p>MM Web Agency<br>+39 333 123 4567</p>',
      ),
    ).toBe('Mario Rossi · MM Web Agency · +39 333 123 4567')
    expect(signaturePreview('Mario Rossi\n\nMM Web Agency')).toBe(
      'Mario Rossi · MM Web Agency',
    )
  })

  it('is empty without a signature', () => {
    expect(signaturePreview(null)).toBe('')
    expect(signaturePreview('<p></p>')).toBe('')
  })
})

describe('replyDraft', () => {
  it('quotes the email being answered under an empty line to write on', () => {
    expect(replyDraft('', '<p>Mi confermate?</p>')).toBe(
      '<p></p><p class="reply-to-content"></p><blockquote><p>Mi confermate?</p></blockquote>',
    )
  })

  it('keeps what was already written', () => {
    expect(replyDraft('<p>Buongiorno,</p>', '<p>x</p>')).toBe(
      '<p>Buongiorno,</p><p class="reply-to-content"></p><blockquote><p>x</p></blockquote>',
    )
  })

  it('answers the new email, not the one answered before', () => {
    const second = replyDraft(REPLY, '<p>Nuova domanda</p>')
    expect(second).toContain('Grazie, confermo.')
    expect(second).toContain('Nuova domanda')
    expect(second).not.toContain('Mi confermate giovedì?')
  })
})

describe('replyAddresses', () => {
  const ours = ['info@studio.it', 'mm@studio.it']

  it('answers a customer from the mailbox they wrote to', () => {
    expect(
      replyAddresses(
        {
          sender: 'Mario Rossi <mario@cliente.it>',
          recipients: 'info@studio.it',
        },
        ours,
      ),
    ).toEqual({
      from: 'info@studio.it',
      to: ['mario@cliente.it'],
      cc: [],
      bcc: [],
    })
  })

  it('never writes as the customer', () => {
    const { from } = replyAddresses(
      { sender: 'mario@cliente.it', recipients: 'altro@esterno.it' },
      ours,
    )
    expect(from).toBe('')
  })

  it('answers our own email to the people it went to, not to ourselves', () => {
    expect(
      replyAddresses(
        { sender: 'mm@studio.it', recipients: 'mario@cliente.it' },
        ours,
      ),
    ).toEqual({
      from: 'mm@studio.it',
      to: ['mario@cliente.it'],
      cc: [],
      bcc: [],
    })
  })

  it('copies everybody else on reply-all, never us', () => {
    expect(
      replyAddresses(
        {
          sender: 'mario@cliente.it',
          recipients: 'INFO@studio.it, socio@cliente.it',
          cc: 'Anna <anna@cliente.it>, mm@studio.it',
        },
        ours,
        true,
      ),
    ).toEqual({
      from: 'info@studio.it',
      to: ['mario@cliente.it'],
      cc: ['socio@cliente.it', 'anna@cliente.it'],
      bcc: [],
    })
  })

  it('keeps the blind copies of our own email on reply-all only', () => {
    const email = {
      sender: 'mm@studio.it',
      recipients: 'mario@cliente.it',
      bcc: 'commercialista@studio2.it',
    }
    expect(replyAddresses(email, ours, true).bcc).toEqual([
      'commercialista@studio2.it',
    ])
    expect(replyAddresses(email, ours, false).bcc).toEqual([])
  })

  it('gives our address as the account spells it', () => {
    expect(
      replyAddresses(
        { sender: 'mario@cliente.it', recipients: 'info@studio.it' },
        ['Info@Studio.it'],
      ).from,
    ).toBe('Info@Studio.it')
  })
})

describe('replySubject', () => {
  it('says Re: once', () => {
    expect(replySubject('Preventivo')).toBe('Re: Preventivo')
    expect(replySubject('Re: Preventivo')).toBe('Re: Preventivo')
    expect(replySubject('RE: Preventivo')).toBe('RE: Preventivo')
    expect(replySubject(null)).toBe('Re: ')
  })
})
