import { describe, expect, it } from 'vitest'
import {
  formatEuro,
  invoiceLabel,
  invoiceStatusTheme,
  isCreditNote,
  isRealStatus,
  worstStatus,
} from '@/utils/invoicing'

describe('invoiceStatusTheme', () => {
  it('settles green', () => {
    expect(invoiceStatusTheme('consegnata')).toBe('green')
    expect(invoiceStatusTheme('accolto')).toBe('green')
  })

  it('turns red on a refusal, whichever channel refused', () => {
    expect(invoiceStatusTheme('scartata')).toBe('red')
    expect(invoiceStatusTheme('scartato')).toBe('red')
    expect(invoiceStatusTheme('mancata_consegna')).toBe('red')
    expect(invoiceStatusTheme('errore')).toBe('red')
  })

  it('is blue on the way and orange while it is still ours', () => {
    expect(invoiceStatusTheme('inviato')).toBe('blue')
    expect(invoiceStatusTheme('da_inviare')).toBe('orange')
  })
})

describe('isRealStatus', () => {
  it('hides the states that mean «this does not apply»', () => {
    expect(isRealStatus('non_applicabile')).toBe(false)
    expect(isRealStatus('')).toBe(false)
    expect(isRealStatus(undefined)).toBe(false)
    expect(isRealStatus('inviato')).toBe(true)
  })
})

describe('worstStatus', () => {
  it('says nothing when neither channel applies', () => {
    expect(
      worstStatus({
        sdi_status: 'non_applicabile',
        ts_status: 'non_applicabile',
      }),
    ).toBe('')
  })

  it('a refusal outranks a success on the other channel', () => {
    expect(
      worstStatus({ sdi_status: 'consegnata', ts_status: 'scartato' }),
    ).toBe('scartato')
    expect(worstStatus({ sdi_status: 'scartata', ts_status: 'accolto' })).toBe(
      'scartata',
    )
  })

  it('otherwise the SdI state is the one shown', () => {
    expect(
      worstStatus({ sdi_status: 'inviato', ts_status: 'da_inviare' }),
    ).toBe('inviato')
  })

  it('falls back to whichever channel is in play', () => {
    expect(
      worstStatus({ sdi_status: 'non_applicabile', ts_status: 'accolto' }),
    ).toBe('accolto')
  })
})

describe('isCreditNote', () => {
  it('knows the two types that give money back', () => {
    expect(isCreditNote('TD04')).toBe(true)
    expect(isCreditNote('TD08')).toBe(true)
    expect(isCreditNote('TD01')).toBe(false)
    expect(isCreditNote(undefined)).toBe(false)
  })
})

describe('formatEuro', () => {
  // The grouping separator depends on the ICU data the runtime was built with,
  // so what is asserted is what the format has to get right everywhere: two
  // decimals after a comma, and the currency named.
  it('writes euros the Italian way', () => {
    expect(formatEuro(1234.5)).toContain(',50')
    expect(formatEuro(1234.5)).toContain('€')
  })

  it('an empty amount is zero, not NaN', () => {
    expect(formatEuro(undefined)).toContain('0,00')
    expect(formatEuro(null)).toContain('0,00')
  })
})

describe('invoiceLabel', () => {
  it('a draft says so instead of showing a number it has not been given', () => {
    expect(invoiceLabel({ docstatus: 0, name: 'new-crm-invoice-1' })).toBe(
      'Draft',
    )
  })

  it('otherwise it is the number on the document', () => {
    expect(
      invoiceLabel({ docstatus: 1, document_number: '12', name: 'INV-1' }),
    ).toBe('12')
  })

  it('falls back to the record name when there is no number yet', () => {
    expect(invoiceLabel({ docstatus: 1, name: 'INV-2026-00012' })).toBe(
      'INV-2026-00012',
    )
  })
})
