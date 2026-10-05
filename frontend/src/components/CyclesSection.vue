<template>
  <!-- The person's cycles of sessions: ten of physiotherapy, six of laser. Sold
       here, the appointments of their service join them by themselves; each
       says how far it is and when the next session is. -->
  <div v-if="cycles.data" class="flex flex-col">
    <div class="h-px w-full border-t" />
    <div class="p-1 sm:p-3">
      <CollapsibleSection
        labelClass="px-2 font-semibold"
        headerClass="h-8"
        :label="__('Cycles of sessions')"
        :count="going || ''"
      >
        <template #actions>
          <Button
            v-if="cycles.data.can_manage"
            variant="ghost"
            class="touch-target"
            icon="plus"
            :aria-label="__('Sell a cycle')"
            :title="__('Sell a cycle')"
            @click="open(null)"
          />
        </template>
        <div class="flex flex-col gap-0.5 pb-1 pt-2">
          <button
            v-for="cycle in cycles.data.cycles"
            :key="cycle.name"
            type="button"
            class="flex flex-col gap-1 rounded px-3 py-1.5 text-left hover:bg-surface-gray-2 focus-visible:bg-surface-gray-2 focus-visible:outline-none"
            @click="open(cycle.name)"
          >
            <span class="flex items-center justify-between gap-2">
              <span class="min-w-0 truncate text-base text-ink-gray-8">
                {{ serviceName(cycle.service) }}
              </span>
              <InProgressBadge
                v-if="cycle.status === 'Active'"
                class="shrink-0"
                :label="__(cycle.status)"
              />
              <Badge
                v-else
                class="shrink-0"
                variant="subtle"
                :theme="TEMA_DELLO_STATO[cycle.status] || 'gray'"
                :label="__(cycle.status)"
              />
            </span>
            <!-- one segment a session, the used ones in the brand's colour -->
            <span
              v-if="tappe(cycle.counts)"
              class="dc-steps w-full"
              role="progressbar"
              :aria-valuenow="percentuale(cycle.counts)"
              aria-valuemin="0"
              aria-valuemax="100"
              :aria-label="__('Sessions used')"
            >
              <span
                v-for="(usata, i) in tappe(cycle.counts)"
                :key="i"
                :class="{ 'is-done': usata }"
              />
            </span>
            <span
              v-else
              class="h-1.5 w-full overflow-hidden rounded-full bg-surface-gray-2"
              role="progressbar"
              :aria-valuenow="percentuale(cycle.counts)"
              aria-valuemin="0"
              aria-valuemax="100"
              :aria-label="__('Sessions used')"
            >
              <span
                class="block h-full rounded-full bg-[var(--brand-segno)]"
                :style="{ width: `${percentuale(cycle.counts)}%` }"
              />
            </span>
            <span class="text-p-sm text-ink-gray-6">
              {{ comeVa(cycle.counts, t) }}
            </span>
            <span v-if="cycle.next" class="text-p-sm text-ink-gray-5">
              {{
                __('Next session {0}', [
                  formatDate(cycle.next, 'ddd D MMM, HH:mm'),
                ])
              }}
            </span>
            <span
              v-else-if="cycle.status === 'Active' && cycle.counts.left"
              class="text-p-sm text-ink-gray-5"
            >
              {{ daPrenotare(cycle.counts, t) }}
            </span>
          </button>
          <div
            v-if="!cycles.data.cycles.length"
            class="px-3 py-1 text-p-sm text-ink-gray-5"
          >
            {{
              __('No cycles yet: ten sessions of physiotherapy, six of laser…')
            }}
          </div>
        </div>
      </CollapsibleSection>
    </div>
  </div>
  <CycleDialog
    v-model="dialog.show"
    :lead="lead"
    :name="dialog.name"
    @changed="cycles.reload()"
  />
</template>

<script setup>
import CollapsibleSection from '@/components/CollapsibleSection.vue'
import CycleDialog from '@/components/CycleDialog.vue'
import InProgressBadge from '@/components/Espresso/InProgressBadge.vue'
import { useSchedulerMeta } from '@/composables/scheduling'
import { usersStore } from '@/stores/users'
import { formatDate } from '@/utils'
import {
  TEMA_DELLO_STATO,
  comeVa,
  daPrenotare,
  percentuale,
  tappe,
} from '@/utils/cicli'
import { Badge, Button, createResource } from 'frappe-ui'
import { computed, reactive, watch } from 'vue'

const props = defineProps({
  lead: { type: String, required: true },
})

const { puo } = usersStore()
const meta = useSchedulerMeta()
const t = (text, args, contesto) => __(text, args, contesto)

const cycles = createResource({
  url: 'crm.scheduling.cicli.get_cycles',
  makeParams: () => ({ lead: props.lead }),
  // shown where there are cycles, or somebody who sells them
  transform: (data) => (data.cycles.length || data.can_manage ? data : null),
  onError: () => cycles.setData(null),
})

watch(
  () => props.lead,
  (lead) => lead && puo('agenda.vedi') && cycles.reload(),
  { immediate: true },
)

// the ones going on
const going = computed(
  () =>
    (cycles.data?.cycles || []).filter((cycle) => cycle.status === 'Active')
      .length,
)

function serviceName(name) {
  const service = (meta.data?.services || []).find((one) => one.name === name)
  return service?.service_name || name
}

const dialog = reactive({ show: false, name: null })

function open(name) {
  Object.assign(dialog, { show: true, name })
}
</script>
