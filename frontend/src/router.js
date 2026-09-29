import { createRouter, createWebHistory } from 'vue-router'
import { standardViewTypesFor } from '@/utils/viewTypes'
import { DASHBOARD_CAPABILITIES } from '@/utils/dashboard'
import { call } from 'frappe-ui'
import { usersStore } from '@/stores/users'
import { sessionStore } from '@/stores/session'
import { viewsStore } from '@/stores/views'
import { isMobileView } from '@/composables/breakpoints'

let personaChecked = false
export const PERSONA_DONE_KEY = 'crm_persona_captured'

async function shouldCapturePersona() {
  // Client-side flag guards against re-prompting if the server persist failed.
  if (localStorage.getItem(PERSONA_DONE_KEY)) return false
  const captured = await call('frappe.client.get_single_value', {
    doctype: 'FCRM Settings',
    field: 'persona_captured',
  })
  if (captured) return false
  // The wizard only feeds telemetry; skip it entirely if the user opted out.
  const { enabled } =
    (await call('frappe.utils.telemetry.pulse.client.boot_config')) || {}
  return !!enabled
}

const routes = [
  {
    path: '/',
    name: 'Home',
  },
  {
    path: '/notifications',
    name: 'Notifications',
    component: () => import('@/pages/MobileNotification.vue'),
  },
  {
    path: '/dashboard',
    name: 'Dashboard',
    meta: { richiede: DASHBOARD_CAPABILITIES },
    component: () => import('@/pages/Dashboard.vue'),
  },
  {
    // Where you answer people: the list, the conversation and the person, all
    // on screen at once. A place you stay, rather than a list that sends you
    // somewhere else on every click.
    path: '/conversazioni',
    name: 'Conversations',
    meta: { richiede: 'conversazioni.usa' },
    component: () => import('@/pages/Conversations.vue'),
  },
  {
    // the two addresses the Inbox has had before now
    path: '/inbox',
    name: 'Inbox',
    redirect: () => ({ name: 'Conversations' }),
  },
  {
    path: '/automations',
    name: 'Automations',
    meta: { richiede: 'automazioni.vedi' },
    component: () => import('@/pages/Automations.vue'),
  },
  {
    path: '/automations/:automationId',
    name: 'Automation',
    meta: { richiede: 'automazioni.vedi' },
    component: () => import('@/pages/AutomationEditor.vue'),
  },
  {
    path: '/dialer',
    name: 'Dialer',
    meta: { richiede: 'telefono.chiama' },
    component: () => import('@/pages/Dialer.vue'),
  },
  {
    path: '/social',
    name: 'Social Planner',
    meta: { richiede: ['social.bozze', 'social.pubblica'] },
    component: () => import('@/pages/SocialPlanner.vue'),
  },
  {
    path: '/sito',
    name: 'Website',
    component: () => import('@/pages/Website.vue'),
    meta: { richiede: 'sito.gestisci' },
  },
  {
    // the operator's console: what has been issued, and what still has a button
    // waiting to be pressed. Editing a document happens on its form.
    path: '/fatture',
    name: 'Invoices',
    component: () => import('@/pages/Invoices.vue'),
    // the centre's register: whoever sees the centre's invoices, Read only too.
    // The practitioner finds theirs on each person
    meta: { richiede: 'fatture.vedi', ambito: 'centro' },
  },
  {
    // full page, not a modal: Builder's canvas refuses to work in a small box
    path: '/sito/pagine/:name',
    name: 'WebsitePage',
    component: () => import('@/pages/WebsitePageEditor.vue'),
    meta: { richiede: 'sito.gestisci' },
  },
  {
    alias: '/leads',
    path: '/leads/view/:viewType?',
    name: 'Leads',
    meta: { richiede: 'persone.vedi' },
    component: () => import('@/pages/Leads.vue'),
  },
  {
    path: '/leads/:leadId',
    name: 'Lead',
    meta: { richiede: 'persone.vedi' },
    component: () => import(`@/pages/${handleMobileView('Lead')}.vue`),
    props: true,
  },
  {
    alias: '/deals',
    path: '/deals/view/:viewType?',
    name: 'Deals',
    meta: { richiede: 'trattative.vedi' },
    component: () => import('@/pages/Deals.vue'),
  },
  {
    path: '/deals/:dealId',
    name: 'Deal',
    meta: { richiede: 'trattative.vedi' },
    component: () => import(`@/pages/${handleMobileView('Deal')}.vue`),
    props: true,
  },
  {
    alias: '/notes',
    path: '/notes/view/:viewType?',
    name: 'Notes',
    meta: { richiede: 'note.vedi' },
    component: () => import('@/pages/Notes.vue'),
  },
  {
    alias: '/tasks',
    path: '/tasks/view/:viewType?',
    name: 'Tasks',
    meta: { richiede: 'persone.vedi' },
    component: () => import('@/pages/Tasks.vue'),
  },
  {
    alias: '/contacts',
    path: '/contacts/view/:viewType?',
    name: 'Contacts',
    meta: { richiede: 'persone.vedi' },
    component: () => import('@/pages/Contacts.vue'),
  },
  {
    path: '/contacts/:contactId',
    name: 'Contact',
    meta: { richiede: 'persone.vedi' },
    component: () => import(`@/pages/${handleMobileView('Contact')}.vue`),
    props: true,
    // an address book entry is not a person: open the lead that owns it, which
    // is where the chat, the activity and the timeline are. There is no way past
    // this any more — with one number and one email per person there is nothing
    // in here that is not on the person's own page.
    beforeEnter: async (to) => {
      const leadId = await leadOwning(to.params.contactId)
      return leadId ? { name: 'Lead', params: { leadId } } : true
    },
  },
  {
    alias: '/organizations',
    path: '/organizations/view/:viewType?',
    name: 'Organizations',
    meta: { richiede: 'persone.vedi' },
    component: () => import('@/pages/Organizations.vue'),
  },
  {
    path: '/organizations/:organizationId',
    name: 'Organization',
    meta: { richiede: 'persone.vedi' },
    component: () => import(`@/pages/${handleMobileView('Organization')}.vue`),
    props: true,
  },
  {
    alias: '/call-logs',
    path: '/call-logs/view/:viewType?',
    name: 'Call Logs',
    meta: { richiede: 'telefono.registro' },
    component: () => import('@/pages/CallLogs.vue'),
  },
  {
    path: '/calendar',
    name: 'Calendar',
    meta: { richiede: 'agenda.vedi' },
    component: () => import('@/pages/Calendar.vue'),
  },
  {
    // the desk's day: arrivals, the waiting room, what the last days left open
    path: '/oggi',
    name: 'Today',
    meta: { richiede: 'agenda.presenze' },
    component: () => import('@/pages/Today.vue'),
  },
  {
    path: '/data-import',
    name: 'DataImportList',
    meta: { richiede: 'persone.importa' },
    component: () => import('@/pages/DataImport.vue'),
  },
  {
    path: '/data-import/doctype/:doctype',
    name: 'NewDataImport',
    meta: { richiede: 'persone.importa' },
    component: () => import('@/pages/DataImport.vue'),
    props: true,
  },
  {
    path: '/data-import/:importName',
    name: 'DataImport',
    meta: { richiede: 'persone.importa' },
    component: () => import('@/pages/DataImport.vue'),
    props: true,
  },
  {
    path: '/onboarding',
    name: 'Onboarding',
    component: () => import('@/pages/PersonaForm.vue'),
  },
  {
    path: '/:invalidpath',
    name: 'Invalid Page',
    component: () => import('@/pages/InvalidPage.vue'),
  },
  {
    path: '/not-permitted',
    name: 'Not Permitted',
    component: () => import('@/pages/NotPermitted.vue'),
  },
]

async function leadOwning(contactId) {
  if (!contactId) return null
  try {
    return await call('crm.api.contact.get_owning_lead', { contact: contactId })
  } catch (error) {
    // fail open: a contact we cannot resolve still opens its own page
    return null
  }
}

const handleMobileView = (componentName) => {
  return isMobileView.value ? `Mobile${componentName}` : componentName
}

let router = createRouter({
  history: createWebHistory('/crm'),
  routes,
})

// Where to land when the default page is not one's own: the first one the level
// opens. Notifications asks for nothing, so there is always somewhere to go.
const LANDINGS = [
  'Leads',
  'Calendar',
  'Conversations',
  'Invoices',
  'Dashboard',
  'Deals',
  'Notifications',
]

// What a page asks (doc 30): a capability, or one of several; with `ambito`,
// one of them on that much of the centre.
function meets(meta, { puoUno, ambito }) {
  if (!meta?.richiede) return true
  if (meta.ambito)
    return [].concat(meta.richiede).some((c) => ambito(c) === meta.ambito)
  return puoUno(meta.richiede)
}

function allowed(name, store) {
  const route = router.getRoutes().find((r) => r.name === name)
  return meets(route?.meta, store)
}

function firstAllowed(store) {
  return LANDINGS.find((name) => allowed(name, store)) || 'Notifications'
}

router.beforeEach(async (to, from, next) => {
  router.previousRoute = from

  const { isLoggedIn, user } = sessionStore()
  const store = usersStore()
  const { users, isCrmUser, isAgency, permissions, puoUno } = store

  if (isLoggedIn && !users.fetched) {
    try {
      await users.promise
    } catch (error) {
      console.error('Error loading users', error)
    }
  }
  // the capabilities come with the page; asked for only when they did not
  if (isLoggedIn && !permissions.data) {
    try {
      await permissions.reload()
    } catch (error) {
      console.error('Error loading permissions', error)
    }
  }

  // the wizard that sets the CRM up is the agency's, or the centre's manager's
  const isAdminUser =
    isLoggedIn &&
    (isAgency() || user === 'Administrator' || puoUno('utenti.gestisci'))

  // Only admins who haven't finished may reach the wizard, even via direct URL.
  if (isLoggedIn && to.name === 'Onboarding') {
    try {
      if (!isAdminUser || !(await shouldCapturePersona())) {
        return next({ name: 'Home' })
      }
    } catch {
      return next({ name: 'Home' })
    }
  }

  if (
    isLoggedIn &&
    isCrmUser() &&
    !personaChecked &&
    to.name !== 'Onboarding' &&
    isAdminUser
  ) {
    personaChecked = true
    try {
      if (await shouldCapturePersona()) {
        return next({ name: 'Onboarding' })
      }
    } catch (error) {
      // fail open
    }
  }

  if (isLoggedIn && to.name !== 'Not Permitted' && !isCrmUser()) {
    next({ name: 'Not Permitted' })
  } else if (isLoggedIn && !meets(to.meta, store)) {
    // a page hidden from the menu does not open from its address either (doc 30)
    next({ name: 'Home' })
  } else if (to.name === 'Home' && isLoggedIn) {
    const { views, getDefaultView } = viewsStore()
    await views.promise

    let defaultView = getDefaultView()
    if (!defaultView) {
      next({ name: firstAllowed(store) })
      return
    }

    let { route_name, type, name, is_standard } = defaultView
    route_name = route_name || 'Leads'
    // a default view on a page the level does not open is not a way in
    if (!allowed(route_name, store)) {
      next({ name: firstAllowed(store) })
      return
    }

    if (name && !is_standard) {
      next({
        name: route_name,
        params: { viewType: type },
        query: { view: name },
      })
    } else {
      next({ name: route_name, params: { viewType: type } })
    }
  } else if (!isLoggedIn) {
    window.location.href = '/login?redirect-to=/crm'
  } else if (to.matched.length === 0) {
    next({ name: 'Invalid Page' })
  } else if (['Deal', 'Lead'].includes(to.name) && !to.hash) {
    let storageKey = to.name === 'Deal' ? 'lastDealTab' : 'lastLeadTab'
    const activeTab = localStorage.getItem(storageKey) || 'activity'
    const hash = '#' + activeTab
    next({ ...to, hash })
  } else if (
    [
      'Leads',
      'Deals',
      'Contacts',
      'Organizations',
      'Notes',
      'Tasks',
      'Call Logs',
    ].includes(to.name) &&
    !to.query?.view
  ) {
    const { views, standardViews, getDefaultView } = viewsStore()
    await views.promise

    const viewType = to.params?.viewType ?? ''
    const standardViewTypes = standardViewTypesFor(to.name)

    if (!viewType) {
      const doctypeMap = {
        Leads: 'CRM Lead',
        Deals: 'CRM Deal',
        Contacts: 'Contact',
        Organizations: 'CRM Organization',
        Notes: 'FCRM Note',
        Tasks: 'CRM Task',
        'Call Logs': 'CRM Call Log',
      }

      const doctype = doctypeMap[to.name]
      // deals live on a pipeline: the board is the view that shows it. Any view
      // the user marked as default (below) still wins.
      let defaultViewType = to.name === 'Deals' ? 'kanban' : 'list'

      let globalDefault = getDefaultView()
      if (globalDefault && globalDefault.route_name === to.name) {
        defaultViewType = globalDefault.type || 'list'
        if (globalDefault.name && !globalDefault.is_standard) {
          next({
            name: to.name,
            params: { viewType: defaultViewType },
            query: { ...to.query, view: globalDefault.name },
          })
          return
        }
      }

      for (const viewType of standardViewTypes) {
        const standardView = standardViews.value?.[doctype + ' ' + viewType]
        if (standardView?.is_default) {
          defaultViewType = viewType
          break
        }
      }

      next({
        name: to.name,
        params: { viewType: defaultViewType },
        query: to.query,
      })
    } else if (!standardViewTypes.includes(viewType)) {
      const viewNameOrLabel = viewType

      let view = views.data?.find(
        (v) => v.name == viewNameOrLabel || v.label === viewNameOrLabel,
      )

      if (view) {
        next({
          name: to.name,
          params: { viewType: view.type || 'list' },
          query: { ...to.query, view: view.name },
        })
      } else {
        next({
          name: to.name,
          params: { viewType: 'list' },
          query: to.query,
        })
      }
    } else {
      next()
    }
  } else {
    next()
  }
})

export default router
