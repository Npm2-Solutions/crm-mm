// Modifications copyright (c) 2026, NPM2 Solutions Srl

import './index.css'

import { createApp } from 'vue'
import { createPinia } from 'pinia'
import { createDialog } from './utils/dialogs'
import { initSocket } from './socket'
import router from './router'
import translationPlugin from './translation'
import { indossa } from './utils/marchio'
import { ascoltaLInstallazione } from './utils/installa'
import { ricaricaSeManca } from './utils/ricarica'
import { percorsoDellApp } from './utils/spinta'
import App from './App.vue'

import {
  FrappeUI,
  Button,
  Input,
  TextInput,
  FormControl,
  ErrorMessage,
  Dialog,
  Alert,
  Badge,
  setConfig,
  frappeRequest,
  FeatherIcon,
} from 'frappe-ui'

// the lucide icons drawn by name come into the page one by one, and the
// sprite's text when the app is idle - not the whole sprite at the start
import { caricaQuandoLibero } from '@/utils/icone'

let globalComponents = {
  Button,
  TextInput,
  Input,
  FormControl,
  ErrorMessage,
  Dialog,
  Alert,
  Badge,
  FeatherIcon,
}

// the product's brand - the vertical's - before anything is drawn: its colours,
// favicon, name and home-screen icon (crm.marchio)
indossa()
// the browser's offer to put the app on the home screen, kept for the More
// page (utils/installa.js)
ascoltaLInstallazione()
// a part that no longer exists on the server (a new version came out while the
// page was open): the page loads again, once (utils/ricarica.js)
ricaricaSeManca()

// a notification touched while DottorCloud is open goes to its page without
// loading it again, and says so at once: a page that does not answer is
// loaded there by the worker (crm/notifiche/spinta_sw.js)
navigator.serviceWorker?.addEventListener('message', (evento) => {
  if (evento.data?.tipo !== 'apri') return
  const percorso = percorsoDellApp(evento.data.url)
  if (!percorso) return
  evento.ports?.[0]?.postMessage('andata')
  router.push(percorso)
})
// where they were turned on, the server knows this browser is this person's:
// once the app is idle, never before the first page (composables/spinta.js)
if (window.Notification?.permission === 'granted') {
  const quandoLibero =
    window.requestIdleCallback || ((fai) => setTimeout(fai, 3000))
  quandoLibero(() =>
    import('@/composables/spinta')
      .then((spinta) => spinta.sincronizza())
      .catch(() => {}),
  )
}

// create a pinia instance
let pinia = createPinia()

let app = createApp(App)

setConfig('resourceFetcher', frappeRequest)
// no telemetry plugin: DottorCloud sends nothing about its use to anybody
// (crm/telemetria.py); the capture() calls left in the components do nothing
app.use(FrappeUI)
app.use(pinia)
app.use(router)
app.use(translationPlugin)
for (let key in globalComponents) {
  app.component(key, globalComponents[key])
}

app.config.globalProperties.$dialog = createDialog

let socket
if (import.meta.env.DEV) {
  frappeRequest({ url: '/api/method/crm.www.crm.get_context_for_dev' }).then(
    (values) => {
      for (let key in values) {
        window[key] = values[key]
      }
      socket = initSocket()
      app.config.globalProperties.$socket = socket
      app.mount('#app')
    },
  )
} else {
  socket = initSocket()
  app.config.globalProperties.$socket = socket
  app.mount('#app')
}

if (import.meta.env.DEV) {
  window.$dialog = createDialog
}

caricaQuandoLibero()
