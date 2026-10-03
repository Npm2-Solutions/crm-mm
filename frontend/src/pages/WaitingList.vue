<!--
  Copyright (c) 2026, NPM2 Solutions Srl and contributors
  For license information, please see license.txt

  Who waits, in the line's order: the urgent first, then who joined first. Each
  says what they wait for, when they can, and how the place offered to them
  stands - waiting for an answer, or not sent because there is nothing to send
  it to, and the desk calls. Opened, an entry finds the free places and offers
  or books one; the closed ones stay a while to look back.
-->
<template>
  <LayoutHeader>
    <template #left-header>
      <ViewBreadcrumbs routeName="Waiting List" label="Waiting list" />
    </template>
    <template #right-header>
      <TabButtons
        v-model="closed"
        :buttons="[
          { label: __('In the line'), value: 0 },
          { label: __('Closed'), value: 1 },
        ]"
      />
    </template>
  </LayoutHeader>
  <div class="flex-1 overflow-y-auto">
    <div class="mx-auto flex max-w-4xl flex-col gap-6 px-5 py-6 max-md:px-4">
      <div class="flex flex-wrap items-center gap-2">
        <div class="w-60 max-md:w-full">
          <FormControl
            v-model="service"
            type="select"
            :aria-label="__('Service')"
            :options="serviceOptions"
          />
        </div>
        <div class="w-52 max-md:w-full">
          <FormControl
            v-model="staff"
            type="select"
            :aria-label="__('With')"
            :options="staffOptions"
          />
        </div>
      </div>

      <!-- how the line stands, at a glance: the design system's tiles, on a
           phone one short row; who is to be called, when there is somebody,
           in red -->
      <div v-if="!closed" class="dc-stat-row grid grid-cols-3 gap-3">
        <StatTile
          v-for="(stat, i) in stats"
          :key="stat.label"
          :label="__(stat.label)"
          :blocco="i === 0"
        >
          <span :class="{ 'text-ink-red-6': stat.alert && stat.value }">
            {{ stat.value }}
          </span>
        </StatTile>
      </div>

      <div
        v-if="list.loading && !list.data"
        class="flex justify-center py-10 text-ink-gray-5"
      >
        <LoadingIndicator class="size-4" />
      </div>
      <!-- the design system's empty list, as every other one -->
      <EmptyState
        v-else-if="!entries.length && closed"
        :title="__('Nobody has left the line yet')"
      />
      <EmptyState
        v-else-if="!entries.length"
        :title="__('Nobody is waiting')"
        :text="
          __(
            'From a person’s page, put them on the list when there is no place: what frees up goes to them.',
          )
        "
      />
      <ol
        v-else
        class="divide-y divide-outline-gray-1 rounded-lg border border-outline-gray-2"
      >
        <li v-for="entry in entries" :key="entry.name" class="flex">
          <button
            type="button"
            class="flex min-w-0 flex-1 flex-col gap-0.5 px-4 py-3 text-left hover:bg-surface-gray-1 focus-visible:bg-surface-gray-1 focus-visible:outline-none"
            @click="open(entry)"
          >
            <span class="flex items-center justify-between gap-2">
              <span
                class="flex min-w-0 items-center gap-2 text-base font-medium text-ink-gray-9"
              >
                <span class="truncate">{{ entry.lead_name }}</span>
                <Badge
                  v-if="entry.urgent && !closed"
                  class="shrink-0"
                  variant="subtle"
                  theme="red"
                  :label="__('Urgent')"
                />
              </span>
              <Badge
                class="shrink-0"
                variant="subtle"
                :theme="STATO[entry.status]?.theme || 'gray'"
                :label="__(STATO[entry.status]?.label || entry.status)"
              />
            </span>
            <span class="text-p-sm text-ink-gray-7">
              {{ entry.service_name
              }}<template v-if="entry.staff_name">
                · {{ entry.staff_name }}</template
              >
            </span>
            <span class="text-p-sm text-ink-gray-5">
              {{ whenLine(entry) }}
            </span>
            <span
              v-if="entry.offer"
              class="text-p-sm"
              :class="
                entry.offer.channel ? 'text-ink-gray-6' : 'text-ink-red-7'
              "
            >
              {{ offerLine(entry.offer) }}
            </span>
          </button>
          <RouterLink
            :to="{ name: 'Lead', params: { leadId: entry.lead } }"
            class="flex shrink-0 items-center px-3 text-ink-gray-5 hover:text-ink-gray-8 focus-visible:text-ink-gray-8 focus-visible:outline-none"
            :aria-label="__('Open {0}', [entry.lead_name])"
            :title="__('Open {0}', [entry.lead_name])"
          >
            <span class="lucide-user size-4" aria-hidden="true" />
          </RouterLink>
        </li>
      </ol>
    </div>
  </div>
  <WaitingDialog
    v-if="dialog.lead"
    v-model="dialog.show"
    :lead="dialog.lead"
    :name="dialog.name"
    @changed="list.reload()"
  />
</template>

<script setup>
import EmptyState from '@/components/Espresso/EmptyState.vue'
import StatTile from '@/components/Espresso/StatTile.vue'
import LayoutHeader from '@/components/LayoutHeader.vue'
import ViewBreadcrumbs from '@/components/ViewBreadcrumbs.vue'
import LoadingIndicator from '@/components/Icons/LoadingIndicator.vue'
import WaitingDialog from '@/components/Waiting/WaitingDialog.vue'
import { useSchedulerMeta } from '@/composables/scheduling'
import { formatDate } from '@/utils'
import { STATO, comeStaLOfferta, quandoPuo } from '@/utils/attese'
import { appLocale } from '@/utils/locale'
import {
  Badge,
  FormControl,
  TabButtons,
  createResource,
  usePageMeta,
} from 'frappe-ui'
import { computed, reactive, ref, watch } from 'vue'

const meta = useSchedulerMeta()
const t = (text, args) => __(text, args)
const locale = appLocale()

const closed = ref(0)
const service = ref('')
const staff = ref('')

const list = createResource({
  url: 'crm.scheduling.attese.get_waiting_list',
  makeParams: () => ({
    service: service.value || null,
    staff: staff.value || null,
    closed: closed.value,
  }),
  auto: true,
})
watch([closed, service, staff], () => list.reload())

const entries = computed(() => list.data?.entries || [])

const serviceOptions = computed(() => [
  { label: __('Every service'), value: '' },
  ...(meta.data?.services || []).map((one) => ({
    label: one.service_name,
    value: one.name,
  })),
])

const staffOptions = computed(() => [
  { label: __('Every professional'), value: '' },
  ...(meta.data?.staff || []).map((one) => ({
    label: one.full_name,
    value: one.name,
  })),
])

const stats = computed(() => [
  {
    label: 'Waiting',
    value: entries.value.filter((entry) => entry.status === 'Waiting').length,
  },
  {
    label: 'Offers to answer',
    value: entries.value.filter((entry) => entry.offer?.channel).length,
  },
  {
    label: 'To call',
    value: entries.value.filter((entry) => entry.offer && !entry.offer.channel)
      .length,
    alert: true,
  },
])

function whenLine(entry) {
  const parts = [
    entry.class_session
      ? __('A seat in the class of {0}', [
          formatDate(entry.class_starts_on, 'ddd D MMM, HH:mm'),
        ])
      : quandoPuo(entry, t, locale),
  ]
  if (entry.until)
    parts.push(__('until {0}', [formatDate(entry.until, 'D MMM')]))
  parts.push(__('since {0}', [formatDate(entry.since, 'D MMM')]))
  return parts.join(' · ')
}

function offerLine(offer) {
  return `${formatDate(offer.starts_on, 'ddd D MMM, HH:mm')} · ${comeStaLOfferta(
    offer,
    t,
    (value) => formatDate(value, 'HH:mm'),
  )}`
}

const dialog = reactive({ show: false, lead: '', name: null })

function open(entry) {
  Object.assign(dialog, { show: true, lead: entry.lead, name: entry.name })
}

usePageMeta(() => ({ title: __('Waiting list') }))
</script>
