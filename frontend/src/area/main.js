// The patient area: its own app, never the CRM's (crm/www/area.py).
import './area.css'

import { createApp } from 'vue'
import { frappeRequest, setConfig } from 'frappe-ui'
import App from './App.vue'
import router from './router'
import { translate } from './translation'
import { indossa, marchio } from '@/utils/marchio'

// the product's brand - the vertical's - before anything shows: its colours,
// its icons, its name in the tab next to the centre's
indossa(document, marchio(window.AREA?.brand))

setConfig('resourceFetcher', frappeRequest)

const app = createApp(App)
app.use(router)
app.config.globalProperties.__ = translate
window.__ = translate
app.mount('#app')
