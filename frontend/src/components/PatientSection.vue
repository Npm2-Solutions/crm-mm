<template>
  <!-- Whether the person is a patient, since when and why: only where the plan
       has the clinic, and only for who may know it. Marketing does not. -->
  <div v-if="status.data" class="flex flex-col">
    <div class="h-px w-full border-t" />
    <div class="p-1 sm:p-3">
      <CollapsibleSection
        labelClass="px-2 font-semibold"
        headerClass="h-8"
        :label="__('Patient')"
      >
        <div class="flex flex-col gap-2 px-3 pb-1 pt-3">
          <template v-if="patient">
            <div class="flex items-center gap-1 text-base text-ink-gray-8">
              <IndicatorIcon
                class="-ml-1 shrink-0"
                :class="parseColor('green')"
              />
              <span>
                {{
                  __('Patient since {0}', [
                    formatDate(patient.patient_since, '', true),
                  ])
                }}
              </span>
            </div>
            <div class="text-p-sm text-ink-gray-6">
              {{ because }}
            </div>
            <div
              v-if="patient.note"
              class="whitespace-pre-line text-p-sm text-ink-gray-5 [overflow-wrap:anywhere]"
            >
              {{ patient.note }}
            </div>
          </template>
          <template v-else>
            <div class="flex items-center justify-between gap-2">
              <div
                class="flex min-w-0 items-center gap-1 text-base text-ink-gray-7"
              >
                <IndicatorIcon class="-ml-1 shrink-0 text-ink-gray-4" />
                <span class="truncate">{{ __('Not a patient') }}</span>
              </div>
              <Button
                v-if="status.data.can_mark"
                size="sm"
                variant="ghost"
                class="touch-target shrink-0"
                :label="__('Mark as patient')"
                @click="showMark = true"
              />
            </div>
            <div class="text-p-sm text-ink-gray-5">
              {{
                __(
                  'They become one by themselves on their first appointment attended or their first healthcare invoice.',
                )
              }}
            </div>
          </template>
        </div>
      </CollapsibleSection>
    </div>
  </div>

  <Dialog
    v-model="showMark"
    :options="{ title: __('Mark as patient'), size: 'md' }"
  >
    <template #body-content>
      <div class="flex flex-col gap-4">
        <p class="text-p-base text-ink-gray-7">
          {{
            __(
              'For who no rule sees: a patient of the old practice, a visit outside the agenda. A patient stays a patient: their clinical record is kept.',
            )
          }}
        </p>
        <FormControl
          v-model="note"
          type="textarea"
          :label="__('Why')"
          :placeholder="__('Patient of the previous practice since 2019')"
        />
        <ErrorMessage :message="error" />
      </div>
    </template>
    <template #actions>
      <div class="flex justify-end">
        <Button
          variant="solid"
          :label="__('Mark as patient')"
          :loading="saving"
          @click="mark"
        />
      </div>
    </template>
  </Dialog>
</template>

<script setup>
import CollapsibleSection from '@/components/CollapsibleSection.vue'
import IndicatorIcon from '@/components/Icons/IndicatorIcon.vue'
import { usersStore } from '@/stores/users'
import { formatDate, parseColor } from '@/utils'
import {
  Dialog,
  ErrorMessage,
  FormControl,
  createResource,
  call,
  toast,
} from 'frappe-ui'
import { computed, ref, watch } from 'vue'

const props = defineProps({
  lead: { type: String, required: true },
})

const { puo } = usersStore()

const status = createResource({
  url: 'crm.clinica.paziente.patient_status',
  makeParams: () => ({ lead: props.lead }),
  onError: () => status.setData(null),
})

watch(
  () => props.lead,
  (lead) => lead && puo('pazienti.vedi') && status.reload(),
  { immediate: true },
)

const patient = computed(() => status.data?.patient)

const RULES = {
  'Medical information': __('the first clinical record saved about them'),
  'Check-in': __('their arrival registered at the desk'),
  'Appointment attended': __('an appointment attended'),
  'Healthcare invoice': __('a healthcare invoice'),
  Import: __('brought over from the previous software'),
  'By hand': __('marked by hand'),
}

const because = computed(() => {
  const p = patient.value
  if (!p) return ''
  const rule = RULES[p.rule] || p.rule
  return p.recorded_by_name
    ? __('Because of {0}, by {1}', [rule, p.recorded_by_name])
    : __('Because of {0}', [rule])
})

const showMark = ref(false)
const note = ref('')
const error = ref('')
const saving = ref(false)

async function mark() {
  saving.value = true
  error.value = ''
  try {
    const data = await call('crm.clinica.paziente.mark_as_patient', {
      lead: props.lead,
      note: note.value || null,
    })
    status.setData(data)
    showMark.value = false
    note.value = ''
    toast.success(__('Marked as patient'))
  } catch (err) {
    error.value = err.messages?.[0] || err.message
  } finally {
    saving.value = false
  }
}
</script>
