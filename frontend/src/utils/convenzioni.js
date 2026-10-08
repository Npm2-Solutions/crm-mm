// Copyright (c) 2026, NPM2 Solutions Srl and contributors
// For license information, please see license.txt

/**
 * Conventions, health funds and insurances (crm/convenzioni, doc 61): their
 * words, the shares while a convention is edited, a pratica's state, a cover's
 * line. The same rules as crm/convenzioni/regole.py; `t` is the translator
 * (`__`).
 */

export const FONDO = 'Health fund'
export const ASSICURAZIONE = 'Insurance'
export const AZIENDA = 'Company'
export const TIPI = [FONDO, ASSICURAZIONE, AZIENDA]

export const DIRETTA = 'Direct'
export const INDIRETTA = 'Indirect'

export const LISTINO = 'Price list'
export const SCONTO = 'Discount'
export const PREZZI_DEL_CENTRO = 'Centre prices'

export const NIENTE = 'None'
export const FISSA = 'Fixed'
export const PERCENTUALE = 'Percentage'

/** A kind of convention in words. */
export function nomeDelTipo(tipo, t) {
  return (
    {
      [FONDO]: t('Health fund'),
      [ASSICURAZIONE]: t('Insurance'),
      [AZIENDA]: t('Company convention'),
    }[tipo] ||
    tipo ||
    ''
  )
}

/** A form in words: «Forma diretta», «Forma indiretta». */
export function nomeDellaForma(forma, t) {
  if (forma === DIRETTA) return t('Direct form')
  if (forma === INDIRETTA) return t('Indirect form')
  return ''
}

/** A pratica's state in words, and its badge's theme. */
export function statoInParole(stato, t) {
  return (
    {
      'To authorise': { label: t('To authorise'), theme: 'orange' },
      Authorised: { label: t('Authorised'), theme: 'blue' },
      Done: { label: t('Done, to bill'), theme: 'green' },
      Drafted: { label: t('In a draft to the fund'), theme: 'gray' },
      Billed: { label: t('Billed to the fund'), theme: 'gray' },
      Paid: { label: t('Paid by the fund'), theme: 'green' },
      Cancelled: { label: t('Cancelled'), theme: 'gray' },
      Missed: { label: t('Did not come', null, 'Pratica'), theme: 'red' },
    }[stato] || { label: stato || '', theme: 'gray' }
  )
}

/** An amount to the cent, half up, as a number of cents. */
function centesimi(valore) {
  const numero = Number(valore)
  if (!Number.isFinite(numero)) return 0
  // 1.005 is 1.00499999… in binary: the half is decided on the decimal text
  return Math.round(Number((numero * 100).toFixed(6)))
}

function percentuale(valore) {
  return Math.min(Math.max(Number(valore) || 0, 0), 100)
}

/** What a service costs under the convention, as `regole.prezzo`. */
export function prezzo(convenzione, prezzoDelCentro, prezzoDelListino = null) {
  const modo = convenzione?.price_mode || PREZZI_DEL_CENTRO
  if (modo === LISTINO && prezzoDelListino !== null)
    return centesimi(prezzoDelListino) / 100
  if (modo === SCONTO) {
    const sconto = percentuale(convenzione.discount_percent)
    return (
      Math.round(
        Number(
          ((centesimi(prezzoDelCentro) * (100 - sconto)) / 100).toFixed(6),
        ),
      ) / 100
    )
  }
  return centesimi(prezzoDelCentro) / 100
}

/**
 * `[the person's share, the fund's]` of a total, as `regole.quote`: indirect
 * form, all the person's; direct, a service's own share before the
 * convention's, never more than the total, the fund the rest.
 */
export function quote(convenzione, forma, totale, servizio = null) {
  const tutto = centesimi(totale)
  if (forma !== DIRETTA) return [tutto / 100, 0]
  const propria = (convenzione?.shares || []).find(
    (riga) => riga.service && riga.service === servizio,
  )
  let persona = 0
  if (propria) persona = centesimi(propria.patient_share)
  else if (convenzione?.share_mode === FISSA)
    persona = centesimi(convenzione.share_amount)
  else if (convenzione?.share_mode === PERCENTUALE)
    persona = Math.round(
      Number(
        ((tutto * percentuale(convenzione.share_percent)) / 100).toFixed(6),
      ),
    )
  persona = Math.min(Math.max(persona, 0), tutto)
  return [persona / 100, (tutto - persona) / 100]
}

/** What stops a convention from being saved, as `regole.problemi`: the first. */
export function problemaDellaConvenzione(c, t) {
  if (!(c.convention_name || '').trim()) return t("Write the convention's name")
  if (!TIPI.includes(c.kind)) return t('Choose what kind of convention it is')
  if (!c.direct && !c.indirect)
    return t('Choose the direct form, the indirect form or both')
  if (c.direct && !c.organization)
    return t('In direct form the fund is billed: choose the company that pays')
  const modo = c.price_mode || PREZZI_DEL_CENTRO
  if (modo === LISTINO && !c.price_list)
    return t('Choose the price list of the convention')
  const sconto = Number(c.discount_percent)
  if (modo === SCONTO && !(sconto > 0 && sconto <= 100))
    return t('The discount is a percentage between 0 and 100')
  if (c.direct && c.share_mode === PERCENTUALE) {
    const quota = Number(c.share_percent)
    if (!(quota >= 0 && quota <= 100))
      return t("The person's share is a percentage between 0 and 100")
  }
  if (
    (c.direct && c.share_mode === FISSA && Number(c.share_amount) < 0) ||
    (c.shares || []).some((riga) => Number(riga.patient_share) < 0)
  )
    return t("The person's share cannot be below zero")
  if (c.valid_from && c.valid_upto && c.valid_from > c.valid_upto)
    return t('It ends before it starts')
  return ''
}

/**
 * A convention in one line for the settings' list: its kind, its forms, its
 * prices, the person's share. `soldi(n)` writes an amount.
 */
export function rigaDellaConvenzione(c, t, soldi) {
  const parti = [nomeDelTipo(c.kind, t)]
  if (c.direct && c.indirect) parti.push(t('Direct and indirect form'))
  else if (c.direct || c.indirect)
    parti.push(nomeDellaForma(c.direct ? DIRETTA : INDIRETTA, t))
  if (c.price_mode === LISTINO && c.price_list_name)
    parti.push(t('prices of {0}', [c.price_list_name]))
  else if (c.price_mode === SCONTO)
    parti.push(t('{0}% off', [Number(c.discount_percent) || 0]))
  if (c.direct) {
    if (c.share_mode === PERCENTUALE)
      parti.push(t('the person pays {0}%', [Number(c.share_percent) || 0]))
    else if (c.share_mode === FISSA)
      parti.push(t('the person pays {0}', [soldi(c.share_amount)]))
    else parti.push(t('the fund pays it all'))
  }
  return parti.join(' · ')
}

/** A cover in one line: the card, whose it is, until when. */
export function rigaDellaCopertura(c, t, giorno) {
  const parti = []
  if (c.card_number) parti.push(t('Card {0}', [c.card_number]))
  if (c.holder_name) parti.push(t('holder {0}', [c.holder_name]))
  if (c.valid_upto) parti.push(t('until {0}', [giorno(c.valid_upto)]))
  return parti.join(' · ')
}

/** The month before and after a "YYYY-MM", for the statement's arrows. */
export function meseAccanto(mese, passi) {
  const [anno, numero] = String(mese).split('-').map(Number)
  const totale = anno * 12 + (numero - 1) + passi
  return `${Math.floor(totale / 12)}-${String((totale % 12) + 1).padStart(2, '0')}`
}

/** The pratiche the fund may be billed for now: done, something to bill. */
export function daFatturare(pratiche = []) {
  return pratiche.filter((p) => p.state === 'Done' && Number(p.fund_share) > 0)
}
