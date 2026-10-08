// Copyright (c) 2026, NPM2 Solutions Srl and contributors
// For license information, please see license.txt

// A campaign: an automation started by hand, sent from the People list to a view
// or to the rows chosen (crm/automation/campagne.py). What the dialog and the
// automation's Enrolments say of it, in words: the reasons a person is left out
// (in the server's order), the ways it writes by, the list it went to.

/** The reasons, in the order the server looks at them (`campagne_regole.MOTIVI`). */
export const MOTIVI = ['already', 'consent', 'conditions', 'stop', 'no_contact']

const VIA_DEL_PASSO = {
  send_email: 'email',
  send_sms: 'sms',
  send_whatsapp_template: 'whatsapp',
}

/** The ways an automation writes by, through its branches and paths, as the
 * server reads them (`campagne_regole.canali`): a form goes the way its step says. */
export function canali(passi) {
  const trovati = new Set()
  for (const passo of passi || []) {
    if (!passo || typeof passo !== 'object') continue
    if (VIA_DEL_PASSO[passo.type]) trovati.add(VIA_DEL_PASSO[passo.type])
    else if (passo.type === 'send_form')
      trovati.add(
        ['email', 'sms', 'whatsapp'].includes(passo.via) ? passo.via : 'email',
      )
    const dentro = [
      ...(passo.branches || []).map((ramo) => ramo.steps),
      passo.else_steps,
      ...(passo.paths || []).map((percorso) => percorso.steps),
    ]
    for (const blocco of dentro)
      for (const via of canali(blocco)) trovati.add(via)
  }
  return [...trovati].sort()
}

/** What a person left out for want of an address lacks, by the ways it writes. */
export function senzaRecapito(canali, t = (s) => s) {
  const vie = new Set(canali || [])
  const email = vie.has('email')
  const cellulare = vie.has('sms') || vie.has('whatsapp')
  if (email && cellulare) return t('No email nor mobile number')
  if (email) return t('No email address')
  return t('No mobile number')
}

/** The reasons that happened, each with its words and how many: `{chiave, testo, quanti}`. */
export function righeDeiSalti(saltati, canali, t = (s) => s) {
  const parole = {
    already: t('Already in this campaign'),
    consent: t('No marketing consent'),
    conditions: t("Do not meet the campaign's conditions"),
    stop: t("Wrote STOP to the centre's SMS"),
    no_contact: senzaRecapito(canali, t),
  }
  const righe = MOTIVI.filter((chiave) => saltati?.[chiave] > 0)
  // a reason this version does not know still counts, under its own key
  for (const chiave of Object.keys(saltati || {})) {
    if (!MOTIVI.includes(chiave) && saltati[chiave] > 0) righe.push(chiave)
  }
  return righe.map((chiave) => ({
    chiave,
    testo: parole[chiave] || chiave,
    quanti: saltati[chiave],
  }))
}

/** How many were left out in all. */
export function quantiSaltati(saltati) {
  return Object.values(saltati || {}).reduce((a, b) => a + (Number(b) || 0), 0)
}

/** The ways a campaign writes by, in one line («By email and SMS»), or ''. */
export function vieDellaCampagna(canali, t = (s) => s) {
  const nomi = { email: t('email'), sms: t('SMS'), whatsapp: t('WhatsApp') }
  const vie = ['email', 'sms', 'whatsapp'].filter((via) =>
    (canali || []).includes(via),
  )
  if (!vie.length) return t('It writes to nobody: tasks, tags, notes')
  const elenco = vie.map((via) => nomi[via])
  const ultima = elenco.pop()
  const parole = elenco.length
    ? t('{0} and {1}').replace('{0}', elenco.join(', ')).replace('{1}', ultima)
    : ultima
  return t('By {0}').replace('{0}', parole)
}

/** The list a campaign goes to, as the report keeps it: the rows chosen or the view. */
export function fonteDellaLista({ scelti = 0, vista = '' } = {}, t = (s) => s) {
  if (scelti === 1) return t('1 person chosen')
  if (scelti > 1) return t('{0} people chosen').replace('{0}', scelti)
  return vista
    ? t('The view «{0}»').replace('{0}', vista)
    : t('The list on screen')
}
