<!--
  Modifications copyright (c) 2026, NPM2 Solutions Srl
-->
<template>
  <Dialog
    v-model:open="showSettings"
    :size="'5xl'"
    :disableOutsideClickToClose="disableSettingModalOutsideClick"
    @close="activeSettingsPage = ''"
  >
    <template #body>
      <!-- Two levels: the categories on the left, each with its icon; on the
           right a category's entries, each saying what it is for, and the
           entry one opens, with the way back to its category. On a phone they
           do not fit side by side, so it becomes a list that pushes to a page
           and comes back, and it takes the whole screen (`.settings-modal` in
           telefono.css): as a card it kept frappe-ui's margins, 16px a side and
           48px above, and was 32px taller than the screen. -->
      <div
        ref="radice"
        class="settings-modal flex bg-surface-gray-1"
        :class="
          isMobileView ? 'h-app pb-safe pt-safe' : 'h-[calc(100vh_-_8rem)]'
        "
      >
        <div
          class="flex shrink-0 flex-col overflow-y-auto bg-surface-gray-1"
          :class="
            isMobileView
              ? ['w-full', { hidden: showingDetail }]
              : 'm-1 w-56 rounded-l-lg'
          "
        >
          <!-- On a phone the categories are a page of their own: a large title,
               the way out (the `#body` slot suppresses the dialog's own chrome,
               and there is no backdrop left to tap), the categories as rows a
               thumb hits, each with its icon in a tile. -->
          <template v-if="isMobileView">
            <div class="flex items-center justify-between gap-2 px-4 pb-2 pt-3">
              <h1 class="text-2xl-semibold text-ink-gray-9">
                {{ __('Settings') }}
              </h1>
              <Button
                variant="ghost"
                size="md"
                icon="x"
                :aria-label="__('Close')"
                @click="showSettings = false"
              />
            </div>
            <nav class="px-4 pb-8 pt-2" :aria-label="__('Settings')">
              <ul
                class="divide-y divide-outline-gray-1 overflow-hidden rounded-2xl bg-surface-elevation-1 shadow-sm ring-1 ring-outline-gray-1"
              >
                <li v-for="gruppo in tabs" :key="gruppo.key">
                  <button
                    type="button"
                    class="flex min-h-[3.25rem] w-full items-center gap-3 px-4 py-2 text-left active:bg-surface-gray-2"
                    @click="apriCategoria(gruppo.key)"
                  >
                    <span
                      class="grid size-8 shrink-0 place-items-center rounded-lg bg-surface-gray-2 text-ink-gray-7"
                      aria-hidden="true"
                    >
                      <Icon :icon="gruppo.icon" class="size-[18px]" />
                    </span>
                    <span
                      class="min-w-0 flex-1 truncate text-base text-ink-gray-9"
                    >
                      {{ __(gruppo.label) }}
                    </span>
                    <span
                      class="lucide-chevron-right size-5 shrink-0 text-ink-gray-4"
                      aria-hidden="true"
                    />
                  </button>
                </li>
              </ul>
            </nav>
          </template>
          <div
            v-else
            class="flex items-center justify-between px-2 py-1.5 md:pt-3"
          >
            <span class="text-base-medium text-ink-gray-9">
              {{ __('Settings') }}
            </span>
          </div>
          <nav
            v-if="!isMobileView"
            class="space-y-[3px] px-1 pb-2"
            :aria-label="__('Settings')"
          >
            <SidebarItem
              v-for="gruppo in tabs"
              :key="gruppo.key"
              :label="__(gruppo.label)"
              :active="categoria === gruppo.key"
              class="w-full"
              :class="categoria !== gruppo.key && 'hover:!bg-surface-gray-3'"
              @click="apriCategoria(gruppo.key)"
            >
              <template #prefix>
                <Icon :icon="gruppo.icon" class="size-4 text-ink-gray-7" />
              </template>
            </SidebarItem>
          </nav>
        </div>
        <!-- the pane a page is drawn in, and what its layout follows
             (`impostazioni-strette:` in tailwind.config.js): upright on a
             tablet it is 500px, a phone's width beside the menu -->
        <div
          class="flex flex-1 flex-col overflow-y-auto bg-surface-elevation-2 [container-name:impostazioni] [container-type:inline-size]"
          :class="{ hidden: isMobileView && !showingDetail }"
        >
          <div
            v-if="isMobileView"
            class="sticky top-0 z-10 flex min-h-12 items-center justify-between gap-2 border-b border-outline-elevation-2 bg-surface-elevation-2 pl-1 pr-2"
          >
            <!-- named after where it goes, as an app's bar does: the page
                 below says where one is with its own title -->
            <button
              type="button"
              class="flex h-11 min-w-0 items-center gap-0.5 rounded-lg pl-1 pr-2 text-base text-[var(--brand-action)] active:opacity-60"
              @click="indietro"
            >
              <span
                class="lucide-chevron-left size-6 shrink-0"
                aria-hidden="true"
              />
              <span class="truncate">
                {{
                  __(
                    activeTab && gruppoAperto ? gruppoAperto.label : 'Settings',
                  )
                }}
              </span>
            </button>
            <Button
              variant="ghost"
              size="md"
              icon="x"
              class="shrink-0"
              :aria-label="__('Close')"
              @click="showSettings = false"
            />
          </div>
          <template v-if="activeTab">
            <!-- the way back to the category the entry belongs to -->
            <div v-if="!isMobileView && gruppoAperto" class="px-6 pt-5">
              <button
                type="button"
                class="inline-flex items-center gap-1 rounded text-sm text-ink-gray-5 hover:text-ink-gray-8"
                @click="apriCategoria(gruppoAperto.key)"
              >
                <span class="lucide-chevron-left size-4" aria-hidden="true" />
                {{ __(gruppoAperto.label) }}
              </button>
            </div>
            <!-- an entry with several sides draws its tabs; the others are one page -->
            <SettingsHub
              v-if="activeTab.tabs"
              :key="activeTab.key"
              :voce="activeTab"
            />
            <!-- the page, as one scroll on a phone (telefono.css) -->
            <div v-else data-pagina-impostazioni class="contents">
              <component :is="activeTab.component" />
            </div>
            <!-- a page's «Update» on a phone (AzioneImpostazioni.vue): at the
                 bottom of the screen, where a thumb is, in sight however far
                 the page scrolls; nothing while there is nothing to save -->
            <div
              v-if="isMobileView"
              id="barra-impostazioni"
              class="sticky bottom-0 z-10 mt-auto border-t border-outline-elevation-2 bg-surface-elevation-2 px-3 pb-[max(0.75rem,env(safe-area-inset-bottom))] pt-3 empty:hidden"
            />
          </template>
          <!-- a category: what it is for, and each of its entries with a line
               on what one sets up there -->
          <div
            v-else-if="gruppoAperto"
            class="flex flex-col gap-6 px-6 py-8 max-md:px-3 max-md:py-5"
          >
            <div class="flex items-start gap-3 px-2">
              <span
                class="grid size-9 shrink-0 place-items-center rounded-lg bg-surface-gray-2"
                aria-hidden="true"
              >
                <Icon
                  :icon="gruppoAperto.icon"
                  class="size-5 text-ink-gray-7"
                />
              </span>
              <div class="flex min-w-0 flex-col gap-1">
                <h2 class="text-2xl-semibold leading-tight text-ink-gray-8">
                  {{ __(gruppoAperto.label) }}
                </h2>
                <p class="text-p-base text-ink-gray-6">
                  {{ __(gruppoAperto.description) }}
                </p>
              </div>
            </div>
            <ul
              class="flex flex-col divide-y divide-outline-elevation-2 rounded-lg border border-outline-gray-2"
            >
              <li v-for="voce in gruppoAperto.items" :key="voce.key">
                <button
                  type="button"
                  class="flex w-full items-center gap-3 px-4 py-3 text-left hover:bg-surface-gray-1 focus-visible:bg-surface-gray-1"
                  @click="openSettingsPage(voce.key)"
                >
                  <span class="flex min-w-0 flex-1 flex-col gap-0.5">
                    <span class="text-base-medium text-ink-gray-8">
                      {{ __(voce.label) }}
                    </span>
                    <span class="text-p-sm text-ink-gray-5">
                      {{ __(voce.description) }}
                    </span>
                  </span>
                  <span
                    class="lucide-chevron-right size-4 shrink-0 text-ink-gray-4"
                    aria-hidden="true"
                  />
                </button>
              </li>
            </ul>
          </div>
        </div>
      </div>
    </template>
  </Dialog>
</template>
<script setup>
import LucideReceipt from '~icons/lucide/receipt-text'
import LucideBuilding from '~icons/lucide/building-2'
import LucideCalendarDays from '~icons/lucide/calendar-days'
import LucideMegaphone from '~icons/lucide/megaphone'
import LucidePlug from '~icons/lucide/plug-zap'
import LucideUsers from '~icons/lucide/users'
import KanbanIcon from '@/components/Icons/KanbanIcon.vue'
import WhatsAppIcon from '@/components/Icons/WhatsAppIcon.vue'
import PhoneIcon from '@/components/Icons/PhoneIcon.vue'
import Email2Icon from '@/components/Icons/Email2Icon.vue'
import SettingsHub from '@/components/Settings/SettingsHub.vue'
import Icon from '@/components/Icon.vue'
import { usersStore } from '@/stores/users'
import { aRichiesta } from '@/utils/aRichiesta'
import {
  showSettings,
  activeSettingsPage,
  isMobileView,
  disableSettingModalOutsideClick,
} from '@/composables/settings'
import { isWhatsappInstalled } from '@/composables/whatsapp'
import { menuDi, trova } from '@/utils/impostazioni'
import { chiudeConIndietro } from '@/utils/indietro'
import { Button, Dialog, Avatar, SidebarItem } from 'frappe-ui'
import { ref, markRaw, computed, watch, h, provide, onBeforeUnmount } from 'vue'

const { getUser, puo, ambito } = usersStore()

const user = computed(() => getUser() || {})

// What each page is drawn with, by the name it has in the menu
// (utils/impostazioni.js): an entry of its own, or a tab of one. Each comes
// when it is opened: the modal is always mounted, and its pages imported here
// were in every page's first download.
const PAGINE = {
  Profile: aRichiesta(
    () => import('@/components/Settings/Profile/ProfilePage.vue'),
  ),
  Preferences: aRichiesta(
    () => import('@/components/Settings/PreferencesSettings.vue'),
  ),
  Notifications: aRichiesta(
    () => import('@/components/Settings/NotificationsSettings.vue'),
  ),
  'Your email': aRichiesta(
    () => import('@/components/Settings/Profile/MyEmail.vue'),
  ),
  'Google Calendar': aRichiesta(
    () => import('@/components/Settings/GoogleCalendarSettings.vue'),
  ),
  Brand: aRichiesta(() => import('@/components/Settings/BrandSettings.vue')),
  Language: aRichiesta(
    () => import('@/components/Settings/CentreLanguageSettings.vue'),
  ),
  General: aRichiesta(
    () => import('@/components/Settings/GeneralSettings.vue'),
  ),
  Dashboard: aRichiesta(
    () => import('@/components/Settings/DashboardSettings.vue'),
  ),
  'Home Actions': aRichiesta(
    () => import('@/components/Settings/HomeActions.vue'),
  ),
  Defaults: aRichiesta(
    () => import('@/components/Settings/DefaultsSettings.vue'),
  ),
  Users: aRichiesta(() => import('@/components/Settings/Users.vue')),
  'Invite User': aRichiesta(
    () => import('@/components/Settings/InviteUserPage.vue'),
  ),
  'Sales Hierarchy': aRichiesta(
    () => import('@/components/Settings/Hierarchy/Hierarchy.vue'),
  ),
  Plan: aRichiesta(() => import('@/components/Settings/PlanSettings.vue')),
  'Your data': aRichiesta(
    () => import('@/components/Settings/YourDataSettings.vue'),
  ),
  'Demo data': aRichiesta(
    () => import('@/components/Settings/DemoDataSettings.vue'),
  ),
  Services: aRichiesta(
    () => import('@/components/Settings/Scheduling/ServicesSettings.vue'),
  ),
  'Price Lists': aRichiesta(
    () => import('@/components/Settings/Scheduling/PriceListsSettings.vue'),
  ),
  Subscriptions: aRichiesta(
    () =>
      import('@/components/Settings/Scheduling/SubscriptionTypesSettings.vue'),
  ),
  'Studio hours & rules': aRichiesta(
    () => import('@/components/Settings/Scheduling/SchedulingDefaults.vue'),
  ),
  'Team rota': aRichiesta(
    () => import('@/components/Settings/Scheduling/StaffSchedulesSettings.vue'),
  ),
  'Rooms & Equipment': aRichiesta(
    () => import('@/components/Settings/Scheduling/ResourcesSettings.vue'),
  ),
  'Calendar & reminders': aRichiesta(
    () => import('@/components/Settings/CalendarSettings.vue'),
  ),
  'Appointment reminders': aRichiesta(
    () => import('@/components/Settings/Scheduling/RemindersSettings.vue'),
  ),
  'Waiting list': aRichiesta(
    () => import('@/components/Settings/Scheduling/WaitingListSettings.vue'),
  ),
  'Online booking': aRichiesta(
    () => import('@/components/Settings/Booking/OnlineBookingSetup.vue'),
  ),
  'Page & rules': aRichiesta(
    () => import('@/components/Settings/Booking/BookingPageSettings.vue'),
  ),
  'Booking platforms': aRichiesta(
    () => import('@/components/Settings/Booking/BookingPlatforms.vue'),
  ),
  Forms: aRichiesta(
    () => import('@/components/Settings/Forms/FormsSettings.vue'),
  ),
  Consents: aRichiesta(
    () => import('@/components/Settings/ConsentsSettings.vue'),
  ),
  'News in the client area': aRichiesta(
    () => import('@/components/Settings/AreaNoticeSettings.vue'),
  ),
  Exercises: aRichiesta(
    () => import('@/components/Settings/Plans/ExercisesSettings.vue'),
  ),
  Foods: aRichiesta(
    () => import('@/components/Settings/Clinic/FoodsSettings.vue'),
  ),
  Pipelines: aRichiesta(
    () => import('@/components/Settings/Pipelines/PipelinesSettings.vue'),
  ),
  'Assignment Rules': aRichiesta(
    () =>
      import('@/components/Settings/AssignmentRules/AssignmentRulePage.vue'),
  ),
  'SLA Policies': aRichiesta(
    () => import('@/components/Settings/Sla/SlaConfig.vue'),
  ),
  Accounts: aRichiesta(() => import('@/components/Settings/EmailConfig.vue')),
  Templates: aRichiesta(
    () => import('@/components/Settings/EmailTemplate/EmailTemplatePage.vue'),
  ),
  WhatsApp: aRichiesta(
    () => import('@/components/Settings/WhatsAppSettings.vue'),
  ),
  'WhatsApp Templates': aRichiesta(
    () => import('@/components/Settings/WhatsAppTemplates.vue'),
  ),
  Telephony: aRichiesta(
    () => import('@/components/Settings/Telephony/TelephonyPage.vue'),
  ),
  'Call Scripts': aRichiesta(
    () => import('@/components/Settings/CallScriptsSettings.vue'),
  ),
  Website: aRichiesta(
    () => import('@/components/Settings/Website/WebsiteSettings.vue'),
  ),
  'Social profiles': aRichiesta(
    () => import('@/components/Settings/Social/SocialSettings.vue'),
  ),
  'Lead Tracking': aRichiesta(
    () => import('@/components/Settings/TrackingSettings.vue'),
  ),
  'Tracked Links': aRichiesta(
    () => import('@/components/Settings/TrackedLinksSettings.vue'),
  ),
  'Issuing company': aRichiesta(
    () => import('@/components/Settings/Invoicing/InvoicingCompany.vue'),
  ),
  'Provider connection': aRichiesta(
    () => import('@/components/Settings/Invoicing/ProviderConnection.vue'),
  ),
  'Fatture in Cloud': aRichiesta(
    () => import('@/components/Settings/Invoicing/FattureInCloud.vue'),
  ),
  'Billable services': aRichiesta(
    () =>
      import('@/components/Settings/Invoicing/BillableServicesSettings.vue'),
  ),
  Providers: aRichiesta(
    () => import('@/components/Settings/Invoicing/ProvidersSettings.vue'),
  ),
  'Qualification register': aRichiesta(
    () => import('@/components/Settings/Invoicing/QualificationsSettings.vue'),
  ),
  'Invoicing defaults': aRichiesta(
    () => import('@/components/Settings/Invoicing/InvoicingDefaults.vue'),
  ),
  // one page with its own tabs: the connection and the three things it feeds
  'Meta connection': aRichiesta(
    () => import('@/components/Settings/Meta/MetaSettings.vue'),
  ),
  'Seal and time stamp': aRichiesta(
    () => import('@/components/Settings/SealSettings.vue'),
  ),
  Assistant: aRichiesta(
    () => import('@/components/Settings/AssistantSettings.vue'),
  ),
}

// The icon of each category: the categories carry them, their entries are
// read by their words (and the line under each).
const ICONE = {
  account: () =>
    h(Avatar, {
      size: 'xs',
      label: user.value.full_name,
      image: user.value.user_image,
    }),
  centre: LucideBuilding,
  agenda: LucideCalendarDays,
  clients: LucideUsers,
  deals: KanbanIcon,
  email: Email2Icon,
  whatsapp: WhatsAppIcon,
  phone: PhoneIcon,
  marketing: LucideMegaphone,
  invoicing: LucideReceipt,
  integrations: LucidePlug,
}

// a component, an icon: never made reactive along with the entry holding it
const fermo = (cosa) =>
  cosa && typeof cosa === 'object' ? markRaw(cosa) : cosa

// The menu this person sees (each page asks for the capability of its own
// screen, doc 30), with what its pages and entries are drawn with.
const tabs = computed(() =>
  menuDi({
    puo,
    ambito,
    whatsapp: isWhatsappInstalled.value,
    verticale: window.vertical?.key || null,
  }).map((gruppo) => ({
    ...gruppo,
    icon: fermo(ICONE[gruppo.key]),
    items: gruppo.items.map((voce) => ({
      ...voce,
      component: voce.tabs ? null : fermo(PAGINE[voce.key]),
      tabs: voce.tabs?.map((scheda) => ({
        ...scheda,
        component: fermo(PAGINE[scheda.key]),
      })),
    })),
  })),
)

// the pages that send one elsewhere in the settings (the features page, to
// where each one is set up) link only to what this person sees
provide('menuDelleImpostazioni', tabs)

// The category open on the left, and the entry open on the right: none, and
// the right pane shows the category's entries, each saying what it is for.
const categoria = ref(tabs.value[0]?.key)
const activeTab = ref(null)
const gruppoAperto = computed(
  () => tabs.value.find((gruppo) => gruppo.key === categoria.value) || null,
)

function gruppoDi(voce) {
  return tabs.value.find((gruppo) =>
    gruppo.items.some((item) => item.key === voce?.key),
  )
}

function setActiveTab(tabName) {
  // A deep link built server-side (an OAuth callback sending the browser back
  // here) names the page by its key, which is not translated; a page that is a
  // tab now, or used to be a page of its own (an alias), opens the entry holding
  // it. A screen outside the modal may still ask by the English label.
  const voce = trova(tabs.value, tabName, (testo) => __(testo))?.voce || null
  activeTab.value = voce
  if (voce) categoria.value = gruppoDi(voce)?.key || categoria.value
}

// A category: its entries on the right, no entry open.
function apriCategoria(chiave) {
  categoria.value = chiave
  activeTab.value = null
  activeSettingsPage.value = ''
  showingDetail.value = true
}

// The phone's way back: from an entry to its category, from a category to the
// list of categories.
function indietro() {
  if (activeTab.value) apriCategoria(categoria.value)
  else showingDetail.value = false
}

// Which pane a phone is looking at. Ignored on anything wider, where both are
// always on screen.
const showingDetail = ref(false)

// on a phone Android's back takes the settings one step back, as their own
// bar does, before it closes them (utils/indietro.js)
const radice = ref(null)
let togliDaIndietro = null
watch(
  () => showSettings.value && isMobileView.value && showingDetail.value,
  (dentro) => {
    togliDaIndietro?.()
    togliDaIndietro = dentro ? chiudeConIndietro(indietro, radice) : null
  },
  { immediate: true },
)
onBeforeUnmount(() => togliDaIndietro?.())

watch(showSettings, (open) => {
  if (!open) return
  showingDetail.value = !!activeSettingsPage.value
  // opened without a page: the first category's entries
  if (!activeSettingsPage.value) {
    activeTab.value = null
    categoria.value = categoria.value || tabs.value[0]?.key
  }
})

watch(activeSettingsPage, (activePage) => {
  setActiveTab(activePage)
  // Covers the deep link and the callers that jump straight to a page, such as
  // the sidebar's "Invite User".
  if (activePage) showingDetail.value = true
})

// The page a link asks for can sit in a group whose condition is not known yet:
// the user's role and whether WhatsApp is installed both load in the
// background. The WhatsApp signup comes back to `?settings=WhatsApp` on a fresh
// page, and landed on Profile whenever it won that race. So when the menu
// changes, the page asked for is looked up again, and the entry open is taken
// as the new menu has it, with the tabs it has now.
watch(tabs, () => {
  if (activeSettingsPage.value) return setActiveTab(activeSettingsPage.value)
  const aperta = activeTab.value?.key
  activeTab.value = aperta
    ? tabs.value
        .flatMap((tab) => tab.items)
        .find((item) => item.key === aperta) || null
    : null
  if (!tabs.value.some((gruppo) => gruppo.key === categoria.value))
    categoria.value = tabs.value[0]?.key
})

// Tapping a row has to push to the detail even when it is the row you were last
// on: `activeSettingsPage` does not change then, so the watch above never fires.
function openSettingsPage(id) {
  activeSettingsPage.value = id
  setActiveTab(id)
  showingDetail.value = true
}

// deep link: /crm?settings=<page> opens the modal on that page (an OAuth
// callback, an email's preferences, a notification touched): the router reads
// it (router.js), maybe before the modal is drawn - then it opens as it is
if (showSettings.value && activeSettingsPage.value) {
  showingDetail.value = true
  setActiveTab(activeSettingsPage.value)
}
</script>
