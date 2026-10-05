// Modifications copyright (c) 2026, NPM2 Solutions Srl

import { defineStore } from 'pinia'
import { createResource } from 'frappe-ui'
import { sessionStore } from './session'
import { computed, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { nomeDiUnUtente } from '@/utils/marchio'

export const usersStore = defineStore('crm-users', () => {
  const session = sessionStore()

  let usersByName = reactive({})
  const router = useRouter()

  // A user asked for before the first list arrives (the page no longer waits for
  // it) gets a stand-in, and is asked of the server only if the list does not
  // bring them: one call, not one for every name on the page.
  const abbozzi = new Set()
  const chiestiPrima = new Set()

  // Fast initial fetch — returns only the ~few CRM users so the UI is
  // interactive immediately. Non-CRM user profile data is filled in
  // afterwards by the background `usersFull` fetch (and by `get_user_info`
  // for the race window before that lands).
  const users = createResource({
    url: 'crm.api.session.get_users',
    cache: 'crm-users',
    initialData: [],
    auto: true,
    transform([allUsers, crmUsers]) {
      allUsers = normalizeUsers(allUsers)
      crmUsers = normalizeUsers(crmUsers)
      for (let user of allUsers) {
        usersByName[user.name] = user
        abbozzi.delete(user.name)
        if (user.name === 'Administrator') {
          usersByName[user.email] = user
        }
      }
      return { allUsers, crmUsers }
    },
    onError(error) {
      if (error && error.exc_type === 'AuthenticationError') {
        router.push('/login')
      }
    },
    onSuccess() {
      // the names asked for while the list was on its way, that it did not bring
      for (const email of chiestiPrima)
        if (abbozzi.has(email)) queueResolve(email)
      chiestiPrima.clear()
      scheduleBackgroundFetch()
    },
  })

  // Background full-list fetch fired on browser idle. Only System Manager
  // sessions receive a larger payload here; for others the server returns
  // the same crm-users-only list. Populates usersByName so existing
  // getUser(email) call sites keep working for non-CRM emails (comment
  // authors, doc owners, email recipient typeahead, etc.).
  const usersFull = createResource({
    url: 'crm.api.session.get_users',
    params: { include_all: 1 },
    cache: 'crm-users-full',
    auto: false,
    transform([allUsers]) {
      allUsers = normalizeUsers(allUsers)
      for (let user of allUsers) {
        // upgrade partial get_user_info so always full record is used
        const existing = usersByName[user.name]
        if (existing) {
          Object.assign(existing, user)
        } else {
          usersByName[user.name] = user
        }
      }
      return { allUsers }
    },
  })

  let backgroundFetchScheduled = false
  function scheduleBackgroundFetch() {
    if (backgroundFetchScheduled) return
    // only the agency (System Manager) gets more than the first list: for anybody
    // else the server sent the same users again, a second call at every opening
    if (!isAgency()) return
    backgroundFetchScheduled = true
    const fire = () => usersFull.fetch()
    if (typeof requestIdleCallback === 'function') {
      requestIdleCallback(fire, { timeout: 5000 })
    } else {
      setTimeout(fire, 2000)
    }
  }

  // Coalesced on-demand resolver. Used when getUser(email) is called for
  // an email that the fast fetch did not cover and the background full
  // fetch has not yet landed.
  const pendingResolves = new Set()
  let flushScheduled = false

  function queueResolve(email) {
    pendingResolves.add(email)
    if (flushScheduled) return
    flushScheduled = true
    queueMicrotask(flush)
  }

  async function flush() {
    flushScheduled = false
    if (!pendingResolves.size) return
    const batch = [...pendingResolves]
    pendingResolves.clear()
    try {
      const r = createResource({
        url: 'crm.api.session.get_user_info',
        params: { users: batch },
        auto: false,
      })
      const records = await r.fetch()
      for (const u of normalizeUsers(records || [])) {
        usersByName[u.name] = { ...usersByName[u.name], ...u }
      }
    } catch (e) {
      // best-effort — the synthesized stub remains on failure
    }
  }

  function getUser(email) {
    if (!email || email === 'sessionUser') {
      email = session.user
    }
    if (!usersByName[email]) {
      usersByName[email] = {
        name: email,
        email: email,
        full_name: nomeDiUnUtente({
          name: email,
          full_name: email.split('@')[0],
        }),
        first_name: email.split('@')[0],
        last_name: '',
        user_image: null,
        role: null,
      }
      abbozzi.add(email)
      // Try to upgrade the stub via a batched fetch unless the full list
      // has already arrived - or the first list is still on its way, and may
      // bring them (onSuccess above).
      if (!usersFull.data) {
        if (users.fetched) queueResolve(email)
        else chiestiPrima.add(email)
      }
    }
    return usersByName[email]
  }

  function isWebsiteUser(email) {
    return getUser(email).user_type === 'Website User'
  }

  function isTelephonyAgent(email) {
    return getUser(email).is_telephony_agent
  }

  function getUserRole(email) {
    const user = getUser(email)
    if (user && user.role) {
      return user.role
    }
    return null
  }

  const isCrmUser = (user) => {
    user = user || session.user
    // the session's own answer comes with the page, which opens only to whoever
    // may use DottorCloud (crm.www.crm, `crm_user`): nothing waits for the list
    if (user === session.user && !users.fetched && window.crm_user != null)
      return Boolean(window.crm_user)
    return users.data.crmUsers?.find((u) => u.name === user)
  }

  // What the session may do, as the server decides it (doc 30): its levels,
  // every capability with its scope, and the plan's modules. It comes with the
  // page, so nothing appears late; it is asked again when levels change.
  const permissions = createResource({
    url: 'crm.api.session.get_permissions',
    cache: 'crm-permissions',
    initialData: window.crm_permissions || null,
    auto: !window.crm_permissions,
  })

  /**
   * Whether the session may do `capability` (`'fatture.emetti'`). Screens ask
   * this, never for a role name: the level decides, and the plan (doc 30).
   */
  function puo(capability) {
    return Boolean(permissions.data?.capabilities?.[capability])
  }

  /** On which records: 'centro', 'team', 'suoi'… or null when it may not. */
  function ambito(capability) {
    return permissions.data?.capabilities?.[capability] || null
  }

  /** Whether the session may do at least one of `capabilities`. */
  function puoUno(capabilities) {
    return [].concat(capabilities || []).some(puo)
  }

  /** Whether the session manages the site rather than works in the centre. */
  function isAgency() {
    return Boolean(permissions.data?.agency)
  }

  /**
   * Whether Read only takes every write away from the session: for what no
   * capability covers, like tasks. Everything else asks `puo()`.
   */
  function solaLettura() {
    return (
      !isAgency() && (permissions.data?.levels || []).includes('sola_lettura')
    )
  }

  return {
    users,
    usersFull,
    allUsers: computed(() => usersFull.data?.allUsers || users.data?.allUsers),
    crmUsers: computed(() => users.data?.crmUsers),
    getUser,
    isTelephonyAgent,
    getUserRole,
    isWebsiteUser,
    isCrmUser,
    permissions,
    puo,
    puoUno,
    ambito,
    isAgency,
    solaLettura,
  }
})

function normalizeUsers(users) {
  return (users || []).filter(Boolean).map((user) => normalizeUser(user))
}

function normalizeUser(user) {
  const name = user.name || user.email || ''
  const email = user.email || name
  const fallbackName = name || email

  return {
    ...user,
    name,
    email,
    full_name: nomeDiUnUtente({ ...user, name }) || fallbackName,
  }
}
