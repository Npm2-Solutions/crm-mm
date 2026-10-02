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
           index.css): as a card it kept frappe-ui's margins, 16px a side and
           48px above, and was 32px taller than the screen. -->
      <div
        class="settings-modal flex bg-surface-gray-1"
        :class="
          isMobileView ? 'h-app pb-safe pt-safe' : 'h-[calc(100vh_-_8rem)]'
        "
      >
        <div
          class="m-1 flex shrink-0 flex-col overflow-y-auto rounded-l-lg bg-surface-gray-1"
          :class="
            isMobileView
              ? ['w-full rounded-lg', { hidden: showingDetail }]
              : 'w-56'
          "
        >
          <!-- The `#body` slot suppresses the dialog's own chrome, so on a phone
               — where there is no backdrop left to tap — this is the only way out. -->
          <div
            class="flex items-center justify-between px-2 py-1.5"
            :class="{ 'md:pt-3': !isMobileView }"
          >
            <span class="text-base-medium text-ink-gray-9">
              {{ __('Settings') }}
            </span>
            <Button
              v-if="isMobileView"
              variant="ghost"
              icon="x"
              :aria-label="__('Close')"
              @click="showSettings = false"
            />
          </div>
          <nav class="space-y-[3px] px-1 pb-2" :aria-label="__('Settings')">
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
        <div
          class="flex flex-1 flex-col overflow-y-auto bg-surface-elevation-2"
          :class="{ hidden: isMobileView && !showingDetail }"
        >
          <div
            v-if="isMobileView"
            class="sticky top-0 z-10 flex items-center gap-1 border-b border-outline-elevation-2 bg-surface-elevation-2 px-2 py-1.5"
          >
            <Button
              variant="ghost"
              icon="chevron-left"
              :aria-label="__('Back')"
              @click="indietro"
            />
            <span class="truncate text-base-medium text-ink-gray-9">
              {{
                __(
                  activeTab
                    ? activeTab.title || activeTab.label
                    : gruppoAperto?.label || 'Settings',
                )
              }}
            </span>
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
            <component :is="activeTab.component" v-else />
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
import Users from '@/components/Settings/Users.vue'
import Hierarchy from '@/components/Settings/Hierarchy/Hierarchy.vue'
import InviteUserPage from '@/components/Settings/InviteUserPage.vue'
import ProfilePage from '@/components/Settings/Profile/ProfilePage.vue'
import PreferencesSettings from '@/components/Settings/PreferencesSettings.vue'
import NotificationsSettings from '@/components/Settings/NotificationsSettings.vue'
import MyEmail from '@/components/Settings/Profile/MyEmail.vue'
import WhatsAppSettings from '@/components/Settings/WhatsAppSettings.vue'
import WhatsAppTemplates from '@/components/Settings/WhatsAppTemplates.vue'
import DefaultsSettings from '@/components/Settings/DefaultsSettings.vue'
import BrandSettings from '@/components/Settings/BrandSettings.vue'
import CalendarSettings from '@/components/Settings/CalendarSettings.vue'
import HomeActions from '@/components/Settings/HomeActions.vue'
import FormsSettings from '@/components/Settings/Forms/FormsSettings.vue'
import AssistantSettings from '@/components/Settings/AssistantSettings.vue'
import SealSettings from '@/components/Settings/SealSettings.vue'
import AreaNoticeSettings from '@/components/Settings/AreaNoticeSettings.vue'
import ExercisesSettings from '@/components/Settings/Plans/ExercisesSettings.vue'
import FoodsSettings from '@/components/Settings/Clinic/FoodsSettings.vue'
import GeneralSettings from '@/components/Settings/GeneralSettings.vue'
import DashboardSettings from '@/components/Settings/DashboardSettings.vue'
import EmailTemplatePage from '@/components/Settings/EmailTemplate/EmailTemplatePage.vue'
import TelephonyPage from '@/components/Settings/Telephony/TelephonyPage.vue'
import BookingPlatforms from '@/components/Settings/Booking/BookingPlatforms.vue'
import BookingPageSettings from '@/components/Settings/Booking/BookingPageSettings.vue'
import OnlineBookingSetup from '@/components/Settings/Booking/OnlineBookingSetup.vue'
import GoogleCalendarSettings from '@/components/Settings/GoogleCalendarSettings.vue'
import ServicesSettings from '@/components/Settings/Scheduling/ServicesSettings.vue'
import ResourcesSettings from '@/components/Settings/Scheduling/ResourcesSettings.vue'
import PriceListsSettings from '@/components/Settings/Scheduling/PriceListsSettings.vue'
import StaffSchedulesSettings from '@/components/Settings/Scheduling/StaffSchedulesSettings.vue'
import SchedulingDefaults from '@/components/Settings/Scheduling/SchedulingDefaults.vue'
import WaitingListSettings from '@/components/Settings/Scheduling/WaitingListSettings.vue'
import SubscriptionTypesSettings from '@/components/Settings/Scheduling/SubscriptionTypesSettings.vue'
import PipelinesSettings from '@/components/Settings/Pipelines/PipelinesSettings.vue'
import CallScriptsSettings from '@/components/Settings/CallScriptsSettings.vue'
import MetaSettings from '@/components/Settings/Meta/MetaSettings.vue'
import SocialSettings from '@/components/Settings/Social/SocialSettings.vue'
import WebsiteSettings from '@/components/Settings/Website/WebsiteSettings.vue'
import TrackedLinksSettings from '@/components/Settings/TrackedLinksSettings.vue'
import TrackingSettings from '@/components/Settings/TrackingSettings.vue'
import InvoicingCompany from '@/components/Settings/Invoicing/InvoicingCompany.vue'
import InvoicingDefaults from '@/components/Settings/Invoicing/InvoicingDefaults.vue'
import QualificationsSettings from '@/components/Settings/Invoicing/QualificationsSettings.vue'
import BillableServicesSettings from '@/components/Settings/Invoicing/BillableServicesSettings.vue'
import ProvidersSettings from '@/components/Settings/Invoicing/ProvidersSettings.vue'
import ProviderConnection from '@/components/Settings/Invoicing/ProviderConnection.vue'
import EmailConfig from '@/components/Settings/EmailConfig.vue'
import PlanSettings from '@/components/Settings/PlanSettings.vue'
import ConsentsSettings from '@/components/Settings/ConsentsSettings.vue'
import SettingsHub from '@/components/Settings/SettingsHub.vue'
import Icon from '@/components/Icon.vue'
import { usersStore } from '@/stores/users'
import {
  showSettings,
  activeSettingsPage,
  isMobileView,
  disableSettingModalOutsideClick,
} from '@/composables/settings'
import { isWhatsappInstalled } from '@/composables/whatsapp'
import { menuDi, trova } from '@/utils/impostazioni'
import { Button, Dialog, Avatar, SidebarItem } from 'frappe-ui'
import { ref, markRaw, computed, watch, h, provide } from 'vue'
import AssignmentRulePage from './AssignmentRules/AssignmentRulePage.vue'
import SlaConfig from './Sla/SlaConfig.vue'

const { getUser, puo, ambito } = usersStore()

const user = computed(() => getUser() || {})

// What each page is drawn with, by the name it has in the menu
// (utils/impostazioni.js): an entry of its own, or a tab of one.
const PAGINE = {
  Profile: ProfilePage,
  Preferences: PreferencesSettings,
  Notifications: NotificationsSettings,
  'Your email': MyEmail,
  'Google Calendar': GoogleCalendarSettings,
  Brand: BrandSettings,
  General: GeneralSettings,
  Dashboard: DashboardSettings,
  'Home Actions': HomeActions,
  Defaults: DefaultsSettings,
  Users,
  'Invite User': InviteUserPage,
  'Sales Hierarchy': Hierarchy,
  Plan: PlanSettings,
  Services: ServicesSettings,
  'Price Lists': PriceListsSettings,
  Subscriptions: SubscriptionTypesSettings,
  'Studio hours & rules': SchedulingDefaults,
  'Team rota': StaffSchedulesSettings,
  'Rooms & Equipment': ResourcesSettings,
  'Calendar & reminders': CalendarSettings,
  'Waiting list': WaitingListSettings,
  'Online booking': OnlineBookingSetup,
  'Page & rules': BookingPageSettings,
  'Booking platforms': BookingPlatforms,
  Forms: FormsSettings,
  Consents: ConsentsSettings,
  'News in the client area': AreaNoticeSettings,
  Exercises: ExercisesSettings,
  Foods: FoodsSettings,
  Pipelines: PipelinesSettings,
  'Assignment Rules': AssignmentRulePage,
  'SLA Policies': SlaConfig,
  Accounts: EmailConfig,
  Templates: EmailTemplatePage,
  WhatsApp: WhatsAppSettings,
  'WhatsApp Templates': WhatsAppTemplates,
  Telephony: TelephonyPage,
  'Call Scripts': CallScriptsSettings,
  Website: WebsiteSettings,
  'Social profiles': SocialSettings,
  'Lead Tracking': TrackingSettings,
  'Tracked Links': TrackedLinksSettings,
  'Issuing company': InvoicingCompany,
  'Provider connection': ProviderConnection,
  'Billable services': BillableServicesSettings,
  Providers: ProvidersSettings,
  'Qualification register': QualificationsSettings,
  'Invoicing defaults': InvoicingDefaults,
  // one page with its own tabs: the connection and the three things it feeds
  'Meta connection': MetaSettings,
  'Seal and time stamp': SealSettings,
  Assistant: AssistantSettings,
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

// deep link: /crm?settings=<page> opens the modal on that page (used by OAuth
// callbacks, e.g. the Meta Lead Ads connect flow)
const settingsParam = new URLSearchParams(window.location.search).get(
  'settings',
)
if (settingsParam) {
  showSettings.value = true
  activeSettingsPage.value = settingsParam
  setActiveTab(settingsParam)
}
</script>
