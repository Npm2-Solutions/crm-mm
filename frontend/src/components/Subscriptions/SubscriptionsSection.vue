<template>
  <!-- The person's subscriptions: a month of the gym, three months of pilates
       twice a week. Sold here, the appointments of the services they comprise
       use their entries by themselves; each says until when it lasts and how
       this week's or month's entries stand. -->
  <div v-if="subscriptions.data" class="flex flex-col">
    <div class="h-px w-full border-t" />
    <div class="p-1 sm:p-3">
      <CollapsibleSection
        labelClass="px-2 font-semibold"
        headerClass="h-8"
        :label="__('Subscriptions')"
        :count="going || ''"
      >
        <template #actions>
          <Button
            v-if="
              subscriptions.data.can_manage && subscriptions.data.types.length
            "
            variant="ghost"
            class="touch-target"
            icon="plus"
            :aria-label="__('Sell a subscription')"
            :title="__('Sell a subscription')"
            @click="open(null)"
          />
        </template>
        <div class="flex flex-col gap-0.5 pb-1 pt-2">
          <button
            v-for="sub in subscriptions.data.subscriptions"
            :key="sub.name"
            type="button"
            class="flex flex-col gap-1 rounded px-3 py-1.5 text-left hover:bg-surface-gray-2 focus-visible:bg-surface-gray-2 focus-visible:outline-none"
            @click="open(sub.name)"
          >
            <span class="flex items-center justify-between gap-2">
              <span class="min-w-0 truncate text-base text-ink-gray-8">
                {{ sub.subscription_type }}
              </span>
              <Badge
                class="shrink-0"
                variant="subtle"
                :theme="TEMA_DELLO_STATO[sub.status] || 'gray'"
                :label="__(sub.status)"
              />
            </span>
            <span
              v-if="sub.entries !== ILLIMITATI && sub.used !== null"
              class="h-1.5 w-full overflow-hidden rounded-full bg-surface-gray-2"
              role="progressbar"
              :aria-valuenow="percentuale(sub)"
              aria-valuemin="0"
              aria-valuemax="100"
              :aria-label="__('Entries used')"
            >
              <span
                class="block h-full rounded-full bg-[var(--brand-segno)]"
                :style="{ width: `${percentuale(sub)}%` }"
              />
            </span>
            <span class="text-p-sm text-ink-gray-6">{{ line(sub) }}</span>
          </button>
          <div
            v-if="!subscriptions.data.subscriptions.length"
            class="px-3 py-1 text-p-sm text-ink-gray-5"
          >
            {{
              subscriptions.data.types.length
                ? __(
                    'No subscription yet: a month of the gym, three of pilates…',
                  )
                : __(
                    'No subscription yet. The types to sell are made in Settings > Agenda > Services > Subscriptions.',
                  )
            }}
          </div>
        </div>
      </CollapsibleSection>
    </div>
  </div>
  <SubscriptionDialog
    v-model="dialog.show"
    :lead="lead"
    :name="dialog.name"
    :types="subscriptions.data?.types || []"
    @changed="subscriptions.reload()"
  />
</template>

<script setup>
import CollapsibleSection from '@/components/CollapsibleSection.vue'
import SubscriptionDialog from '@/components/Subscriptions/SubscriptionDialog.vue'
import { usersStore } from '@/stores/users'
import { formatDate } from '@/utils'
import {
  ILLIMITATI,
  TEMA_DELLO_STATO,
  percentuale,
  questoPeriodo,
} from '@/utils/abbonamenti'
import { Badge, Button, createResource } from 'frappe-ui'
import { computed, reactive, watch } from 'vue'

const props = defineProps({
  lead: { type: String, required: true },
})

const { puo } = usersStore()
const t = (text, args) => __(text, args)

const subscriptions = createResource({
  url: 'crm.scheduling.abbonamenti.get_subscriptions',
  makeParams: () => ({ lead: props.lead }),
  // shown where there are subscriptions, or somebody who sells them
  transform: (data) =>
    data.subscriptions.length || data.can_manage ? data : null,
  onError: () => subscriptions.setData(null),
})

watch(
  () => props.lead,
  (lead) =>
    lead &&
    (puo('agenda.vedi') || puo('agenda.abbonamenti')) &&
    subscriptions.reload(),
  { immediate: true },
)

// the ones going on
const going = computed(
  () =>
    (subscriptions.data?.subscriptions || []).filter((sub) =>
      ['Active', 'Suspended'].includes(sub.status),
    ).length,
)

function line(sub) {
  const parts = []
  if (['Active', 'Suspended'].includes(sub.status)) {
    const period = questoPeriodo(sub, t)
    if (period) parts.push(period)
    if (sub.suspended_until)
      parts.push(
        __('suspended until {0}', [formatDate(sub.suspended_until, 'D MMM')]),
      )
    parts.push(__('until {0}', [formatDate(sub.ends_on, 'D MMM YYYY')]))
  } else {
    parts.push(
      __('{0} to {1}', [
        formatDate(sub.starts_on, 'D MMM YYYY'),
        formatDate(sub.ends_on, 'D MMM YYYY'),
      ]),
    )
  }
  if (sub.renewed_by) parts.push(__('renewed'))
  return parts.join(' · ')
}

const dialog = reactive({ show: false, name: null })

function open(name) {
  Object.assign(dialog, { show: true, name })
}
</script>
