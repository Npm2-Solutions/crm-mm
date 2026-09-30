<!--
  The patient area's shell: the centre's name, whose area it is (a parent sees
  their child's too), and four places at the bottom, within reach of a thumb.
  Staff who open it are sent to the CRM: the area is for patients.
-->
<template>
  <div v-if="staff" class="grid h-full place-items-center px-4">
    <div class="flex max-w-sm flex-col items-center gap-3 text-center">
      <p class="text-base text-ink-gray-8">
        {{ __('This area is for the patients of the centre.') }}
      </p>
      <p class="text-p-sm text-ink-gray-5">
        {{ __('Your work is in the CRM.') }}
      </p>
      <Button variant="solid" :label="__('Open the CRM')" @click="goCrm" />
    </div>
  </div>
  <router-view v-else-if="route.name === 'Login'" />
  <div v-else class="flex h-full flex-col">
    <header
      class="flex items-center justify-between gap-3 border-b border-outline-gray-1 bg-surface-white px-4 py-3"
    >
      <div class="flex min-w-0 items-center gap-2">
        <img v-if="logo" :src="logo" alt="" class="max-h-7 max-w-[7rem]" />
        <span class="truncate text-base font-semibold text-ink-gray-9">
          {{ centre || __('Your area') }}
        </span>
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
      class="border-b border-outline-gray-1 bg-surface-white px-4 py-2"
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
      </div>
    </main>
    <nav
      class="pb-safe grid grid-cols-4 border-t border-outline-gray-1 bg-surface-white"
    >
      <router-link
        v-for="place in places"
        :key="place.name"
        :to="{ name: place.name }"
        class="flex flex-col items-center gap-1 py-2 text-xs"
        :class="
          route.name === place.name
            ? 'text-ink-gray-9 font-medium'
            : 'text-ink-gray-5'
        "
      >
        <FeatherIcon :name="place.icon" class="size-5" />
        {{ place.label }}
      </router-link>
    </nav>
  </div>
</template>

<script setup>
import { Button, ErrorMessage, FeatherIcon, FormControl } from 'frappe-ui'
import { useRoute } from 'vue-router'
import { area, choose, loadMe, logout } from './store'

const route = useRoute()
const boot = window.AREA || {}
const staff = Boolean(boot.staff)
const centre = boot.centre
const logo = boot.logo

const places = [
  { name: 'Home', label: __('Home'), icon: 'home' },
  { name: 'Appointments', label: __('Appointments'), icon: 'calendar' },
  { name: 'Documents', label: __('Documents'), icon: 'file-text' },
  { name: 'Invoices', label: __('Invoices'), icon: 'credit-card' },
]

if (!staff && boot.user && boot.user !== 'Guest') loadMe()

function goCrm() {
  window.location.href = '/crm'
}
</script>
