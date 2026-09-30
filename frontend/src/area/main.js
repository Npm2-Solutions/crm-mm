// The patient area: its own app, never the CRM's (crm/www/area.py).
import './area.css'

import { createApp } from 'vue'
import { frappeRequest, setConfig } from 'frappe-ui'
import App from './App.vue'
import router from './router'
import { translate } from './translation'

setConfig('resourceFetcher', frappeRequest)

const app = createApp(App)
app.use(router)
app.config.globalProperties.__ = translate
window.__ = translate
app.mount('#app')
