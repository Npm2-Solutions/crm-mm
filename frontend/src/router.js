// Modifications copyright (c) 2026, NPM2 Solutions Srl

import { createRouter, createWebHistory } from 'vue-router'
import { standardViewTypesFor } from '@/utils/viewTypes'
import { DASHBOARD_CAPABILITIES } from '@/utils/dashboard'
import { call } from 'frappe-ui'
import { usersStore } from '@/stores/users'
import { sessionStore } from '@/stores/session'
import { viewsStore } from '@/stores/views'
import { isMobileView } from '@/composables/breakpoints'
import { nomeDellaPagina } from '@/utils/menu'
import { segnaIRitorni } from '@/utils/ritorno'

// The centre's first opening (crm/benvenuto.py): whoever sets it up chooses its
// language and writes its name before anything else, as the page's boot says.
// «Later» leaves it for this tab (`sessionStorage`), and it comes back with the
// next one
export const BENVENUTO_DOPO = 'dc-benvenuto-dopo'
function daAccogliere() {
  if (!window.benvenuto) return false
  try {
    return window.sessionStorage.getItem(BENVENUTO_DOPO) !== '1'
  } catch {
    return true
  }
}

// Every scope of people's records but the masked one: who reads names, emails
// and phones (the address book)
const RECAPITI = ['centro', 'team', 'suoi']

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
    // "More" on a phone: what the bar at the bottom has no room for
    // (pages/Altro.vue). The desk has all of it in its sidebar.
    path: '/altro',
    name: 'More',
    beforeEnter: () => (isMobileView.value ? true : { name: 'Home' }),
    component: () => import('@/pages/Altro.vue'),
  },
  {
    path: '/dashboard',
    name: 'Dashboard',
    // it follows `?d=` itself (App.vue keys the page on its path)
    meta: { richiede: DASHBOARD_CAPABILITIES, segueLaQuery: true },
    component: () => import('@/pages/Dashboard.vue'),
  },
  {
    // Where you answer people: the list, the conversation and the person, all
    // on screen at once. A place you stay, rather than a list that sends you
    // somewhere else on every click.
    path: '/conversazioni',
    name: 'Conversations',
    // it follows `?person=` itself (App.vue keys the page on its path)
    meta: { richiede: 'conversazioni.usa', segueLaQuery: true },
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
    // everybody the centre has heard from, in one list: a lead is a step of
    // theirs, not another list (docs/progetto-ghl/54)
    alias: '/persone',
    path: '/persone/view/:viewType?',
    name: 'Leads',
    meta: { richiede: 'persone.vedi' },
    component: () => import('@/pages/Leads.vue'),
  },
  {
    path: '/persone/:leadId',
    name: 'Lead',
    meta: { richiede: 'persone.vedi' },
    component: () => import(`@/pages/${handleMobileView('Lead')}.vue`),
    props: true,
  },
  // the addresses the people had before: a link in an email sent last month,
  // a bookmark, still opens its person
  {
    path: '/leads/view/:viewType?',
    redirect: (to) => ({ name: 'Leads', params: to.params, query: to.query }),
  },
  { path: '/leads', redirect: (to) => ({ name: 'Leads', query: to.query }) },
  {
    path: '/leads/:leadId',
    redirect: (to) => ({
      name: 'Lead',
      params: to.params,
      query: to.query,
      hash: to.hash,
    }),
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
    // the address book is names, emails and phones: whoever sees people with
    // them masked (Marketing) does not read it (crm/permissions/seguono.py)
    meta: { richiede: 'persone.vedi', ambito: RECAPITI },
    component: () => import('@/pages/Contacts.vue'),
  },
  {
    path: '/contacts/:contactId',
    name: 'Contact',
    // not the address book's scope: an entry opens its person, whom Marketing
    // reads masked (a deal's contact arrow leads there)
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
    // who waits for a place, and the places offered to them
    path: '/waiting-list',
    name: 'Waiting List',
    meta: { richiede: 'agenda.attese' },
    component: () => import('@/pages/WaitingList.vue'),
  },
  {
    // the desk's day: arrivals, the waiting room, what the last days left
    // open - a view of the agenda (utils/menu.js, SORELLE); its first address
    // still opens it
    path: '/accoglienza',
    alias: '/oggi',
    name: 'Today',
    meta: { richiede: 'agenda.presenze' },
    component: () => import('@/pages/Today.vue'),
  },
  {
    // a form filled with a person and signed on the screen; signed, it is read
    path: '/moduli/:formId',
    name: 'FormFill',
    props: true,
    meta: { richiede: 'moduli.vedi' },
    component: () => import('@/pages/FormFill.vue'),
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
    path: '/benvenuto',
    alias: '/onboarding',
    name: 'Onboarding',
    component: () => import('@/pages/Benvenuto.vue'),
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

// a back to a list finds it as it was left (utils/ritorno.js): noted first,
// before any guard sends the navigation elsewhere
segnaIRitorni(router)

// Where to land when the default page is not one's own: the first one the level
// opens. The desk's day for who has it (the front desk, the practitioners, the
// manager), the numbers for who looks at the centre from above (accounting,
// marketing, the medical director). Notifications asks for nothing, so there is
// always somewhere to go.
const LANDINGS = [
  'Today',
  'Dashboard',
  'Calendar',
  'Leads',
  'Conversations',
  'Invoices',
  'Deals',
  'Notifications',
]

// What a page asks (doc 30): a capability, or one of several; with `ambito`,
// one of them on that much of the centre (or on one of a list of scopes).
function meets(meta, { puoUno, ambito }) {
  if (!meta?.richiede) return true
  if (meta.ambito) {
    const ambiti = [].concat(meta.ambito)
    return [].concat(meta.richiede).some((c) => ambiti.includes(ambito(c)))
  }
  return puoUno(meta.richiede)
}

function allowed(name, store) {
  const route = router.getRoutes().find((r) => r.name === name)
  return meets(route?.meta, store)
}

function firstAllowed(store) {
  return LANDINGS.find((name) => allowed(name, store)) || 'Notifications'
}

// every tab says which page it is; a page that names itself (a person, a view)
// does it after this. Moving within a page leaves the page's own name alone.
router.afterEach((to, from) => {
  if (to.name === from.name) return
  const nome = nomeDellaPagina(to.name)
  if (nome) document.title = __(nome)
})

router.beforeEach(async (to, from, next) => {
  router.previousRoute = from

  // a notification touched on the phone opens its page with `?notifica=`: it is
  // read, and the address goes on without it (crm/notifiche/spinta.py)
  if (to.query.notifica) {
    const { notifica, ...resto } = to.query
    call('crm.notifiche.api.mark_as_read', { names: [notifica] }).catch(
      () => {},
    )
    return next({ path: to.path, query: resto, hash: to.hash, replace: true })
  }

  const { isLoggedIn } = sessionStore()
  const store = usersStore()
  const { users, isCrmUser, permissions } = store

  // whether the session opens DottorCloud comes with the page (`crm_user`): the
  // list of users arrives meanwhile, the first page does not wait for it
  if (isLoggedIn && !users.fetched && window.crm_user == null) {
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

  // the welcome is only while the centre is still to be welcomed, and before
  // anything else for whoever sets it up (the boot's `benvenuto` says both)
  if (isLoggedIn && to.name === 'Onboarding' && !window.benvenuto) {
    return next({ name: 'Home' })
  }
  if (
    isLoggedIn &&
    to.name !== 'Onboarding' &&
    to.name !== 'Not Permitted' &&
    daAccogliere()
  ) {
    return next({ name: 'Onboarding' })
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
  } else if (to.name === 'Lead' && !to.hash) {
    // one person, two doors (docs/progetto-ghl/54): a person opens on their
    // summary from wherever one comes without saying otherwise - the People
    // list, the agenda, a search -, and the conversations and a message's
    // notification name the chat. Not the tab left last time: the person a
    // colleague sends is read from the top
    next({ ...to, hash: '#summary' })
  } else if (to.name === 'Deal' && !to.hash) {
    const activeTab = localStorage.getItem('lastDealTab') || 'activity'
    next({ ...to, hash: '#' + activeTab })
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
