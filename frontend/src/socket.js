// Modifications copyright (c) 2026, NPM2 Solutions Srl

import { io } from 'socket.io-client'
import { getCachedListResource, getCachedResource } from 'frappe-ui'

export function initSocket() {
  let socketio_port = window.socketio_port || 9000
  let host = window.location.hostname
  let siteName = window.site_name
  let port = window.location.port ? `:${socketio_port}` : ''
  let protocol = port ? 'http' : 'https'
  let url = `${protocol}://${host}${port}/${siteName}`

  // The app on a phone stays open for days: it keeps trying to reconnect,
  // never giving up. Five attempts, twenty seconds of a network gone or of a
  // phone asleep, left it deaf until it was opened again.
  let socket = io(url, {
    withCredentials: true,
    reconnectionDelayMax: 10000,
  })
  // back in sight, or the network back: at once, not at the next attempt
  // that a phone asleep has pushed back (`connect()` alone waits for it), nor
  // never, as after the server refused one
  const riprova = () => {
    if (!socket.connected) socket.disconnect().connect()
  }
  document.addEventListener('visibilitychange', () => {
    if (document.visibilityState === 'visible') riprova()
  })
  window.addEventListener('online', riprova)
  socket.on('refetch_resource', (data) => {
    if (data.cache_key) {
      let resource =
        getCachedResource(data.cache_key) ||
        getCachedListResource(data.cache_key)
      if (resource) {
        resource.reload()
      }
    }
  })
  return socket
}
