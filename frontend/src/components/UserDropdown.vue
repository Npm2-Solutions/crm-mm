<!--
  Modifications copyright (c) 2026, NPM2 Solutions Srl

  The account's menu heading the sidebar: its entries are the centre's
  (composables/vociAccount.js), the phone draws the same as rows (pages/Altro.vue).
-->
<template>
  <Dropdown :options="dropdownItems" v-bind="$attrs">
    <template #default="{ open }">
      <button
        class="flex items-center rounded-md duration-300 ease-in-out"
        :class="[
          isCollapsed ? 'h-12 w-auto px-0' : 'min-h-12 w-full px-2 py-2',
          !isCollapsed &&
            (open
              ? 'bg-surface-elevation-3 shadow-sm'
              : 'hover:bg-surface-gray-2'),
        ]"
        :aria-label="platform.name"
      >
        <!-- the product's logo heads the sidebar (design system Espresso): on its
             own row, the user under it; collapsed, its icon. The centre's mark
             leads where people deal with the centre: the public pages, the area -->
        <div
          v-if="!isCollapsed"
          class="flex min-w-0 flex-1 flex-col items-start gap-1.5 text-left"
        >
          <img
            :src="platform.logo"
            :alt="platform.name"
            class="h-5 w-auto shrink-0 dark:hidden"
          />
          <img
            :src="platform.logo_dark"
            :alt="platform.name"
            class="hidden h-5 w-auto shrink-0 dark:block"
          />
          <div class="w-full truncate text-sm leading-none text-ink-gray-6">
            {{ user.full_name }}
          </div>
        </div>
        <CRMLogo v-else class="size-8 shrink-0 rounded-md" />
        <div
          class="duration-300 ease-in-out"
          :class="
            isCollapsed
              ? 'ml-0 w-0 overflow-hidden opacity-0'
              : 'ml-2 w-auto opacity-100'
          "
        >
          <span
            class="lucide-chevron-down size-4 text-ink-gray-5"
            aria-hidden="true"
          />
        </div>
      </button>
    </template>
  </Dropdown>
</template>

<script setup>
import CRMLogo from '@/components/Icons/CRMLogo.vue'
import AppsIcon from '@/components/Icons/AppsIcon.vue'
import { useVociAccount } from '@/composables/vociAccount'
import { usersStore } from '@/stores/users'
import { marchio } from '@/utils/marchio'
import { Dropdown } from 'frappe-ui'
import { computed, h, markRaw } from 'vue'

defineProps({
  isCollapsed: { type: Boolean, default: false },
})

// the product's brand heads the sidebar; the centre's mark leads on the pages
// its people open (crm.marchio)
const platform = marchio()
const { getUser } = usersStore()
const { gruppi, apps } = useVociAccount()

const user = computed(() => getUser() || {})

// the account's menu (composables/vociAccount.js) as the dropdown's groups
const dropdownItems = computed(() =>
  gruppi.value.map((gruppo, i) => ({
    group: i ? '' : 'Dropdown Items',
    hideLabel: true,
    items: gruppo.map((voce) =>
      voce.tipo === 'app'
        ? {
            icon: markRaw(AppsIcon),
            label: voce.etichetta,
            submenu: appMenuItems(),
          }
        : { icon: voce.icona, label: voce.etichetta, onClick: voce.azione },
    ),
  })),
)

function appMenuItems() {
  return (apps.data || []).map((app) => ({
    label: app.title,
    onClick: () => (window.location.href = app.route),
    slots: {
      prefix: () =>
        app.icon
          ? h(app.icon, { class: 'size-5 text-ink-gray-7' })
          : h('img', { class: 'size-5 rounded', src: app.logo }),
    },
  }))
}
</script>
