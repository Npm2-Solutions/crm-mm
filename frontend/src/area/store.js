// Who is in and whose area they are looking at: one person at a time, chosen
// among the session's own (the server checks it on every call anyway).
import { call } from 'frappe-ui'
import { reactive } from 'vue'

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
    area.me = await call('crm.clinica.area.api.get_me')
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

export function choose(person) {
  area.person = person
  try {
    sessionStorage.setItem(KEY, person)
  } catch {
    /* the choice lasts the page only */
  }
}

export async function logout() {
  await fetch('/api/method/logout', {
    method: 'POST',
    headers: { 'X-Frappe-CSRF-Token': window.csrf_token || '' },
  }).catch(() => {})
  window.location.href = '/area'
}

export function messageOf(error) {
  return (
    error?.messages?.[0] ||
    error?.message ||
    __('Something went wrong: try again.')
  )
}
