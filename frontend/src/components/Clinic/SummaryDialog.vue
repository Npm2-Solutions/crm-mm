<!--
  Copyright (c) 2026, NPM2 Solutions Srl and contributors
  For license information, please see license.txt

  The summary before the visit: what the practitioner may read of the record,
  summarised with its sources numbered, [1], [2]. No scores, no alerts, no
  advice; nothing is kept but the register's event.
-->
<template>
  <Dialog
    v-model="show"
    :options="{ title: __('Summary before the visit'), size: '3xl' }"
  >
    <template #body-content>
      <div class="flex flex-col gap-3">
        <p
          class="rounded-md bg-surface-gray-2 px-3 py-2 text-p-sm text-ink-gray-7"
        >
          {{
            __(
              'An AI summary of what you may read of the record, citing its sources: check it against them. It gives no scores and no alerts, and it is not kept.',
            )
          }}
        </p>
        <div v-if="busy" class="py-10 text-center text-p-sm text-ink-gray-5">
          {{ __('The assistant is reading the record…') }}
        </div>
        <template v-else-if="summary">
          <p class="whitespace-pre-line text-p-base text-ink-gray-9">
            {{ summary.summary }}
          </p>
          <div class="flex flex-col gap-1 border-t border-outline-gray-1 pt-3">
            <span class="text-sm font-medium text-ink-gray-5">
              {{ __('Sources') }}
            </span>
            <span
              v-for="source in summary.sources"
              :key="source.n"
              class="text-p-sm text-ink-gray-7"
            >
              [{{ source.n }}] {{ source.label }}
            </span>
          </div>
        </template>
        <ErrorMessage :message="error" />
      </div>
    </template>
    <template #actions>
      <div class="dialog-footer flex justify-end">
        <Button variant="solid" :label="__('Done')" @click="done" />
      </div>
    </template>
  </Dialog>
</template>

<script setup>
import { Button, Dialog, ErrorMessage, call } from 'frappe-ui'
import { ref, watch } from 'vue'

const props = defineProps({ lead: { type: String, required: true } })
const show = defineModel({ type: Boolean })

const summary = ref(null)
const busy = ref(false)
const error = ref('')

watch(show, async (open) => {
  if (!open) return
  summary.value = null
  error.value = ''
  busy.value = true
  try {
    const answer = await call('crm.clinica.riassunto.summary_before_visit', {
      lead: props.lead,
    })
    if (answer.error) {
      error.value = answer.error
    } else {
      summary.value = answer
    }
  } catch (e) {
    error.value = e.messages?.join(' ') || e.message
  } finally {
    busy.value = false
  }
})

async function done() {
  // read: the register says the practitioner saw it
  if (summary.value?.event) {
    call('crm.clinica.riassunto.read', { event: summary.value.event }).catch(
      () => {},
    )
  }
  show.value = false
}
</script>
