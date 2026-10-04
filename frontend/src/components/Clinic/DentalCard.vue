<!--
  Copyright (c) 2026, NPM2 Solutions Srl and contributors
  For license information, please see license.txt

  The teeth: the odontogram the dentists write. A care plan is a quote with a tooth
  on its rows: on the Quotes tab, with the others (crm.preventivi).
-->
<template>
  <section
    v-if="shown"
    class="flex flex-col gap-3 rounded-lg border border-outline-gray-2 p-4"
  >
    <div class="flex flex-wrap items-center justify-between gap-2">
      <h3 class="text-base-semibold text-ink-gray-8">
        {{ __('Teeth') }}
      </h3>
      <div class="flex shrink-0 flex-wrap items-center gap-2">
        <!-- on a phone the chart is written top to bottom: saving is at
             its end -->
        <template v-if="editing">
          <Button
            class="max-md:hidden"
            :label="__('Cancel')"
            @click="stopEditing"
          />
          <Button
            class="max-md:hidden"
            variant="solid"
            :label="__('Save the chart')"
            :loading="saving"
            @click="saveChart"
          />
        </template>
        <template v-else>
          <Button
            v-if="canWriteChart"
            :label="
              dental.data.chart ? __('Edit the chart') : __('Start the chart')
            "
            @click="startEditing"
          />
        </template>
      </div>
    </div>

    <!-- the chart: somebody else's without the dossier is said, not shown -->
    <p
      v-if="dental.data.chart?.hidden"
      class="rounded-md bg-surface-gray-2 px-3 py-2 text-p-sm text-ink-gray-7"
    >
      {{
        __(
          'The dental chart was started by {0}: with the dossier consent you read it.',
          [dental.data.chart.practitioner_name],
        )
      }}
    </p>
    <template v-else-if="dental.data.chart || editing">
      <div v-if="editing" class="flex flex-wrap items-center gap-2">
        <span class="text-p-sm text-ink-gray-6">{{ __('Dentition') }}</span>
        <TabButtons v-model="draft.dentition" :buttons="dentitions" />
      </div>
      <DentalChart
        :rows="editing ? draft.teeth : dental.data.chart.teeth"
        :dentition="editing ? draft.dentition : dental.data.chart.dentition"
        :selected="tooth"
        @select="(value) => (tooth = tooth === value ? null : value)"
      />
      <!-- the legend: the conditions on the chart, by name -->
      <div v-if="legend.length" class="flex flex-wrap gap-x-3 gap-y-1">
        <span
          v-for="condition in legend"
          :key="condition"
          class="flex items-center gap-1.5 text-p-xs text-ink-gray-6"
        >
          <span class="size-2 rounded-sm" :class="segno(condition)" />
          {{ nomeDi(condition) }}
        </span>
      </div>

      <!-- one tooth: what it is, and in writing what to change -->
      <div
        v-if="tooth"
        class="flex flex-col gap-2 rounded-md border border-outline-gray-2 p-3"
      >
        <div class="text-p-base font-medium text-ink-gray-8">
          {{ __('Tooth {0}', [tooth]) }}
        </div>
        <p
          v-if="!toothRows.length && !editing"
          class="text-p-sm text-ink-gray-5"
        >
          {{ __('Nothing noted on this tooth.') }}
        </p>
        <div
          v-for="(row, index) in toothRows"
          :key="`${row.condition}-${index}`"
          class="flex flex-wrap items-center gap-2"
        >
          <span
            class="shrink-0 rounded px-1.5 py-0.5 text-p-xs font-medium"
            :class="tono(row.condition)"
          >
            {{ nomeDi(row.condition) }}
          </span>
          <template v-if="editing">
            <!-- on a phone the fields go under the condition, the × beside it -->
            <div
              class="flex min-w-0 flex-1 gap-2 max-md:order-last max-md:basis-full"
            >
              <div v-if="suSuperfici(row.condition)" class="w-24 shrink-0">
                <TextInput
                  v-model="row.surfaces"
                  :placeholder="__('MOD')"
                  :aria-label="__('Surfaces')"
                />
              </div>
              <div class="min-w-0 flex-1">
                <TextInput
                  v-model="row.note"
                  :placeholder="__('Note')"
                  :aria-label="__('Note')"
                />
              </div>
            </div>
            <Button
              variant="ghost"
              icon="x"
              class="touch-target shrink-0 max-md:ml-auto"
              :aria-label="__('Remove')"
              @click="removeRow(row)"
            />
          </template>
          <span v-else class="min-w-0 text-p-sm text-ink-gray-7">
            {{ [row.surfaces, row.note].filter(Boolean).join(' · ') }}
            <span v-if="row.noted_by_name" class="text-ink-gray-5">
              · {{ row.noted_by_name }},
              {{ formatDate(row.noted_on, 'D MMM YYYY') }}
            </span>
          </span>
        </div>
        <Dropdown v-if="editing" :options="addOptions" placement="left">
          <Button
            class="w-fit"
            size="sm"
            icon-left="plus"
            :label="__('Add a condition')"
          />
        </Dropdown>
      </div>
      <p
        v-else-if="!editing && dental.data.chart?.updated_by_name"
        class="text-p-xs text-ink-gray-5"
      >
        {{
          __('Updated by {0} on {1}. Pick a tooth to read it.', [
            dental.data.chart.updated_by_name,
            formatDate(dental.data.chart.updated_on, 'D MMM YYYY'),
          ])
        }}
      </p>
      <ErrorMessage :message="error" />
      <div v-if="editing" class="flex gap-2 md:hidden [&>button]:flex-1">
        <Button :label="__('Cancel')" @click="stopEditing" />
        <Button
          variant="solid"
          :label="__('Save the chart')"
          :loading="saving"
          @click="saveChart"
        />
      </div>
    </template>

    <p v-if="!dental.data.chart && !editing" class="text-p-sm text-ink-gray-5">
      {{
        __(
          'No chart yet. The chart says what each tooth is; a care plan is a quote, on the Quotes tab.',
        )
      }}
    </p>
  </section>
</template>

<script setup>
import DentalChart from '@/components/Clinic/DentalChart.vue'
import { usersStore } from '@/stores/users'
import { formatDate } from '@/utils'
import {
  CONDIZIONI,
  DECIDUA,
  MISTA,
  PERMANENTE,
  delDente,
  segno,
  suSuperfici,
  tono,
} from '@/utils/cure'
import {
  Button,
  Dropdown,
  ErrorMessage,
  TabButtons,
  TextInput,
  call,
  createResource,
  toast,
} from 'frappe-ui'
import { computed, reactive, ref, watch } from 'vue'

const props = defineProps({ lead: { type: String, required: true } })

const { puo } = usersStore()

const dental = createResource({
  url: 'crm.clinica.cure.get_dental',
  makeParams: () => ({ lead: props.lead }),
  onError: () => dental.setData(null),
})

watch(
  () => props.lead,
  (lead) => {
    if (lead && (puo('cure.scrivi') || puo('clinica.vedi'))) dental.reload()
  },
  { immediate: true },
)

// a card only where there is a chart, or a dentist to write it
const shown = computed(
  () => dental.data && (dental.data.is_dentist || dental.data.chart),
)

const canWriteChart = computed(
  () =>
    dental.data?.is_dentist &&
    !dental.data.chart?.hidden &&
    (!dental.data.chart || dental.data.chart.can_write),
)

// --- the chart -----------------------------------------------------------------

const tooth = ref(null)
const editing = ref(false)
const saving = ref(false)
const error = ref('')
const draft = reactive({ dentition: PERMANENTE, teeth: [] })

const dentitions = [
  { label: __('Permanent'), value: PERMANENTE },
  { label: __('Mixed'), value: MISTA },
  { label: __('Milk teeth'), value: DECIDUA },
]

const rows = computed(() =>
  editing.value ? draft.teeth : dental.data?.chart?.teeth || [],
)
const toothRows = computed(() =>
  tooth.value ? delDente(rows.value, tooth.value) : [],
)
const legend = computed(() =>
  CONDIZIONI.map((c) => c.value).filter((value) =>
    rows.value.some((row) => row.condition === value),
  ),
)

function startEditing() {
  const chart = dental.data.chart
  draft.dentition = chart?.dentition || PERMANENTE
  draft.teeth = (chart?.teeth || []).map((row) => ({ ...row }))
  error.value = ''
  editing.value = true
}

function stopEditing() {
  editing.value = false
  error.value = ''
}

// what can still be added to the tooth: a condition once
const addOptions = computed(() =>
  CONDIZIONI.filter(
    (c) => !toothRows.value.some((row) => row.condition === c.value),
  ).map((c) => ({
    label: nomeDi(c.value),
    onClick: () =>
      draft.teeth.push({
        tooth: tooth.value,
        condition: c.value,
        surfaces: '',
        note: '',
      }),
  })),
)

// a condition by its name: «Mobile» is a tooth that moves, not a phone
function nomeDi(condizione) {
  return __(condizione, null, 'Tooth condition')
}

function removeRow(row) {
  draft.teeth = draft.teeth.filter((one) => one !== row)
}

async function saveChart() {
  saving.value = true
  error.value = ''
  try {
    await call('crm.clinica.cure.save_chart', {
      lead: props.lead,
      teeth: draft.teeth,
      dentition: draft.dentition,
    })
    toast.success(__('Chart saved'))
    editing.value = false
    dental.reload()
  } catch (e) {
    error.value = (e.messages?.[0] || __('Could not save the chart')).replace(
      /<br>/g,
      ' · ',
    )
  } finally {
    saving.value = false
  }
}
</script>
