// Copyright (c) 2026, NPM2 Solutions Srl and contributors
// For license information, please see license.txt

// The account's menu as data (Settings > The centre > General > Menu): the
// applications, the settings, the information, the centre's own links, the way
// out. The sidebar's dropdown draws it as a menu, the phone's "More" page as
// rows (pages/Altro.vue): the same entries in the same order, a separator a new
// group. Home Actions are edited by Sales Managers and opened by everyone: an
// icon is only ever a Feather name and a route a path or an http(s) link
// (utils/dropdownItems.js).
import LucideLayoutGrid from '~icons/lucide/layout-grid'
import { showAboutModal } from '@/composables/modals'
import { showSettings } from '@/composables/settings'
import { sessionStore } from '@/stores/session'
import { getSettings } from '@/stores/settings'
import { safeDropdownIcon, safeDropdownRoute } from '@/utils/dropdownItems'
import { createResource } from 'frappe-ui'
import { computed, markRaw } from 'vue'

export function useVociAccount() {
  const { settings } = getSettings()
  const { logout } = sessionStore()

  const apps = createResource({
    url: 'frappe.apps.get_apps',
    cache: 'apps',
    auto: true,
    transform: (data) => [appDelDesk(), ...appSorelle(data)],
  })

  /** The groups of entries: `{ tipo, etichetta, icona, azione }`. */
  const gruppi = computed(() => {
    const voci = settings.value?.dropdown_items || []
    const gruppi = [[]]
    for (const voce of voci) {
      if (voce.hidden) continue
      if (voce.type === 'Separator') {
        gruppi.push([])
        continue
      }
      const riga = voceDi(voce)
      if (riga) gruppi[gruppi.length - 1].push(riga)
    }
    return gruppi.filter((gruppo) => gruppo.length)
  })

  function voceDi(voce) {
    const icona = safeDropdownIcon(voce.icon)
    if (voce.is_standard) {
      switch (voce.name1) {
        case 'app_selector':
          return { tipo: 'app', etichetta: __(voce.label), icona }
        case 'settings':
          return {
            tipo: 'impostazioni',
            etichetta: __(voce.label),
            icona,
            azione: () => (showSettings.value = true),
          }
        case 'about':
          return {
            tipo: 'informazioni',
            etichetta: __(voce.label),
            icona,
            azione: () => (showAboutModal.value = true),
          }
        case 'logout':
          return {
            tipo: 'esci',
            etichetta: __(voce.label),
            icona,
            azione: () => logout.submit(),
          }
      }
      return null
    }
    // a route that would run script rather than navigate stays out of the menu
    const route = safeDropdownRoute(voce.route)
    if (!route) return null
    return {
      tipo: 'collegamento',
      etichetta: __(voce.label),
      icona,
      azione: () =>
        window.open(route, voce.open_in_new_window ? '_blank' : '', 'noopener'),
    }
  }

  return { gruppi, apps }
}

// the back office: an icon of its own, not the framework's logo
function appDelDesk() {
  return {
    name: 'desk',
    icon: markRaw(LucideLayoutGrid),
    title: __('Desk'),
    route: '/desk',
  }
}

function appSorelle(data) {
  return (data || [])
    .filter((app) => app.name !== 'crm')
    .map((app) => ({
      name: app.name,
      logo: app.logo,
      title: __(app.title),
      route: app.route,
    }))
}
