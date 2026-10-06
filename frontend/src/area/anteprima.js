// Copyright (c) 2026, NPM2 Solutions Srl and contributors
// For license information, please see license.txt

// The centre's preview of a person's area (crm.area.anteprima): the staff's
// session looking at the area as the person sees it, opened from the person's
// page. Nothing is changed or sent from here: the server refuses it anyway, and
// the pages do not offer it.
import { call } from 'frappe-ui'

export const anteprima = window.AREA?.preview || null

// the person's first name, as the preview's sentences say it
export const chi = (anteprima?.lead_name || '').split(' ')[0]

export async function chiudi() {
  try {
    await call('crm.area.anteprima.stop')
  } catch {
    // it ends by itself within half an hour
  }
  window.location.href = anteprima
    ? `/crm/persone/${encodeURIComponent(anteprima.lead)}`
    : '/crm'
}
