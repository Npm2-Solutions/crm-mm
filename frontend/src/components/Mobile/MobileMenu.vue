<!--
  The phone's menu.

  It used to be the desktop sidebar squeezed into a 260px drawer: thirteen
  undifferentiated rows, two thirds of the screen left blank, and no way to
  reach Settings, notifications or the way out. On a phone the menu is not a
  leftover column — it is a screen, and the only screen that has to answer
  "where else can I go".

  So: the whole width, grouped by what you are doing, a filter for when the
  saved views pile up, and the account row where a phone expects it.
-->
<template>
  <TransitionRoot :show="open" as="template">
    <Dialog as="div" class="fixed inset-0 z-50" @close="close">
      <TransitionChild
        as="template"
        enter="transition-opacity ease-linear duration-200"
        enter-from="opacity-0"
        enter-to="opacity-100"
        leave="transition-opacity ease-linear duration-150"
        leave-from="opacity-100"
        leave-to="opacity-0"
      >
        <DialogOverlay class="fixed inset-0 bg-surface-gray-8/50" />
      </TransitionChild>

      <TransitionChild
        as="template"
        enter="transition ease-out duration-200 transform"
        enter-from="translate-y-full"
        enter-to="translate-y-0"
        leave="transition ease-in duration-150 transform"
        leave-from="translate-y-0"
        leave-to="translate-y-full"
      >
        <!-- Comes up from the bottom, because that is where the tab you pressed
             is. A drawer sliding in from the left would be arriving from a place
             you did not touch. -->
        <DialogPanel
          class="fixed inset-0 flex flex-col bg-surface-base px-safe pt-safe"
        >
          <div class="flex shrink-0 items-center gap-3 px-4 py-3">
            <BrandLogo v-model="brand" class="h-8 max-w-16 shrink-0" />
            <div class="min-w-0 flex-1">
              <div class="truncate text-base-medium text-ink-gray-9">
                {{ __(brand.name || 'CRM') }}
              </div>
              <div class="truncate text-p-sm text-ink-gray-5">
                {{ currentUser.full_name || currentUser.name }}
              </div>
            </div>
            <Button
              variant="ghost"
              icon="x"
              size="md"
              :aria-label="__('Close')"
              @click="close"
            />
          </div>

          <div class="shrink-0 px-4 pb-3">
            <TextInput
              v-model="filter"
              type="text"
              :placeholder="__('Search a screen')"
            >
              <template #prefix>
                <LucideSearch class="size-4 text-ink-gray-4" />
              </template>
            </TextInput>
          </div>

          <div class="min-h-0 flex-1 overflow-y-auto px-2 pb-2">
            <section v-for="group in groups" :key="group.key" class="mb-3">
              <h2
                class="px-2 pb-1 pt-2 text-p-xs uppercase tracking-wide text-ink-gray-5"
              >
                {{ __(group.label) }}
              </h2>
              <MobileMenuRow
                v-for="item in group.links"
                :key="item.key"
                :icon="item.icon"
                :label="__(item.label)"
                :active="activeKey === item.key"
                @click="go(item.to)"
              />
            </section>

            <section v-if="savedViews.length" class="mb-3">
              <h2
                class="px-2 pb-1 pt-2 text-p-xs uppercase tracking-wide text-ink-gray-5"
              >
                {{ __('Saved views') }}
              </h2>
              <MobileMenuRow
                v-for="item in savedViews"
                :key="item.key"
                :icon="item.icon"
                :label="item.label"
                :active="activeKey === item.key"
                @click="go(item.to)"
              />
            </section>

            <section v-if="!groups.length && !savedViews.length" class="p-6">
              <p class="text-center text-p-sm text-ink-gray-4">
                {{ __('Nothing matches that.') }}
              </p>
            </section>
          </div>

          <div
            class="shrink-0 border-t border-outline-gray-1 px-2 pb-2 pt-1.5 [padding-bottom:calc(0.5rem+env(safe-area-inset-bottom))]"
          >
            <div class="grid grid-cols-2 gap-1">
              <MobileMenuRow
                :icon="NotificationsIcon"
                :label="__('Notifications')"
                :badge="unreadNotificationsCount"
                @click="go({ name: 'Notifications' })"
              />
              <MobileMenuRow
                :icon="SettingsIcon"
                :label="__('Settings')"
                @click="openSettings"
              />
              <MobileMenuRow
                :icon="HelpIcon"
                :label="__('Help')"
                @click="openHelp"
              />
              <MobileMenuRow
                :icon="LucideLogOut"
                :label="__('Log out')"
                danger
                @click="logout.submit()"
              />
            </div>
          </div>
        </DialogPanel>
      </TransitionChild>
    </Dialog>
  </TransitionRoot>
</template>

<script setup>
import LucideSearch from '~icons/lucide/search'
import LucideLogOut from '~icons/lucide/log-out'
import BrandLogo from '@/components/BrandLogo.vue'
import HelpIcon from '@/components/Icons/HelpIcon.vue'
import NotificationsIcon from '@/components/Icons/NotificationsIcon.vue'
import SettingsIcon from '@/components/Icons/SettingsIcon.vue'
import MobileMenuRow from '@/components/Mobile/MobileMenuRow.vue'
import { groupedLinks } from '@/composables/appLinks'
import {
  mobileSidebarOpened as open,
  showSettings,
} from '@/composables/settings'
import { unreadNotificationsCount } from '@/stores/notifications'
import { sessionStore } from '@/stores/session'
import { getSettings } from '@/stores/settings'
import { usersStore } from '@/stores/users'
import { viewsStore } from '@/stores/views'
import { currentNavKey } from '@/utils/navigation'
import {
  Dialog,
  DialogOverlay,
  DialogPanel,
  TransitionChild,
  TransitionRoot,
} from '@headlessui/vue'
import { TextInput } from 'frappe-ui'
import { showHelpModal, minimize } from 'frappe-ui/frappe'
import { computed, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'

const route = useRoute()
const router = useRouter()
const { brand } = getSettings()
const { logout } = sessionStore()
const { getUser } = usersStore()
const { getPinnedViews, getPublicViews } = viewsStore()

const filter = ref('')
const currentUser = computed(() => getUser() || {})
const activeKey = computed(() => currentNavKey(route))

function matches(label) {
  const q = filter.value.trim().toLowerCase()
  return !q || String(label).toLowerCase().includes(q)
}

const groups = computed(() =>
  groupedLinks()
    .map((group) => ({
      ...group,
      links: group.links
        .filter((link) => matches(__(link.label)))
        .map((link) => ({ ...link, key: link.to, to: { name: link.to } })),
    }))
    .filter((group) => group.links.length),
)

const savedViews = computed(() =>
  [...getPublicViews(), ...getPinnedViews()]
    .filter((view) => matches(view.label))
    .map((view) => ({
      key: view.name,
      label: view.label,
      icon: view.icon,
      to: {
        name: view.route_name,
        params: { viewType: view.type || 'list' },
        query: { view: view.name },
      },
    })),
)

function close() {
  open.value = false
}

function go(to) {
  close()
  router.push(to)
}

function openSettings() {
  close()
  showSettings.value = true
}

function openHelp() {
  close()
  showHelpModal.value = true
  minimize.value = false
}

// Leaving the menu open behind a route change would have it reappear on the
// next screen; the filter should not survive either.
watch(open, (isOpen) => {
  if (isOpen) filter.value = ''
})
</script>
