// Who is in and whose area they are looking at: one person at a time, chosen
// among the session's own (the server checks it on every call anyway).
import { call } from 'frappe-ui'
import { reactive } from 'vue'
import { esci } from '@/utils/esci'

const KEY = 'area:person'

export const area = reactive({
  me: null,
  person: null,
  loading: false,
  error: '',
})

export async function loadMe() {
  if (area.me || area.loading) return area.me
  area.loading = true
  try {
    area.me = await call('crm.area.api.get_me')
    let kept = null
    try {
      kept = sessionStorage.getItem(KEY)
    } catch {
      kept = null
    }
    const people = area.me.people || []
    area.person =
      people.find((p) => p.name === kept)?.name || people[0]?.name || null
  } catch (e) {
    area.error = e.messages?.[0] || e.message
  } finally {
    area.loading = false
  }
  return area.me
}

// A place another module adds (crm.area.sezioni): the clinic's documents, its
// plans. Shown when it has something for the person being looked at.
export function section(key) {
  const current = (area.me?.people || []).find((p) => p.name === area.person)
  return Boolean(current?.sections?.[key])
}

export function choose(person) {
  area.person = person
  try {
    sessionStorage.setItem(KEY, person)
  } catch {
    /* the choice lasts the page only */
  }
}

// Out of the area, through the one way out (utils/esci.js): the server ends
// the session, then what the browser kept of it goes - whose area was open, a
// form's session, a diet's shopping list ticked. Back to the door either way:
// a logout the server did not end leaves the area as it was.
export async function logout() {
  try {
    await esci(async () => {
      const risposta = await fetch('/api/method/logout', {
        method: 'POST',
        headers: { 'X-Frappe-CSRF-Token': window.csrf_token || '' },
      })
      if (!risposta.ok) throw new Error(risposta.statusText)
    })
  } catch {
    // not out: the session goes on, and nothing was taken away
  }
  window.location.href = '/area'
}

export function messageOf(error) {
  return (
    error?.messages?.[0] ||
    error?.message ||
    __('Something went wrong: try again.')
  )
}
