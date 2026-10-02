<template>
  <MobileNav>
    <MobileNavItem
      v-for="tab in tabs"
      :key="tab.key"
      :to="tab.to"
      :label="__(tab.label)"
      :icon="tab.icon"
      :active="activeTab === tab.key"
    />
    <!-- the notifications are behind "More": a dot says something is new -->
    <MobileNavItem
      :label="__('More')"
      :active="mobileSidebarOpened"
      @click="mobileSidebarOpened = true"
    >
      <template #default="{ active }">
        <span class="relative">
          <MenuIcon
            class="size-6"
            :class="active ? 'text-ink-gray-8' : 'text-ink-gray-5'"
            aria-hidden="true"
          />
          <span
            v-if="unreadNotificationsCount"
            class="absolute -right-0.5 -top-0.5 size-2 rounded-full bg-[var(--brand-segno)] ring-2 ring-[var(--surface-base)]"
            :aria-label="__('Unread notifications')"
          />
        </span>
      </template>
    </MobileNavItem>
  </MobileNav>
</template>

<script setup>
import { ICONE_DEL_MENU } from '@/components/Icons/menu'
import MenuIcon from '@/components/Icons/MenuIcon.vue'
import { mobileSidebarOpened } from '@/composables/settings'
import { unreadNotificationsCount } from '@/stores/notifications'
import { callEnabled } from '@/composables/telephony'
import { usersStore } from '@/stores/users'
import { barraDelTelefono, menuDi } from '@/utils/menu'
import { bottomNavTabFor } from '@/utils/navigation'
import { MobileNav, MobileNavItem } from 'frappe-ui'
import { computed } from 'vue'
import { useRoute } from 'vue-router'

const route = useRoute()
const { puo, puoUno, ambito } = usersStore()

// The four places a phone opens all day, from the same menu as the sidebar
// (utils/menu.js): the day's pages, the people, the conversations. Everything
// else stays one tap away behind "More", which is the drawer.
const tabs = computed(() =>
  barraDelTelefono(
    menuDi({ puo, puoUno, ambito, telefono: callEnabled.value }),
  ).map((voce) => ({
    key: voce.key,
    // a word that fits under an icon a fifth of a phone wide
    label: voce.key === 'Conversations' ? 'Chat' : voce.label,
    icon: ICONE_DEL_MENU[voce.icon],
    to: { name: voce.key },
  })),
)

// `MobileNavItem` lights itself up on an exact route match, which leaves a tab
// dark the moment you open a record inside its section.
const activeTab = computed(() =>
  bottomNavTabFor(
    route,
    tabs.value.map((tab) => tab.key),
  ),
)
</script>
