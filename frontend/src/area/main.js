// The patient area: its own app, never the CRM's (crm/www/area.py).
import './area.css'

import { createApp } from 'vue'
import { frappeRequest, setConfig } from 'frappe-ui'
import App from './App.vue'
import router from './router'
import { translate } from './translation'
import { indossa, marchio } from '@/utils/marchio'
import { ascoltaLInstallazione } from '@/utils/installa'
import { seguiIlTemaDelTelefono } from '@/utils/temaDelTelefono'

// the product's brand - the vertical's - before anything shows: its colours,
// its icons, its name in the tab next to the centre's
indossa(document, marchio(window.AREA?.brand))
// the browser's offer to put the area on the home screen, kept for the card
ascoltaLInstallazione()
// light or dark as the phone is, and as it changes over
seguiIlTemaDelTelefono()

setConfig('resourceFetcher', frappeRequest)

const app = createApp(App)
app.use(router)
app.config.globalProperties.__ = translate
window.__ = translate
app.mount('#app')
