<!--
  The patient's summary: allergies, medications, conditions, parameters.

  A line is the last value a practitioner confirmed. The answers of signed forms
  and sheets that fill a line wait here as proposals, until somebody confirms
  them (as they are, or corrected) or discards them; a line can also be written
  by hand. Every value stays, with where it came from and who decided.
-->
<template>
  <section
    v-if="summary.data"
    class="flex flex-col gap-3 rounded-lg border border-outline-gray-2 p-4"
  >
    <div class="flex items-center justify-between gap-2">
      <h3 class="text-base-semibold text-ink-gray-8">{{ __('Summary') }}</h3>
      <Badge
        v-if="summary.data.proposals.length"
        theme="blue"
        variant="subtle"
        :label="
          summary.data.proposals.length === 1
            ? __('1 to confirm')
            : __('{0} to confirm', [summary.data.proposals.length])
        "
      />
    </div>

    <dl
      class="grid grid-cols-[10rem_1fr] gap-x-4 gap-y-2 text-p-sm max-md:grid-cols-1 max-md:gap-y-0.5"
    >
      <template v-for="line in summary.data.lines" :key="line.key">
        <dt class="pt-1 text-ink-gray-5 max-md:pt-2">{{ line.label }}</dt>
        <dd class="flex min-w-0 items-start gap-2">
          <template v-if="editing === line.key">
            <FormControl
              v-model="draft"
              class="min-w-0 flex-1"
              :placeholder="line.unit"
              @keydown.enter="saveLine(line)"
            />
            <Button
              size="sm"
              variant="solid"
              class="touch-target shrink-0"
              :label="__('Save')"
              @click="saveLine(line)"
            />
            <Button
              size="sm"
              variant="ghost"
              class="touch-target shrink-0"
              :label="__('Cancel')"
              @click="editing = null"
            />
          </template>
          <template v-else>
            <span class="min-w-0 flex-1 pt-1">
              <span v-if="line.value" class="text-ink-gray-8">{{
                line.value
              }}</span>
              <span v-else class="text-ink-gray-4">—</span>
              <span v-if="line.value" class="block text-p-xs text-ink-gray-5">
                {{ line.source_title }} · {{ line.decided_by }},
                {{ formatDate(line.decided_on, 'D MMM YYYY') }}
              </span>
            </span>
            <Button
              v-if="summary.data.can_decide"
              size="sm"
              variant="ghost"
              class="touch-target shrink-0 [@media(hover:none)]:opacity-100"
              icon="edit-2"
              :aria-label="__('Write {0}', [line.label])"
              @click="edit(line)"
            />
          </template>
        </dd>
      </template>
    </dl>

    <!-- what signed forms and sheets propose: a practitioner decides -->
    <div v-if="summary.data.proposals.length" class="flex flex-col gap-2">
      <span class="text-sm font-medium text-ink-gray-5">
        {{ __('Proposed by what was signed') }}
      </span>
      <div
        v-for="proposal in summary.data.proposals"
        :key="proposal.name"
        class="flex flex-wrap items-center gap-2 rounded-md bg-surface-gray-1 px-3 py-2 text-p-sm"
      >
        <span class="min-w-0 flex-1">
          <span class="text-ink-gray-5">{{ __('{0}:', [proposal.label]) }}</span
          >{{ ' ' }}<span class="text-ink-gray-8">{{ proposal.value }}</span>
          <span class="block text-p-xs text-ink-gray-5">
            {{ proposal.source_title }},
            {{ formatDate(proposal.proposed_on, 'D MMM YYYY') }}
          </span>
        </span>
        <div v-if="summary.data.can_decide" class="flex shrink-0 gap-1">
          <Button
            size="sm"
            class="touch-target"
            :label="__('Confirm')"
            @click="decide('confirm_value', proposal)"
          />
          <Button
            size="sm"
            variant="ghost"
            class="touch-target"
            :label="__('Discard')"
            @click="decide('discard_value', proposal)"
          />
        </div>
      </div>
    </div>
  </section>
</template>

<script setup>
import { formatDate } from '@/utils'
import {
  Badge,
  Button,
  FormControl,
  call,
  createResource,
  toast,
} from 'frappe-ui'
import { ref, watch } from 'vue'

const props = defineProps({ lead: { type: String, required: true } })

const summary = createResource({
  url: 'crm.clinica.sintesi.get_summary',
  makeParams: () => ({ lead: props.lead }),
})
watch(
  () => props.lead,
  (lead) => lead && summary.reload(),
  { immediate: true },
)

const editing = ref(null)
const draft = ref('')

function edit(line) {
  editing.value = line.key
  draft.value = line.value || ''
}

async function saveLine(line) {
  try {
    summary.data = {
      ...summary.data,
      ...(await call('crm.clinica.sintesi.set_value', {
        lead: props.lead,
        key: line.key,
        value: draft.value,
      })),
    }
    editing.value = null
  } catch (error) {
    toast.error(error.messages?.[0] || error.message)
  }
}

async function decide(method, proposal) {
  try {
    summary.data = {
      ...summary.data,
      ...(await call(`crm.clinica.sintesi.${method}`, { name: proposal.name })),
    }
  } catch (error) {
    toast.error(error.messages?.[0] || error.message)
  }
}

defineExpose({ reload: () => summary.reload() })
</script>
