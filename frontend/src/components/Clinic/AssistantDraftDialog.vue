<!--
  Copyright (c) 2026, NPM2 Solutions Srl and contributors
  For license information, please see license.txt

  A draft from one's signed note: a letter to the family doctor, or the
  instructions after the visit. The assistant writes only what the note says and
  leaves gaps in square brackets; the practitioner reads it, corrects it, and
  keeps it as a note added to the visit, which they sign like any note.
-->
<template>
  <Dialog v-model="show" :options="{ title: title, size: '3xl' }">
    <template #body-content>
      <div class="flex flex-col gap-3">
        <p
          class="rounded-md bg-surface-gray-2 px-3 py-2 text-p-sm text-ink-gray-7"
        >
          {{
            __(
              'An AI draft from your signed note: read it, correct it, fill the gaps in square brackets. Kept, it becomes a note added to the visit, with the mark of who checked it, and you sign it like any note.',
            )
          }}
        </p>
        <div
          v-if="busy === 'draft'"
          class="py-10 text-center text-p-sm text-ink-gray-5"
        >
          {{ __('The assistant is writing from your note…') }}
        </div>
        <template v-else-if="event">
          <Textarea v-model="text" :rows="14" />
          <p v-if="gaps" class="text-p-sm text-ink-amber-8">
            {{ __('{0} gaps in square brackets still to fill', [gaps]) }}
          </p>
          <label
            v-if="kind === 'instructions' && canPost"
            class="flex items-start gap-2"
          >
            <Checkbox v-model="post" class="touch-target mt-0.5 shrink-0" />
            <span class="text-base text-ink-gray-8">
              {{ __('Also post them on the patient’s board in their area') }}
            </span>
          </label>
        </template>
        <ErrorMessage :message="error" />
      </div>
    </template>
    <template #actions>
      <div class="dialog-footer flex flex-wrap justify-end gap-2">
        <Button
          v-if="event && !failed"
          :label="__('Discard')"
          :loading="busy === 'discard'"
          @click="discard"
        />
        <Button v-else :label="__('Close')" @click="show = false" />
        <Button
          v-if="event && !failed"
          variant="solid"
          :label="__('Keep as a note')"
          :disabled="!text.trim()"
          :loading="busy === 'keep'"
          @click="keep"
        />
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
import { computed, ref, watch } from 'vue'

const props = defineProps({
  record: { type: String, default: null },
  // 'letter' or 'instructions'
  kind: { type: String, default: 'letter' },
  canPost: { type: Boolean, default: false },
})
const emit = defineEmits(['kept'])
const show = defineModel({ type: Boolean })

const event = ref(null)
const text = ref('')
const post = ref(false)
const busy = ref('')
const error = ref('')
const failed = ref(false)

const title = computed(() =>
  props.kind === 'letter'
    ? __('A letter to the family doctor')
    : __('Instructions after the visit'),
)
const gaps = computed(() => (text.value.match(/\[[^\]]+\]/g) || []).length)

watch(show, async (open) => {
  if (!open) return
  event.value = null
  text.value = ''
  post.value = false
  error.value = ''
  failed.value = false
  busy.value = 'draft'
  try {
    const done = await call('crm.clinica.assistente.draft_from_note', {
      record: props.record,
      kind: props.kind,
    })
    event.value = done.event
    text.value = done.draft || ''
    if (done.error) {
      failed.value = true
      error.value = done.error
    }
  } catch (e) {
    error.value = e.messages?.join(' ') || e.message
  } finally {
    busy.value = ''
  }
})

async function keep() {
  busy.value = 'keep'
  error.value = ''
  try {
    const done = await call('crm.clinica.assistente.keep_draft', {
      event: event.value,
      text: text.value,
      post_to_area: post.value ? 1 : 0,
    })
    toast.success(
      done.posted
        ? __('Kept as a note to sign, and posted in the area')
        : __('Kept as a note to sign'),
    )
    show.value = false
    emit('kept')
  } catch (e) {
    error.value = e.messages?.join(' ') || e.message
  } finally {
    busy.value = ''
  }
}

async function discard() {
  busy.value = 'discard'
  try {
    await call('crm.clinica.assistente.discard_draft', { event: event.value })
  } catch {
    /* thrown away all the same */
  } finally {
    busy.value = ''
    show.value = false
  }
}
</script>
