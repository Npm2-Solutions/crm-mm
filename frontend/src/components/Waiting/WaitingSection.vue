<!--
  Copyright (c) 2026, NPM2 Solutions Srl and contributors
  For license information, please see license.txt
-->
<template>
  <!-- What the person waits for: a service on some days, a seat in a full
       class. Put on the list here; a place that frees up is offered by itself,
       or the desk looks for one and offers it or books it. -->
  <div v-if="entries.data" class="flex flex-col">
    <div class="h-px w-full border-t" />
    <div class="p-1 sm:p-3">
      <CollapsibleSection
        labelClass="px-2 font-semibold"
        headerClass="h-8"
        :label="__('Waiting list')"
        :count="waiting || ''"
      >
        <template #actions>
          <Button
            v-if="entries.data.can_manage"
            variant="ghost"
            class="touch-target"
            icon="plus"
            :aria-label="__('Put on the waiting list')"
            :title="__('Put on the waiting list')"
            @click="open(null)"
          />
        </template>
        <div class="flex flex-col gap-0.5 pb-1 pt-2">
          <button
            v-for="entry in entries.data.entries"
            :key="entry.name"
            type="button"
            class="flex flex-col gap-1 rounded px-3 py-1.5 text-left hover:bg-surface-gray-2 focus-visible:bg-surface-gray-2 focus-visible:outline-none"
            @click="open(entry.name)"
          >
            <span class="flex items-center justify-between gap-2">
              <span class="min-w-0 truncate text-base text-ink-gray-8">
                {{ entry.service_name }}
              </span>
              <Badge
                class="shrink-0"
                variant="subtle"
                :theme="STATO[entry.status]?.theme || 'gray'"
                :label="__(STATO[entry.status]?.label || entry.status)"
              />
            </span>
            <span class="text-p-sm text-ink-gray-6">
              {{ line(entry) }}
            </span>
            <span
              v-if="entry.offer"
              class="text-p-sm"
              :class="
                entry.offer.channel ? 'text-ink-gray-5' : 'text-ink-red-7'
              "
            >
              {{ offerLine(entry.offer) }}
            </span>
          </button>
          <div
            v-if="!entries.data.entries.length"
            class="px-3 py-1 text-p-sm text-ink-gray-5"
          >
            {{
              __(
                'Nobody waits: when there is no place, put them on the list and the place that frees up goes to them.',
              )
            }}
          </div>
        </div>
      </CollapsibleSection>
    </div>
  </div>
  <WaitingDialog
    v-model="dialog.show"
    :lead="lead"
    :name="dialog.name"
    @changed="entries.reload()"
  />
</template>

<script setup>
import CollapsibleSection from '@/components/CollapsibleSection.vue'
import WaitingDialog from '@/components/Waiting/WaitingDialog.vue'
import { usersStore } from '@/stores/users'
import { formatDate } from '@/utils'
import { APERTE, STATO, comeStaLOfferta, quandoPuo } from '@/utils/attese'
import { appLocale } from '@/utils/locale'
import { Badge, Button, createResource } from 'frappe-ui'
import { computed, reactive, watch } from 'vue'

const props = defineProps({
  lead: { type: String, required: true },
})

const { puo } = usersStore()
const t = (text, args) => __(text, args)
const locale = appLocale()

const entries = createResource({
  url: 'crm.scheduling.attese.get_entries',
  makeParams: () => ({ lead: props.lead }),
  // shown where there is an entry, or somebody who adds one
  transform: (data) => (data.entries.length || data.can_manage ? data : null),
  onError: () => entries.setData(null),
})

watch(
  () => props.lead,
  (lead) => lead && puo('agenda.attese') && entries.reload(),
  { immediate: true },
)

// the ones still in the line
const waiting = computed(
  () =>
    (entries.data?.entries || []).filter((entry) =>
      APERTE.includes(entry.status),
    ).length,
)

function line(entry) {
  const parts = [
    entry.class_session
      ? __('A seat in the class of {0}', [
          formatDate(entry.class_starts_on, 'ddd D MMM, HH:mm'),
        ])
      : quandoPuo(entry, t, locale),
  ]
  if (entry.staff_name) parts.push(entry.staff_name)
  if (entry.until && APERTE.includes(entry.status))
    parts.push(__('until {0}', [formatDate(entry.until, 'D MMM')]))
  return parts.join(' · ')
}

function offerLine(offer) {
  return `${formatDate(offer.starts_on, 'ddd D MMM, HH:mm')} · ${comeStaLOfferta(
    offer,
    t,
    (value) => formatDate(value, 'HH:mm'),
  )}`
}

const dialog = reactive({ show: false, name: null })

function open(name) {
  Object.assign(dialog, { show: true, name })
}
</script>
