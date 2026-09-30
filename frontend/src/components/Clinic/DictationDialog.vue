<!--
  A visit dictated: the practitioner's words - typed, pasted, or dictated with
  the device's own dictation - proposed as answers of the sheet. Nothing is
  written by itself: the practitioner ticks what to keep, and medicines,
  allergies and doses are never ticked for them.
-->
<template>
  <Dialog
    v-model="show"
    :options="{ title: __('Fill from dictation'), size: '3xl' }"
  >
    <template #body-content>
      <div class="flex flex-col gap-3">
        <p
          class="rounded-md bg-surface-gray-2 px-3 py-2 text-p-sm text-ink-gray-7"
        >
          {{
            __(
              'Write or dictate what happened in the visit: the assistant proposes the answers of the sheet the words speak of, and you tick what to keep. Medicines, allergies and doses are confirmed one by one.',
            )
          }}
        </p>
        <template v-if="!proposals">
          <Textarea
            v-model="text"
            :rows="10"
            :placeholder="
              __(
                'For example: pain in the lower back for two weeks, worse sitting; no allergies…',
              )
            "
          />
        </template>
        <template v-else>
          <p v-if="!proposals.length" class="text-p-sm text-ink-gray-6">
            {{ __('The words do not fill any field of the sheet.') }}
          </p>
          <label
            v-for="proposal in proposals"
            :key="proposal.field"
            class="flex items-start gap-3 rounded-md px-2 py-2"
            :class="proposal.one_by_one ? 'bg-surface-amber-1' : ''"
          >
            <Checkbox
              v-model="kept[proposal.field]"
              class="touch-target mt-0.5 shrink-0"
            />
            <span class="flex min-w-0 flex-col">
              <span class="text-p-sm text-ink-gray-6">{{
                proposal.label
              }}</span>
              <span class="text-base text-ink-gray-9">
                {{ show_(proposal.value) }}
              </span>
              <span
                v-if="proposal.current != null && proposal.current !== ''"
                class="text-p-xs text-ink-gray-5"
              >
                {{ __('Now: {0}', [show_(proposal.current)]) }}
              </span>
              <span
                v-if="proposal.one_by_one"
                class="text-p-xs text-ink-amber-8"
              >
                {{ __('A medicine, an allergy or a dose: tick it yourself') }}
              </span>
            </span>
          </label>
        </template>
        <ErrorMessage :message="error" />
      </div>
    </template>
    <template #actions>
      <div class="dialog-footer flex flex-wrap justify-end gap-2">
        <template v-if="!proposals">
          <Button :label="__('Cancel')" @click="show = false" />
          <Button
            variant="solid"
            :label="__('Propose the answers')"
            :disabled="text.trim().length < 10"
            :loading="busy === 'propose'"
            @click="propose"
          />
        </template>
        <template v-else>
          <Button
            :label="__('Discard')"
            :loading="busy === 'discard'"
            @click="discard"
          />
          <Button
            variant="solid"
            :label="__('Fill the ticked ones')"
            :disabled="!Object.values(kept).some(Boolean)"
            :loading="busy === 'apply'"
            @click="apply"
          />
        </template>
      </div>
    </template>
  </Dialog>
</template>

<script setup>
import {
  Button,
  Checkbox,
  Dialog,
  ErrorMessage,
  Textarea,
  call,
  toast,
} from 'frappe-ui'
import { reactive, ref, watch } from 'vue'

const props = defineProps({ record: { type: String, default: null } })
const emit = defineEmits(['filled'])
const show = defineModel({ type: Boolean })

const text = ref('')
const proposals = ref(null)
const event = ref(null)
const kept = reactive({})
const busy = ref('')
const error = ref('')

watch(show, (open) => {
  if (!open) return
  text.value = ''
  proposals.value = null
  event.value = null
  error.value = ''
  for (const key of Object.keys(kept)) delete kept[key]
})

function show_(value) {
  if (value === true) return __('Yes')
  if (value === false) return __('No')
  if (Array.isArray(value)) return value.join(', ')
  if (value && typeof value === 'object') return JSON.stringify(value)
  return String(value ?? '')
}

async function propose() {
  busy.value = 'propose'
  error.value = ''
  try {
    const done = await call('crm.clinica.dettatura.propose_answers', {
      record: props.record,
      text: text.value,
    })
    event.value = done.event
    if (done.error) {
      error.value = __('The assistant did not answer: {0}', [done.error])
      return
    }
    proposals.value = done.proposals
    // ticked by default, except what is confirmed one by one
    for (const proposal of done.proposals) {
      kept[proposal.field] = !proposal.one_by_one
    }
  } catch (e) {
    error.value = e.messages?.join(' ') || e.message
  } finally {
    busy.value = ''
  }
}

async function apply() {
  busy.value = 'apply'
  error.value = ''
  try {
    const answers = Object.fromEntries(
      proposals.value
        .filter((proposal) => kept[proposal.field])
        .map((proposal) => [proposal.field, proposal.value]),
    )
    await call('crm.clinica.dettatura.apply_answers', {
      event: event.value,
      answers: JSON.stringify(answers),
    })
    toast.success(__('Filled: check the sheet, then sign it'))
    show.value = false
    emit('filled')
  } catch (e) {
    error.value = e.messages?.join(' ') || e.message
  } finally {
    busy.value = ''
  }
}

async function discard() {
  busy.value = 'discard'
  try {
    if (event.value) {
      await call('crm.clinica.dettatura.discard', { event: event.value })
    }
  } catch {
    /* thrown away all the same */
  } finally {
    busy.value = ''
    show.value = false
  }
}
</script>
