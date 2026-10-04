<!--
  Modifications copyright (c) 2026, NPM2 Solutions Srl
-->
<template>
  <FrappeUIProvider>
    <NotPermitted v-if="$route.name === 'Not Permitted'" />
    <router-view v-else-if="$route.name === 'Onboarding'" />
    <!-- The page designer takes the whole viewport: the CRM's sidebar and header on top
         of Builder's own toolbar would be three bars stacked over one canvas. -->
    <router-view
      v-else-if="session.isLoggedIn && $route.name === 'WebsitePage'"
    />
    <Layout v-else-if="session.isLoggedIn" class="isolate">
      <!-- the page's name, for a screen reader's headings: on a phone it is a
           link or a switch in the header, never a heading -->
      <h1 v-if="titolo" id="titolo-pagina" tabindex="-1" class="sr-only">
        {{ __(titolo) }}
      </h1>
      <!-- keyed on the page, not on its tab: another record is another page,
           but the hash only names the tab (or the message a notification
           opens), and the whole record was unmounted and mounted again at
           every tab -->
      <router-view :key="chiaveDellaPagina" />
    </Layout>
    <Dialogs />
    <DoctypeModals />
    <EventNotificationPopup />
  </FrappeUIProvider>
</template>

<script setup>
import NotPermitted from '@/pages/NotPermitted.vue'
import EventNotificationPopup from '@/components/EventNotificationPopup.vue'
import DoctypeModals from '@/components/Modals/DoctypeModals.vue'
import { Dialogs } from '@/utils/dialogs'
import { sessionStore } from '@/stores/session'
import { isMobileView } from '@/composables/breakpoints'
import { titoloDellaPagina } from '@/utils/menu'
import { useRoute } from 'vue-router'
import { FrappeUIProvider, dayjs, setConfig, useTheme } from 'frappe-ui'
import 'dayjs/esm/locale/it'
import { computed, defineAsyncComponent, provide } from 'vue'

const session = sessionStore()
provide('session', session)

const route = useRoute()
const titolo = computed(() => titoloDellaPagina(route.name))
const chiaveDellaPagina = computed(() => route.fullPath.split('#')[0])

const { setTheme } = useTheme()
if (!localStorage.getItem('theme')) {
  setTheme('light')
}

const MobileLayout = defineAsyncComponent(
  () => import('./components/Layouts/MobileLayout.vue'),
)
const DesktopLayout = defineAsyncComponent(
  () => import('./components/Layouts/DesktopLayout.vue'),
)
// Reactive, so rotating a phone or resizing a window actually swaps the shell —
// and so it agrees with the router, which picks the Mobile* detail pages off the
// same breakpoint.
const Layout = computed(() =>
  isMobileView.value ? MobileLayout : DesktopLayout,
)

setConfig('systemTimezone', window.timezone?.system || null)
setConfig('localTimezone', window.timezone?.user || null)
setConfig('translatedMessages', window.translated_messages || {})
// the dates dayjs writes - formatDate, the agenda's headers, «3 minuti fa» - in
// the user's language: «mercoledì 30 settembre» under Italian words, not
// «Wednesday 30 September». Italian is the product's own; any other language
// keeps dayjs's English
if (String(window.lang || '').startsWith('it')) dayjs.locale('it')
</script>
