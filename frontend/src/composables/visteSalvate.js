// Copyright (c) 2026, NPM2 Solutions Srl and contributors
// For license information, please see license.txt

// The views saved for everyone and the pinned ones, after the menu: the sidebar
// draws them in groups that fold, the phone's "More" page as rows. Each view
// opens its list with itself chosen.
import LeadsIcon from '@/components/Icons/LeadsIcon.vue'
import DealsIcon from '@/components/Icons/DealsIcon.vue'
import ContactsIcon from '@/components/Icons/ContactsIcon.vue'
import OrganizationsIcon from '@/components/Icons/OrganizationsIcon.vue'
import NoteIcon from '@/components/Icons/NoteIcon.vue'
import PhoneIcon from '@/components/Icons/PhoneIcon.vue'
import PinIcon from '@/components/Icons/PinIcon.vue'
import { viewsStore } from '@/stores/views'
import { computed, markRaw } from 'vue'

const ICONE = Object.fromEntries(
  Object.entries({
    Leads: LeadsIcon,
    Deals: DealsIcon,
    Contacts: ContactsIcon,
    Organizations: OrganizationsIcon,
    Notes: NoteIcon,
    'Call Logs': PhoneIcon,
  }).map(([pagina, icona]) => [pagina, markRaw(icona)]),
)

/** `[{ name, opened, views: [{ label, icon, key, to }] }]`, the empty ones left out. */
export function useVisteSalvate() {
  const { getPinnedViews, getPublicViews } = viewsStore()

  return computed(() => {
    const gruppi = []
    if (getPublicViews().length)
      gruppi.push({
        name: 'Public Views',
        opened: true,
        views: righe(getPublicViews()),
      })
    if (getPinnedViews().length)
      gruppi.push({
        name: 'Pinned Views',
        opened: true,
        views: righe(getPinnedViews()),
      })
    return gruppi
  })
}

function righe(viste) {
  return viste.map((vista) => ({
    label: vista.label,
    icon: vista.icon || ICONE[vista.route_name] || markRaw(PinIcon),
    key: vista.name,
    to: {
      name: vista.route_name,
      params: { viewType: vista.type || 'list' },
      query: { view: vista.name },
    },
  }))
}
