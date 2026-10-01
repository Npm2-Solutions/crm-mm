<!--
  The client area's shell: the centre's mark at the top - its logo as it is
  drawn, wide on its own or square beside its name - and the product's signature
  at the foot (crm.marchio), whose area it is (a parent sees their child's too),
  and its places at the bottom, within reach of a thumb.
  Staff who open it are sent to DottorCloud: the area is for the centre's clients.
  With the clinic on it is the patient area, and says so (window.AREA.words).
-->
<template>
  <div v-if="staff" class="grid h-full place-items-center px-4">
    <div class="flex max-w-sm flex-col items-center gap-3 text-center">
      <p class="text-base text-ink-gray-8">
        {{ __("This area is for the centre's clients.") }}
      </p>
      <p class="text-p-sm text-ink-gray-5">
        {{ __('Your work is in {brand}.') }}
      </p>
      <Button variant="solid" :label="__('Open {brand}')" @click="goCrm" />
    </div>
  </div>
  <router-view v-else-if="route.name === 'Login'" />
  <div v-else class="flex h-full flex-col">
    <header
      class="flex items-center justify-between gap-3 border-b border-outline-gray-1 bg-surface-base px-4 py-3"
    >
      <div class="flex min-w-0 items-center gap-2.5">
        <img
          v-if="logo && forma === 'wide'"
          :src="logo"
          :alt="centre || ''"
          class="h-8 min-w-0 max-w-full object-contain object-left dark:rounded dark:bg-white dark:px-1.5 dark:py-1"
        />
        <template v-else>
          <CentreTile
            v-if="logo"
            :logo="logo"
            :forma="forma"
            :nome="centre"
            class="size-8"
          />
          <span
            v-if="centre"
            class="min-w-0 truncate text-base font-semibold text-ink-gray-9"
          >
            {{ centre }}
          </span>
          <template v-else-if="!logo">
            <img
              :src="brand.logo"
              :alt="brand.name"
              class="h-6 w-auto shrink-0 dark:hidden"
            />
            <img
              :src="brand.logo_dark"
              :alt="brand.name"
              class="hidden h-6 w-auto shrink-0 dark:block"
            />
          </template>
        </template>
      </div>
      <Button
        variant="ghost"
        :label="__('Log out')"
        class="shrink-0"
        @click="logout"
      />
    </header>
    <div
      v-if="(area.me?.people || []).length > 1"
      class="border-b border-outline-gray-1 bg-surface-elevation-1 px-4 py-2"
    >
      <FormControl
        type="select"
        :label="__('Whose area')"
        :model-value="area.person"
        :options="
          area.me.people.map((p) => ({ label: p.lead_name, value: p.name }))
        "
        @update:model-value="choose"
      />
    </div>
    <main class="min-h-0 flex-1 overflow-y-auto">
      <div class="mx-auto w-full max-w-2xl px-4 py-5">
        <ErrorMessage v-if="area.error" :message="area.error" />
        <router-view v-else-if="area.person" :key="area.person" />
        <!-- the product signs at the foot: the centre leads at the top (where
             it has neither a logo nor a name, the product is up there already) -->
        <p
          v-if="logo || centre"
          class="mt-10 flex items-center justify-center gap-1.5 text-xs text-ink-gray-5"
        >
          <img :src="brand.icon" alt="" class="size-4 rounded-[4px]" />
          {{ __('Powered by {brand}') }}
        </p>
      </div>
    </main>
    <nav
      class="pb-safe grid border-t border-outline-gray-1 bg-surface-elevation-1"
      :style="{
        gridTemplateColumns: `repeat(${places.length}, minmax(0, 1fr))`,
      }"
    >
      <router-link
        v-for="place in places"
        :key="place.name"
        :to="{ name: place.name }"
        class="flex min-w-0 flex-col items-center gap-1 py-2 text-[11px] leading-tight"
        :class="
          placeOf(route.name) === place.name
            ? 'text-ink-gray-9 font-medium'
            : 'text-ink-gray-5'
        "
      >
        <span class="relative">
          <FeatherIcon :name="place.icon" class="size-5" />
          <span
            v-if="place.name === 'Messages' && unread"
            class="absolute -right-2 -top-1 grid min-w-4 place-items-center rounded-full bg-surface-red-5 px-1 text-[10px] font-medium leading-4 text-ink-base"
          >
            {{ unread }}
          </span>
        </span>
        <span class="max-w-full truncate">{{ place.label }}</span>
      </router-link>
    </nav>
  </div>
</template>

<script setup>
import { Button, ErrorMessage, FeatherIcon, FormControl } from 'frappe-ui'
import { computed } from 'vue'
import { useRoute } from 'vue-router'
import { area, choose, loadMe, logout, section } from './store'
import CentreTile from '@/components/CentreTile.vue'
import { useFormaDelLogo } from '@/composables/formaDelLogo'
import { marchio } from '@/utils/marchio'

const route = useRoute()
const boot = window.AREA || {}
const staff = Boolean(boot.staff)
const centre = boot.centre
// the centre's logo leads: wide on its own, square beside its name
const logo = boot.logo
const forma = useFormaDelLogo(logo, boot.logo_shape)
const brand = marchio(boot.brand)

const current = computed(() =>
  (area.me?.people || []).find((p) => p.name === area.person),
)

// the places other modules add, where they have something: "Plans" only for
// whoever follows one - a plan, a programme, a quote - most people never do;
// the documents to who was given some
const places = computed(() =>
  [
    { name: 'Home', label: __('Home'), icon: 'home' },
    { name: 'Appointments', label: __('Agenda'), icon: 'calendar' },
    area.person && (section('plans') || section('quotes'))
      ? { name: 'Plans', label: __('Plans'), icon: 'check-square' }
      : null,
    { name: 'Messages', label: __('Messages'), icon: 'message-square' },
    area.person && section('documents')
      ? { name: 'Documents', label: __('Documents'), icon: 'file-text' }
      : null,
    { name: 'Invoices', label: __('Invoices'), icon: 'credit-card' },
  ].filter(Boolean),
)

// a plan's own page lights its place in the bar
const placeOf = (name) => (name === 'Plan' ? 'Plans' : name)

// what the centre wrote and the person has not opened yet
const unread = computed(() => current.value?.unread || 0)

if (!staff && boot.user && boot.user !== 'Guest') loadMe()

function goCrm() {
  window.location.href = '/crm'
}
</script>
