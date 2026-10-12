// Copyright (c) 2026, NPM2 Solutions Srl and contributors
// What a logout takes away from the browser's storage and what it leaves: every
// key the app writes, decided.
import fs from 'node:fs'
import path from 'node:path'
import {
  DELLA_SESSIONE,
  DELLA_SESSIONE_PER_INIZIO,
  PREFERENZE,
  PREFERENZE_PER_INIZIO,
  bozzaDi,
  daTogliere,
} from '@/utils/dopoLUscita'

const SRC = path.resolve(import.meta.dirname, '../../src')
const ANNA = 'anna@centro.it'
const BRUNO = 'bruno@centro.it'

// Every file of the app that writes localStorage or sessionStorage, how many
// times at most, and a key of each as it writes it, with what a logout does
// with it. A file that starts writing, or writes once more, fails below: its
// key is decided in utils/dopoLUscita.js, and listed here.
const SCRITTORI = {
  'pages/Calendar.vue': {
    volte: 2,
    chiavi: { crmAgenda: 'resta', crmCalendarNewKind: 'resta' },
  },
  'components/Layouts/AppSidebar.vue': {
    volte: 1,
    chiavi: { menuPiegato: 'resta' },
  },
  'components/Resizer.vue': { volte: 1, chiavi: { sidebarWidth: 'resta' } },
  'components/Activities/Activities.vue': {
    volte: 1,
    chiavi: { crmActivityChannel: 'resta' },
  },
  'composables/useActiveTabManager.js': {
    volte: 1,
    chiavi: { lastLeadTab: 'resta', lastDealTab: 'resta' },
  },
  'pages/Dashboard.vue': { volte: 1, chiavi: { crm_dashboard_last: 'resta' } },
  'components/Telephony/TwilioCallUI.vue': {
    volte: 1,
    chiavi: { 'dottorcloud:numero-da-mostrare': 'resta' },
  },
  'components/Telephony/TelnyxCallUI.vue': {
    volte: 1,
    chiavi: { 'dottorcloud:numero-da-mostrare': 'resta' },
  },
  'components/Mobile/InstallaApp.vue': {
    volte: 1,
    chiavi: { 'dc-installa-non-ora': 'resta' },
  },
  'components/Mobile/NotificheSulTelefono.vue': {
    volte: 1,
    chiavi: { 'dc-notifiche-non-ora': 'resta' },
  },
  'area/components/InstallCard.vue': {
    volte: 1,
    chiavi: { 'area:installa:not-now': 'resta' },
  },
  'area/components/PasskeyCard.vue': {
    volte: 1,
    chiavi: { 'area:passkey:not-now': 'resta' },
  },
  'composables/primiPassi.js': {
    volte: 1,
    chiavi: { [`primiPassiNascosti:${ANNA}`]: 'resta' },
  },
  'composables/drafts.js': {
    volte: 1,
    chiavi: {
      [`emailBoxContent-${ANNA}-CRM Lead-CRM-LEAD-2026-00397`]: 'va',
      [`commentBoxContent-${ANNA}-CRM Deal-CRM-DEAL-2026-00012`]: 'va',
      [`attachments-${ANNA}-CRM Lead-CRM-LEAD-2026-00397`]: 'va',
      [`commentAttachments-${ANNA}-CRM Lead-CRM-LEAD-2026-00397`]: 'va',
      [`whatsappDraft-${ANNA}-CRM Lead-CRM-LEAD-2026-00397`]: 'va',
      [`smsDraft-${ANNA}-CRM Lead-CRM-LEAD-2026-00397`]: 'va',
      // a colleague's, kept for when they come back
      [`smsDraft-${BRUNO}-CRM Lead-CRM-LEAD-2026-00397`]: 'resta',
    },
  },
  'data/notifications.js': {
    volte: 1,
    chiavi: { eventNotificationAlerts: 'va' },
  },
  'composables/useBroadcast.js': { volte: 2, chiavi: { app_broadcasts: 'va' } },
  'composables/spinta.js': { volte: 1, chiavi: { 'crm-spinta': 'va' } },
  'pages/Benvenuto.vue': { volte: 1, chiavi: { 'dc-benvenuto-dopo': 'va' } },
  'utils/ricarica.js': { volte: 1, chiavi: { 'dc-ricaricata': 'va' } },
  'area/store.js': { volte: 1, chiavi: { 'area:person': 'va' } },
  'components/ListViews/ListRows.vue': {
    volte: 1,
    chiavi: { 'scrollPositionCRM Lead': 'va' },
  },
  'components/ListViews/MobileListRows.vue': {
    volte: 1,
    chiavi: { 'scrollPositionCRM Lead': 'va' },
  },
  'components/Activities/DataFields.vue': {
    volte: 1,
    chiavi: { 'fieldLayoutTab:CRM Lead:CRM-LEAD-2026-00397': 'va' },
  },
  'area/pages/PlanShopping.vue': {
    volte: 1,
    chiavi: { 'crm-area-spesa:PLAN-0001:2026-10-12': 'va' },
  },
  'area/components/PrepareVisit.vue': {
    volte: 1,
    chiavi: { 'modulo:4f2a9c': 'va' },
  },
}

const SCRIVE = /\b(?:localStorage|sessionStorage)\.setItem\(|\buseStorage\(/g

// the app's files that write the browser's storage, and how many times
function scrittori(cartella = SRC, trovati = {}) {
  for (const voce of fs.readdirSync(cartella, { withFileTypes: true })) {
    const percorso = path.join(cartella, voce.name)
    if (voce.isDirectory()) scrittori(percorso, trovati)
    else if (/\.(js|jsx|ts|vue)$/.test(voce.name)) {
      const volte = (fs.readFileSync(percorso, 'utf8').match(SCRIVE) || [])
        .length
      if (volte) trovati[path.relative(SRC, percorso)] = volte
    }
  }
  return trovati
}

describe('every key the app writes is decided', () => {
  it('knows every file that writes the browser’s storage', () => {
    const trovati = scrittori()
    const nuovi = Object.keys(trovati).filter((file) => !SCRITTORI[file])
    expect(nuovi, 'decide their keys in utils/dopoLUscita.js').toEqual([])
    for (const [file, volte] of Object.entries(trovati))
      expect(volte, file).toBeLessThanOrEqual(SCRITTORI[file].volte)
  })

  it('keeps how the device is set, takes away the rest', () => {
    for (const [file, { chiavi }] of Object.entries(SCRITTORI))
      for (const [chiave, esito] of Object.entries(chiavi))
        expect(daTogliere([chiave], [ANNA]), `${file}: ${chiave}`).toEqual(
          esito === 'va' ? [chiave] : [],
        )
  })

  it('keeps the theme frappe-ui writes, and the sidebar as older versions kept it', () => {
    expect(daTogliere(['theme', 'isSidebarCollapsed'], [ANNA])).toEqual([])
  })

  it('takes away the memos of notifications older versions kept per person', () => {
    expect(daTogliere([`crm-spinta:${BRUNO}`], [ANNA])).toEqual([
      `crm-spinta:${BRUNO}`,
    ])
  })

  it('decides each key once', () => {
    const tenute = [...PREFERENZE, ...PREFERENZE_PER_INIZIO]
    const tolte = [...DELLA_SESSIONE, ...DELLA_SESSIONE_PER_INIZIO]
    expect(tenute.filter((chiave) => tolte.includes(chiave))).toEqual([])
    expect(new Set(tenute).size).toBe(tenute.length)
    expect(new Set(tolte).size).toBe(tolte.length)
  })
})

describe('daTogliere', () => {
  it('takes away the drafts of whoever signs out, under their user or their email', () => {
    const chiavi = [
      `emailBoxContent-${ANNA}-CRM Lead-CRM-LEAD-0001`,
      'emailBoxContent-Administrator-CRM Lead-CRM-LEAD-0001',
      'smsDraft-admin@example.com-CRM Deal-CRM-DEAL-0001',
      `smsDraft-${BRUNO}-CRM Lead-CRM-LEAD-0001`,
    ]
    expect(daTogliere(chiavi, [ANNA])).toEqual([chiavi[0]])
    expect(daTogliere(chiavi, ['Administrator', 'admin@example.com'])).toEqual([
      chiavi[1],
      chiavi[2],
    ])
    // nobody signing out: nobody's drafts
    expect(daTogliere(chiavi, [])).toEqual([])
    expect(daTogliere(chiavi, [null, ''])).toEqual([])
  })

  it('leaves alone what the app does not write', () => {
    // the framework's desk, another app of the site
    expect(
      daTogliere(
        ['_page:Form/CRM Lead', 'last_visited', 'preferred_breadcrumbs:x'],
        [ANNA],
      ),
    ).toEqual([])
  })

  it('takes nothing for a storage that gave nothing', () => {
    expect(daTogliere(null, [ANNA])).toEqual([])
    expect(daTogliere([null, undefined, 3], [ANNA])).toEqual([])
  })
})

describe('bozzaDi', () => {
  it('is a draft of theirs: a kind, their user, then the record', () => {
    expect(bozzaDi(`smsDraft-${ANNA}-CRM Lead-CRM-LEAD-0001`, [ANNA])).toBe(
      true,
    )
    // somebody whose address begins with theirs is somebody else
    expect(bozzaDi('smsDraft-anna@centro.it.vecchio-CRM Lead-X', [ANNA])).toBe(
      false,
    )
    expect(bozzaDi(`-${ANNA}-CRM Lead-X`, [ANNA])).toBe(false)
    expect(bozzaDi(`sms Draft-${ANNA}-CRM Lead-X`, [ANNA])).toBe(false)
  })

  it('never takes a preference for a draft, whatever its shape', () => {
    expect(bozzaDi('dc-installa-non-ora', ['installa'])).toBe(true)
    expect(daTogliere(['dc-installa-non-ora'], ['installa'])).toEqual([])
  })
})
