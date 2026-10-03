<!--
  The client area's shell, as the brand draws the patient's phone: the centre's
  mark at the top - its logo as it is drawn, wide on its own or square beside its
  name - and the product's signature at the foot (crm.marchio), whose area it is
  (a parent sees their child's too), and its places at the bottom, within reach
  of a thumb, the open one in the brand's colour.
  Staff who open it are sent to DottorCloud: the area is for the centre's clients,
  but for the preview a person's page opens (crm.area.anteprima), read only.
  With the clinic on it is the patient area, and says so (window.AREA.words).
-->
<template>
  <div v-if="staff && !anteprima" class="grid h-full place-items-center px-4">
    <div class="flex max-w-sm flex-col items-center gap-3 text-center">
      <p class="text-base text-ink-gray-8">
        {{ __("This area is for the centre's clients.") }}
      </p>
      <p class="text-p-sm text-ink-gray-5">
        {{ __('Your work is in {brand}.') }}
      </p>
      <Button
        variant="solid"
        size="lg"
        :label="__('Open {brand}')"
        @click="goCrm"
      />
    </div>
  </div>
  <router-view v-else-if="route.name === 'Login'" />
  <div v-else class="flex h-full flex-col">
    <header class="flex items-center justify-between gap-3 px-5 pb-1 pt-4">
      <div class="flex min-w-0 items-center gap-2.5">
        <img
          v-if="logo && forma === 'wide'"
          :src="logo"
          :alt="centre || ''"
          class="h-8 min-w-0 max-w-full object-contain object-left"
        />
        <template v-else>
          <CentreTile
            v-if="logo || centre"
            :logo="logo"
            :forma="forma"
            :nome="centre"
            class="size-8"
          />
          <span
            v-if="centre"
            class="min-w-0 truncate text-[15px] font-bold text-ink-gray-9"
          >
            {{ centre }}
          </span>
          <img
            v-else-if="!logo"
            :src="brand.logo"
            :alt="brand.name"
            class="h-6 w-auto shrink-0"
          />
        </template>
      </div>
      <Button
        v-if="anteprima"
        variant="solid"
        :label="__('Close the preview')"
        class="shrink-0"
        @click="chiudi"
      />
      <Button
        v-else
        variant="ghost"
        :label="__('Log out')"
        class="shrink-0"
        @click="logout"
      />
    </header>
    <p
      v-if="anteprima"
      class="mx-5 mt-2 rounded-[12px_12px_12px_2px] bg-[var(--warning-subtle)] px-3 py-2 text-p-sm text-[var(--warning)]"
      role="status"
    >
      {{
        __(
          'Preview: this is the area of {0} as they see it. Nothing is changed or sent from here.',
          [anteprima.lead_name],
        )
      }}
    </p>
    <div v-if="(area.me?.people || []).length > 1" class="px-5 pt-2">
      <FormControl
        type="select"
        size="md"
        :label="__('Whose area')"
        :model-value="area.person"
        :options="
          area.me.people.map((p) => ({ label: p.lead_name, value: p.name }))
        "
        @update:model-value="choose"
      />
    </div>
    <main class="min-h-0 flex-1 overflow-y-auto">
      <div class="mx-auto w-full max-w-2xl px-5 pb-6 pt-3">
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
      class="area-nav pb-safe grid border-t border-outline-gray-1 bg-surface-elevation-1"
      :style="{
        gridTemplateColumns: `repeat(${places.length}, minmax(0, 1fr))`,
      }"
    >
      <router-link
        v-for="place in places"
        :key="place.name"
        :to="{ name: place.name }"
        class="flex min-w-0 flex-col items-center gap-1 pb-2 pt-2.5 text-[11px] font-semibold leading-tight tracking-[0.02em]"
        :class="{ 'is-on': placeOf(route.name) === place.name }"
      >
        <span class="relative">
          <component :is="place.icon" class="size-[22px]" aria-hidden="true" />
          <span
            v-if="place.name === 'Messages' && unread"
            class="absolute -right-2 -top-1 grid min-w-4 place-items-center rounded-full bg-[var(--danger)] px-1 text-[10px] font-semibold leading-4 text-white"
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
import { Button, ErrorMessage, FormControl } from 'frappe-ui'
import { computed, onBeforeUnmount, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import LucideCalendar from '~icons/lucide/calendar'
import LucideFileText from '~icons/lucide/file-text'
import LucideHouse from '~icons/lucide/house'
import LucideListChecks from '~icons/lucide/list-checks'
import LucideMessageCircle from '~icons/lucide/message-circle'
import { anteprima, chiudi } from './anteprima'
import { area, choose, loadMe, logout, section } from './store'
import CentreTile from '@/components/CentreTile.vue'
import { useFormaDelLogo } from '@/composables/formaDelLogo'
import { marchio } from '@/utils/marchio'
import { seguiLaTastiera } from '@/utils/tastieraAperta'

// the keyboard covers the bottom of the phone without making the page any
// shorter: while the person writes (the chat, a code), the area follows what
// one sees, the places at the bottom step aside (area.css); a pressed place
// shows it, where iPhone listens to a touch
let smettiDiSeguire = () => {}
function alTocco() {}
onMounted(() => {
  smettiDiSeguire = seguiLaTastiera()
  document.addEventListener('touchstart', alTocco, { passive: true })
})
onBeforeUnmount(() => {
  smettiDiSeguire()
  document.removeEventListener('touchstart', alTocco)
})

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

// the places, as the brand's phone has them: today, the agenda, the plans -
// only for whoever follows one: a plan, a programme, a quote, most people never
// do - the documents with the invoices, the messages
const places = computed(() =>
  [
    { name: 'Home', label: __('Today'), icon: LucideHouse },
    { name: 'Appointments', label: __('Agenda'), icon: LucideCalendar },
    area.person && (section('plans') || section('quotes'))
      ? { name: 'Plans', label: __('Plans'), icon: LucideListChecks }
      : null,
    { name: 'Documents', label: __('Documents'), icon: LucideFileText },
    { name: 'Messages', label: __('Messages'), icon: LucideMessageCircle },
  ].filter(Boolean),
)

// a page of a place lights it in the bar
const placeOf = (name) =>
  ({ Plan: 'Plans', PlanShopping: 'Plans', Chat: 'Messages' })[name] || name

// what the centre wrote and the person has not opened yet
const unread = computed(() => current.value?.unread || 0)

// a client, or the centre previewing a person's area
if ((!staff || anteprima) && boot.user && boot.user !== 'Guest') loadMe()

function goCrm() {
  window.location.href = '/crm'
}
</script>
