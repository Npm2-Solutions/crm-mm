<template>
  <!-- The notifications panel is absolutely positioned at `left: 100%`, so it
       needs a positioning context that is not the Sidebar itself (Sidebar sets
       overflow-x-hidden, which would clip the panel away).

       It also paints the sidebar surface: Sidebar's own `bg-surface-sidebar` is
       transparent in dark mode, and nothing behind it sets a background, so the
       column falls through to the white page canvas. The token cannot be
       overridden on the Sidebar element itself — `bg-surface-sidebar` is emitted
       after `bg-surface-gray-1` in the utilities layer and would win. -->
  <div class="relative flex h-full bg-surface-gray-1">
    <Sidebar
      v-model:collapsed="isSidebarCollapsed"
      class="border-r border-outline-gray-1"
    >
      <div class="flex h-full flex-col p-2">
        <UserDropdown :isCollapsed="isCollapsed" />

        <!-- overflow-y-auto forces overflow-x to clip too, which would slice the
             active row's shadow. Widen the scroll box to the sidebar edges and
             pad the content back in so the shadow has room. -->
        <div class="-mx-2 mt-2 flex flex-1 flex-col gap-1 overflow-y-auto px-2">
          <SidebarItem
            id="notifications-btn"
            :label="__('Notifications')"
            @click="toggleNotificationPanel()"
          >
            <template #prefix>
              <span class="relative grid size-4 place-items-center">
                <NotificationsIcon class="size-4 text-ink-gray-7" />
                <span
                  v-if="isCollapsed && unreadNotificationsCount"
                  class="absolute -right-1 -top-1 size-1.5 rounded-full bg-[var(--brand-segno)] ring-1 ring-[var(--surface-gray-1)]"
                />
              </span>
            </template>
            <!-- what is new, in the brand's subtle as the design system has
                 its notices of news -->
            <template #suffix>
              <span
                v-if="unreadNotificationsCount"
                class="mr-2 rounded-full bg-[var(--brand-subtle)] px-1.5 text-xs font-medium leading-5 text-[var(--on-brand-subtle)]"
              >
                {{ unreadNotificationsCount }}
              </span>
            </template>
          </SidebarItem>

          <!-- the menu: the centre's work in groups (utils/menu.js), each with
               a small label as the design system draws them; collapsed, a line -->
          <template v-for="(gruppo, i) in menu" :key="gruppo.key">
            <template v-if="gruppo.label">
              <div
                v-if="!isCollapsed"
                class="mb-1 mt-4 select-none px-2 text-[11px] font-medium uppercase tracking-wide text-ink-gray-5"
              >
                {{ __(gruppo.label) }}
              </div>
              <div
                v-else
                class="mx-2 my-2 border-t border-outline-gray-2"
                aria-hidden="true"
              />
            </template>
            <nav
              class="flex flex-col gap-1"
              :class="{ 'mt-1': !gruppo.label && i > 0 }"
              :aria-label="gruppo.label ? __(gruppo.label) : undefined"
            >
              <SidebarItem
                v-for="link in gruppo.entries"
                :key="link.key"
                :to="{ name: link.key }"
                :label="__(link.label)"
                :active="activeItem === link.key"
                @click="selectItem($event, link.key)"
              >
                <template #prefix>
                  <Icon
                    :icon="ICONE[link.icon]"
                    class="size-4 text-ink-gray-7"
                  />
                </template>
                <Tooltip
                  :text="__(link.label)"
                  placement="right"
                  :hoverDelay="1.5"
                  :disabled="isCollapsed"
                >
                  <span class="truncate text-sm">{{ __(link.label) }}</span>
                </Tooltip>
              </SidebarItem>
            </nav>
          </template>

          <CollapsibleSection
            v-for="section in savedViews"
            :key="section.name"
            :label="section.name"
            :hideLabel="section.hideLabel"
            :opened="section.opened"
          >
            <template #header="{ opened, hide, toggle }">
              <SidebarLabel
                v-if="!hide"
                divider
                class="mb-1 mt-4 select-none"
                :class="!isCollapsed && 'cursor-pointer'"
                @click="toggle()"
              >
                <span class="flex items-center gap-1.5">
                  <span
                    class="lucide-chevron-right -ml-0.5 size-4 shrink-0 text-ink-gray-9 transition-transform duration-300 ease-in-out"
                    :class="{ 'rotate-90': opened }"
                    aria-hidden="true"
                  />
                  <span class="truncate">{{ __(section.name) }}</span>
                </span>
              </SidebarLabel>
            </template>
            <nav class="flex flex-col gap-1">
              <SidebarItem
                v-for="link in section.views"
                :key="link.key"
                :to="link.to"
                :label="__(link.label)"
                :active="activeItem === link.key"
                @click="selectItem($event, link.key)"
              >
                <template #prefix>
                  <Icon :icon="link.icon" class="size-4 text-ink-gray-7" />
                </template>
                <Tooltip
                  :text="__(link.label)"
                  placement="right"
                  :hoverDelay="1.5"
                  :disabled="isCollapsed"
                >
                  <span class="truncate text-sm">{{ __(link.label) }}</span>
                </Tooltip>
              </SidebarItem>
            </nav>
          </CollapsibleSection>
        </div>

        <!-- the settings, where one looks for them: not only in the menu under
             the name -->
        <div class="mt-auto flex flex-col gap-1 pt-2">
          <div class="mb-1 flex flex-col gap-2">
            <FirstStepsCard :collapsed="isCollapsed" />
          </div>
          <SidebarItem
            v-if="puo('dati_prova.gestisci') && isDemoDataCreated"
            :label="__('Clear Demo Data')"
            class="!text-ink-red-6 hover:!bg-surface-red-2"
            @click="() => clearDemoData()"
          >
            <template #prefix>
              <BrushCleaningIcon class="size-4" />
            </template>
          </SidebarItem>
          <SidebarItem :label="__('Settings')" @click="openSettings">
            <template #prefix>
              <LucideSettings class="size-4 text-ink-gray-7" />
            </template>
          </SidebarItem>
          <SidebarItem
            :label="isCollapsed ? __('Expand') : __('Collapse')"
            @click="isSidebarCollapsed = !isSidebarCollapsed"
          >
            <template #prefix>
              <CollapseSidebar
                class="size-4 text-ink-gray-7 duration-300 ease-in-out"
                :class="{ '[transform:rotateY(180deg)]': isCollapsed }"
              />
            </template>
          </SidebarItem>
        </div>
      </div>
    </Sidebar>
    <Notifications />
  </div>
</template>

<script setup>
import BrushCleaningIcon from '~icons/lucide/brush-cleaning'
import LucideSettings from '~icons/lucide/settings'
import CollapsibleSection from '@/components/CollapsibleSection.vue'
import Icon from '@/components/Icon.vue'
import UserDropdown from '@/components/UserDropdown.vue'
import FirstStepsCard from '@/components/FirstSteps/FirstStepsCard.vue'
import { callEnabled } from '@/composables/telephony'
import CollapseSidebar from '@/components/Icons/CollapseSidebar.vue'
import NotificationsIcon from '@/components/Icons/NotificationsIcon.vue'
import Notifications from '@/components/Notifications.vue'
import { currentNavKey } from '@/utils/navigation'
import { useVisteSalvate } from '@/composables/visteSalvate'
import {
  unreadNotificationsCount,
  notificationsStore,
} from '@/stores/notifications'
import { usersStore } from '@/stores/users'
import { menuDi } from '@/utils/menu'
import { ICONE_DEL_MENU } from '@/components/Icons/menu'
import { showSettings } from '@/composables/settings'
import { Sidebar, SidebarItem, SidebarLabel, Tooltip } from 'frappe-ui'
import { useStorage } from '@vueuse/core'
import { useDemoData } from '@/composables/demoData'
import { ref, computed, watch } from 'vue'
import { useRoute } from 'vue-router'

const route = useRoute()

const { toggle: toggleNotificationPanel } = notificationsStore()
const { clearDemoData, isDemoDataCreated } = useDemoData()
const { puo, puoUno, ambito } = usersStore()

const isSidebarCollapsed = useStorage('isSidebarCollapsed', false)

const isCollapsed = computed(() => isSidebarCollapsed.value)

// the menu one sees: the groups of the centre's work with what one may open
const menu = computed(() =>
  menuDi({ puo, puoUno, ambito, telefono: callEnabled.value }),
)

// the icon of each entry of the menu (utils/menu.js names them)
const ICONE = ICONE_DEL_MENU

function openSettings() {
  showSettings.value = true
}

// the views saved for everyone and the pinned ones, after the menu
const savedViews = useVisteSalvate()

// A saved view's key is its name; a plain nav item's key is its route name.
function currentRouteKey() {
  return currentNavKey(route)
}

// Set the highlight on click rather than waiting for the route, since route
// components are lazily imported and the first visit waits on a chunk fetch.
// Modified clicks open a new tab without navigating this one, so they must not
// move the highlight here.
const activeItem = ref(currentRouteKey())

function selectItem(event, key) {
  if (
    event.metaKey ||
    event.ctrlKey ||
    event.shiftKey ||
    event.altKey ||
    event.button === 1
  ) {
    return
  }
  activeItem.value = key
}

watch(
  () => [route.name, route.query.view, route.params.viewType],
  () => (activeItem.value = currentRouteKey()),
)
</script>
