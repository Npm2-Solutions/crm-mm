<!--
  Copyright (c) 2026, NPM2 Solutions Srl and contributors
  For license information, please see license.txt
-->
<template>
  <div class="mx-auto flex w-full max-w-3xl flex-col gap-3 px-4 py-6">
    <!-- the campaigns sent from People (crm/automation/campagne.py): to which
         list, how many got in, who was left out and why -->
    <section v-if="campagne.data?.length" class="mb-3 flex flex-col gap-2">
      <h3 class="text-base font-medium text-ink-gray-8">
        {{ __('Campaigns sent') }}
      </h3>
      <div
        class="divide-y divide-outline-gray-1 rounded-lg border border-outline-gray-2"
      >
        <div
          v-for="campagna in campagne.data"
          :key="campagna.name"
          class="flex flex-col gap-1.5 px-3 py-2.5"
        >
          <div class="flex flex-wrap items-center gap-x-3 gap-y-1">
            <span class="min-w-0 flex-1 text-base text-ink-gray-8">
              {{ campagna.source || __('The list on screen') }}
            </span>
            <Badge
              size="sm"
              :theme="TEMI_CAMPAGNA[campagna.status]"
              :label="STATI_CAMPAGNA[campagna.status] || __(campagna.status)"
            />
          </div>
          <span class="text-p-sm text-ink-gray-6">
            {{
              __('{0} · by {1}', [
                formatDate(campagna.creation, 'D MMM YYYY, HH:mm'),
                campagna.sent_by,
              ])
            }}
          </span>
          <span class="text-p-sm text-ink-gray-8">
            {{
              __('{0} in the list · {1} enrolled · {2} left out', [
                campagna.total,
                campagna.enrolled,
                quantiSaltati(campagna.skipped),
              ])
            }}
          </span>
          <ul
            v-if="quantiSaltati(campagna.skipped)"
            class="flex flex-col gap-0.5 text-p-sm text-ink-gray-6"
          >
            <li
              v-for="riga in righeDeiSalti(
                campagna.skipped,
                canaliDellaCampagna,
                __,
              )"
              :key="riga.chiave"
            >
              {{ __('{0}: {1}', [riga.testo, riga.quanti]) }}
            </li>
          </ul>
        </div>
      </div>
    </section>
    <div class="flex items-center justify-between">
      <div class="flex flex-wrap gap-1.5">
        <Button
          v-for="status in STATUSES"
          :key="status"
          size="sm"
          :variant="filter === status ? 'solid' : 'outline'"
          :label="FILTRI[status]"
          @click="((filter = status), enrollments.reload())"
        />
      </div>
      <Button
        variant="ghost"
        icon="lucide-refresh-cw"
        :label="__('Refresh')"
        @click="(enrollments.reload(), campagne.reload())"
      />
    </div>

    <div
      v-if="enrollments.data?.length"
      class="divide-y divide-outline-gray-1 rounded-lg border border-outline-gray-2"
    >
      <div v-for="row in enrollments.data" :key="row.name">
        <button
          class="flex w-full items-center gap-3 px-3 py-2 text-left hover:bg-surface-gray-1"
          @click="toggle(row)"
        >
          <FeatherIcon
            :name="expanded === row.name ? 'chevron-down' : 'chevron-right'"
            class="size-4 shrink-0 text-ink-gray-5"
          />
          <span class="min-w-0 flex-1 truncate text-base text-ink-gray-8">
            {{ row.title || row.reference_name }}
          </span>
          <span class="shrink-0 text-xs text-ink-gray-5">
            <!-- the server's time is the centre's clock: read against the
                 centre's now, never the phone's («in 2 hours» from Lisbon) -->
            {{ dayjs(row.modified).from(adessoDelCentro()) }}
          </span>
          <Badge
            size="sm"
            :theme="THEMES[row.status]"
            :label="STATI[row.status] || __(row.status)"
          />
        </button>

        <div
          v-if="expanded === row.name"
          class="border-t border-outline-gray-1 bg-surface-gray-1 px-4 py-3"
        >
          <div v-if="detail.loading" class="text-sm text-ink-gray-5">
            {{ __('Loading…') }}
          </div>
          <ol v-else class="flex flex-col gap-2">
            <li
              v-for="(log, index) in detail.data?.logs || []"
              :key="index"
              class="flex items-start gap-2 text-sm"
            >
              <FeatherIcon
                :name="LOG_ICONS[log.status] || 'circle'"
                class="mt-0.5 size-3.5 shrink-0"
                :class="LOG_COLORS[log.status]"
              />
              <div class="min-w-0 flex-1">
                <span class="font-medium text-ink-gray-7">
                  {{ stepLabel(log.action) }}
                </span>
                <span class="text-ink-gray-5"> — {{ log.detail }}</span>
              </div>
              <span class="shrink-0 text-xs text-ink-gray-5">
                {{ dayjs(log.creation).format('DD/MM HH:mm') }}
              </span>
            </li>
            <li
              v-if="!(detail.data?.logs || []).length"
              class="text-sm text-ink-gray-5"
            >
              {{ __('No steps have run yet.') }}
            </li>
          </ol>
        </div>
      </div>
    </div>
    <div v-else class="py-8 text-center text-sm text-ink-gray-5">
      {{ __('No records have been enrolled yet.') }}
    </div>
  </div>
</template>

<script setup>
import { Badge, Button, FeatherIcon, createResource, dayjs } from 'frappe-ui'
import { computed, onBeforeUnmount, onMounted, ref } from 'vue'
import { stepLabel } from '@/utils/automation'
import { formatDate } from '@/utils'
import { canali, quantiSaltati, righeDeiSalti } from '@/utils/campagne'
import { globalStore } from '@/stores/global'
import { adessoDelCentro } from '@/utils/scheduler'

const props = defineProps({
  automation: { type: String, required: true },
  // the builder's steps: the ways it writes by name a reason in words
  steps: { type: Array, default: () => [] },
})

const STATI_CAMPAGNA = {
  Queued: __('Queued', null, 'Campaign state'),
  Running: __('Being sent', null, 'Campaign state'),
  Done: __('Sent', null, 'Campaign state'),
  Failed: __('Failed', null, 'Campaign state'),
}
const TEMI_CAMPAGNA = {
  Queued: 'gray',
  Running: 'orange',
  Done: 'green',
  Failed: 'red',
}

const campagne = createResource({
  url: 'crm.automation.campagne.get_campaigns',
  makeParams: () => ({ automation: props.automation }),
  auto: true,
})
const canaliDellaCampagna = computed(() => canali(props.steps))

// the job tells whoever sent it when it is done
const { $socket } = globalStore()
function campagnaFatta(dati) {
  if (dati?.automation !== props.automation) return
  campagne.reload()
  enrollments.reload()
}
onMounted(() => $socket?.on('crm_campaign_done', campagnaFatta))
onBeforeUnmount(() => $socket?.off('crm_campaign_done', campagnaFatta))

const STATUSES = [
  'All',
  'Active',
  'Waiting',
  'Completed',
  'Exited',
  'Skipped',
  'Failed',
]

// an enrolment is feminine in Italian: the filters and the states agree with it
const FILTRI = {
  All: __('All', null, 'Enrolments filter'),
  Active: __('Active', null, 'Enrolments filter'),
  Waiting: __('Waiting', null, 'Enrolments filter'),
  Completed: __('Completed', null, 'Enrolments filter'),
  Exited: __('Exited', null, 'Enrolments filter'),
  Skipped: __('Skipped', null, 'Enrolments filter'),
  Failed: __('Failed', null, 'Enrolments filter'),
}

const STATI = {
  Active: __('Active', null, 'Enrolment state'),
  Waiting: __('Waiting', null, 'Enrolment state'),
  Completed: __('Completed', null, 'Enrolment state'),
  Exited: __('Exited', null, 'Enrolment state'),
  Skipped: __('Skipped', null, 'Enrolment state'),
  Failed: __('Failed', null, 'Enrolment state'),
}

const THEMES = {
  Active: 'blue',
  Waiting: 'orange',
  Completed: 'green',
  Exited: 'gray',
  // not let in: no marketing consent
  Skipped: 'gray',
  Failed: 'red',
}

const LOG_ICONS = {
  Success: 'check-circle',
  Failed: 'alert-triangle',
  Skipped: 'corner-down-right',
}

const LOG_COLORS = {
  Success: 'text-ink-green-7',
  Failed: 'text-ink-red-7',
  Skipped: 'text-ink-gray-5',
}

const filter = ref('All')
const expanded = ref(null)

const enrollments = createResource({
  url: 'crm.api.automation.get_enrollments',
  makeParams: () => ({ automation: props.automation, status: filter.value }),
  auto: true,
})

const detail = createResource({
  url: 'crm.api.automation.get_enrollment_detail',
  makeParams: () => ({ name: expanded.value }),
})

function toggle(row) {
  if (expanded.value === row.name) {
    expanded.value = null
    return
  }
  expanded.value = row.name
  detail.fetch()
}
</script>
