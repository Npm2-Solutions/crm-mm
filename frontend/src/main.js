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

import { telemetryPlugin } from 'frappe-ui/frappe'
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

// create a pinia instance
let pinia = createPinia()

let app = createApp(App)

setConfig('resourceFetcher', frappeRequest)
app.use(FrappeUI)
app.use(pinia)
app.use(router)
app.use(translationPlugin)
for (let key in globalComponents) {
  app.component(key, globalComponents[key])
}
app.use(telemetryPlugin, { app_name: 'crm' })

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
