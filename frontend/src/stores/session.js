// Modifications copyright (c) 2026, NPM2 Solutions Srl

import { defineStore } from 'pinia'
import { call, createResource, toast } from 'frappe-ui'
import router from '@/router'
import { usersStore } from '@/stores/users'
import { esci } from '@/utils/esci'
import { ref, computed, reactive } from 'vue'

export const sessionStore = defineStore('crm-session', () => {
  function sessionUser() {
    let cookies = new URLSearchParams(document.cookie.split('; ').join('&'))
    let _sessionUser = cookies.get('user_id')
    if (_sessionUser === 'Guest') {
      _sessionUser = null
    }
    return _sessionUser
  }

  let user = ref(sessionUser())
  const isLoggedIn = computed(() => !!user.value)

  const login = createResource({
    url: 'login',
    onError() {
      throw new Error(__('Invalid Email or Password'))
    },
    onSuccess() {
      user.value = sessionUser()
      login.reset()
      router.replace({ path: '/' })
    },
  })

  // this device's notifications let go (composables/spinta.js), where it could
  // have them at all: imported then, as main.js does, never in the first
  // download. What it answers, the browser's part, waits for the logout
  function lasciaIlDispositivo() {
    if (window.Notification?.permission !== 'granted') return
    return import('@/composables/spinta').then((spinta) => spinta.lascia())
  }

  // a logout refused: the device is the session's again, at once
  function tieniIlDispositivo() {
    if (window.Notification?.permission !== 'granted') return
    import('@/composables/spinta')
      .then((spinta) => spinta.resta())
      .catch(() => {})
  }

  /**
   * Out of the desk, through the one way out (utils/esci.js): this device's
   * notifications let go while the session is there, the server ends it, then
   * what the browser kept of it goes; the page goes `verso`, the sign-in
   * unless said (the tablet handed to a person: their forms). Rejects, having
   * cleared nothing and kept the device, when the server did not end the
   * session.
   */
  async function esciVerso(verso = '/login?redirect-to=/crm') {
    // whose drafts go, read while the session is there: the user, and the
    // email the composer keeps them under (composables/drafts.js), as the
    // users' list has it - asked of nobody
    const { allUsers } = usersStore()
    const utenti = [
      user.value,
      (allUsers || []).find((utente) => utente.name === user.value)?.email,
    ]
    try {
      await esci(() => call('logout'), { utenti, prima: lasciaIlDispositivo })
    } catch (errore) {
      tieniIlDispositivo()
      throw errore
    }
    user.value = null
    window.location.href = verso
  }

  // the account menu's way out, and «Access denied»'s: a logout the server did
  // not end is said, and the session goes on as it was
  const logout = reactive({
    loading: false,
    async submit() {
      if (logout.loading) return
      logout.loading = true
      try {
        await esciVerso()
      } catch {
        logout.loading = false
        toast.error(__('Could not log out: try again.'))
      }
    },
  })

  return {
    user,
    isLoggedIn,
    login,
    logout,
    esciVerso,
  }
})
