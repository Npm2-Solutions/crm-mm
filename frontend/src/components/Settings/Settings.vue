<template>
  <Dialog
    v-model:open="showSettings"
    :size="'5xl'"
    :disableOutsideClickToClose="disableSettingModalOutsideClick"
    @close="activeSettingsPage = ''"
  >
    <template #body>
      <!-- Two panes side by side on a desktop. On a phone they do not fit, so it
           becomes a list that pushes to a page and comes back, and it takes
           the whole screen (`.settings-modal` in index.css): as a card it
           kept frappe-ui's margins, 16px a side and 48px above, and was 32px
           taller than the screen, with its bottom row cut off. -->
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
            v-if="isMobileView"
            class="flex items-center justify-between px-2 py-1.5"
          >
            <span class="text-base-medium text-ink-gray-9">
              {{ __('Settings') }}
            </span>
            <Button
              variant="ghost"
              icon="x"
              :aria-label="__('Close')"
              @click="showSettings = false"
            />
          </div>
          <!-- One box per group: a sticky label sticks only inside its own
               parent, and with every label in one scroller they all stayed
               pinned and piled up, one group's name over the next one's. -->
          <div v-for="(tab, i) in tabs" :key="tab.key">
            <div v-if="i != 0" class="mx-1 mb-0.5 mt-[5px]" />
            <div
              class="h-7.5 px-2 py-[7px] my-[3px] flex cursor-pointer gap-1.5 text-xs-medium text-ink-gray-5 transition-all duration-300 ease-in-out sticky top-0 z-10 bg-surface-gray-1"
            >
              <span>{{ __(tab.label) }}</span>
            </div>
            <nav class="space-y-[3px] px-1">
              <SidebarItem
                v-for="item in tab.items"
                :key="itemId(item)"
                :label="__(item.label)"
                :active="isActive(item)"
                class="w-full"
                :class="!isActive(item) && 'hover:!bg-surface-gray-3'"
                @click="openSettingsPage(itemId(item))"
              >
                <template #prefix>
                  <Icon :icon="item.icon" class="size-4 text-ink-gray-7" />
                </template>
              </SidebarItem>
            </nav>
          </div>
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
              @click="showingDetail = false"
            />
            <span class="truncate text-base-medium text-ink-gray-9">
              {{ __(activeTab?.title || activeTab?.label || 'Settings') }}
            </span>
          </div>
          <!-- an entry with several sides draws its tabs; the others are one page -->
          <SettingsHub
            v-if="activeTab?.tabs"
            :key="activeTab.key"
            :voce="activeTab"
          />
          <component :is="activeTab.component" v-else-if="activeTab" />
        </div>
      </div>
    </template>
  </Dialog>
</template>
<script setup>
import LucideCalendarCog from '~icons/lucide/calendar-cog'
import LucidePackage from '~icons/lucide/package'
import LucideFileCheck from '~icons/lucide/file-check'
import LucideTextCursorInput from '~icons/lucide/text-cursor-input'
import LucideSparkles from '~icons/lucide/sparkles'
import LucideInfinity from '~icons/lucide/infinity'
import LucideDoorOpen from '~icons/lucide/door-open'
import LucideClock from '~icons/lucide/clock'
import LucideHourglass from '~icons/lucide/hourglass'
import LucideCalendarCheck from '~icons/lucide/calendar-check'
import LucideBellRing from '~icons/lucide/bell-ring'
import LucideRadar from '~icons/lucide/radar'
import LucideListChecks from '~icons/lucide/list-checks'
import LucideReceipt from '~icons/lucide/receipt-text'
import LucideBuilding from '~icons/lucide/building-2'
import LucideUserCog from '~icons/lucide/user-cog'
import LucidePlug from '~icons/lucide/plug-zap'
import LucideLibraryBig from '~icons/lucide/library-big'
import LucideStamp from '~icons/lucide/stamp'
import LucideBot from '~icons/lucide/bot'
import LucideGlobe from '~icons/lucide/globe'
import LucideUsers from '~icons/lucide/users'
import SlidersIcon from '@/components/Icons/SlidersIcon.vue'
import CalendarIcon from '@/components/Icons/CalendarIcon.vue'
import KanbanIcon from '@/components/Icons/KanbanIcon.vue'
import WhatsAppIcon from '@/components/Icons/WhatsAppIcon.vue'
import ERPNextIcon from '@/components/Icons/ERPNextIcon.vue'
import PhoneIcon from '@/components/Icons/PhoneIcon.vue'
import Email2Icon from '@/components/Icons/Email2Icon.vue'
import EmailTemplateIcon from '@/components/Icons/EmailTemplateIcon.vue'
import SettingsIcon from '@/components/Icons/SettingsIcon.vue'
import SettingsIcon2 from '@/components/Icons/SettingsIcon2.vue'
import SocialIcon from '@/components/Icons/SocialIcon.vue'
import Users from '@/components/Settings/Users.vue'
import Hierarchy from '@/components/Settings/Hierarchy/Hierarchy.vue'
import InviteUserPage from '@/components/Settings/InviteUserPage.vue'
import ProfilePage from '@/components/Settings/Profile/ProfilePage.vue'
import PreferencesSettings from '@/components/Settings/PreferencesSettings.vue'
import WhatsAppSettings from '@/components/Settings/WhatsAppSettings.vue'
import WhatsAppTemplates from '@/components/Settings/WhatsAppTemplates.vue'
import ERPNextSettings from '@/components/Settings/ERPNextSettings.vue'
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
import { ref, markRaw, computed, watch, h } from 'vue'
import AssignmentRulePage from './AssignmentRules/AssignmentRulePage.vue'
import SlaConfig from './Sla/SlaConfig.vue'

const { getUser, puo, ambito } = usersStore()

const user = computed(() => getUser() || {})

// What each page is drawn with, by the name it has in the menu
// (utils/impostazioni.js): an entry of its own, or a tab of one.
const PAGINE = {
  Profile: ProfilePage,
  Preferences: PreferencesSettings,
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
  ERPNext: ERPNextSettings,
  'Seal and time stamp': SealSettings,
  Assistant: AssistantSettings,
}

// The icon of each entry.
const ICONE = {
  Profile: () =>
    h(Avatar, {
      size: 'xs',
      label: user.value.full_name,
      image: user.value.user_image,
    }),
  Preferences: SlidersIcon,
  'Google Calendar': CalendarIcon,
  'General settings': SettingsIcon,
  Users: LucideUsers,
  Plan: LucidePackage,
  Services: LucideSparkles,
  'Hours & shifts': LucideClock,
  'Rooms & Equipment': LucideDoorOpen,
  'Calendar & reminders': LucideCalendarCog,
  'Waiting list': LucideHourglass,
  'Online booking': LucideCalendarCheck,
  Forms: LucideTextCursorInput,
  Consents: LucideFileCheck,
  'News in the client area': LucideBellRing,
  Libraries: LucideLibraryBig,
  Pipelines: KanbanIcon,
  Assignment: h(SettingsIcon2, { class: 'rotate-90' }),
  Accounts: Email2Icon,
  Templates: EmailTemplateIcon,
  WhatsApp: WhatsAppIcon,
  'WhatsApp Templates': EmailTemplateIcon,
  Telephony: PhoneIcon,
  'Call Scripts': LucideListChecks,
  Website: LucideGlobe,
  'Social profiles': SocialIcon,
  Tracking: LucideRadar,
  'Issuing company': LucideBuilding,
  'Services & providers': LucideUserCog,
  'Provider connection': LucidePlug,
  'Invoicing defaults': LucideReceipt,
  // the Meta mark, near enough: the sprite has no 'facebook' any more
  'Meta connection': LucideInfinity,
  ERPNext: ERPNextIcon,
  'Seal and time stamp': LucideStamp,
  Assistant: LucideBot,
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
    items: gruppo.items.map((voce) => ({
      ...voce,
      icon: fermo(ICONE[voce.key]),
      component: voce.tabs ? null : fermo(PAGINE[voce.key]),
      tabs: voce.tabs?.map((scheda) => ({
        ...scheda,
        component: fermo(PAGINE[scheda.key]),
      })),
    })),
  })),
)

const activeTab = ref(tabs.value[0].items[0])

function itemId(item) {
  return item.key
}

function isActive(item) {
  return Boolean(activeTab.value) && itemId(activeTab.value) === itemId(item)
}

function setActiveTab(tabName) {
  // A deep link built server-side (an OAuth callback sending the browser back
  // here) names the page by its key, which is not translated; a page that is a
  // tab now, or used to be a page of its own (an alias), opens the entry holding
  // it. A screen outside the modal may still ask by the English label.
  activeTab.value =
    trova(tabs.value, tabName, (testo) => __(testo))?.voce ||
    tabs.value[0].items[0]
}

// Which pane a phone is looking at. Ignored on anything wider, where both are
// always on screen.
const showingDetail = ref(false)

watch(showSettings, (open) => {
  if (open) showingDetail.value = !!activeSettingsPage.value
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
  activeTab.value =
    tabs.value
      .flatMap((tab) => tab.items)
      .find((item) => item.key === aperta) || tabs.value[0].items[0]
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
