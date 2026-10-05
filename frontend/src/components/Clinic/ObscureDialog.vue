<!--
  Obscuring an episode at the patient's request, or revealing it again: the
  medical director's. Obscured, a visit (with its addenda and reports) or a
  document leaves the dossier: its author and the director still read it, and
  nobody else can tell it exists. The request and its note go in the audit log.
-->
<template>
  <Dialog
    v-model="show"
    :options="{
      title: obscured
        ? __('Reveal again')
        : __('Obscure at the patient\'s request'),
      size: 'md',
    }"
  >
    <template #body-content>
      <div class="flex flex-col gap-3">
        <!-- what it is on its own line: glued into the sentence, a note
             without a title read «Nota esce dal dossier» -->
        <div v-if="title" class="flex flex-col gap-0.5">
          <span class="text-base-medium text-ink-gray-8">{{ title }}</span>
          <span v-if="about" class="text-p-sm text-ink-gray-6">
            {{ about }}
          </span>
        </div>
        <p class="text-p-base text-ink-gray-7">
          {{
            obscured
              ? __(
                  'It goes back into the dossier: the care team reads it again, as before.',
                )
              : __(
                  'It leaves the dossier. Its author and you still read it; the other practitioners will not know it exists. A visit takes its addenda and reports with it.',
                )
          }}
        </p>
        <FormControl
          v-model="note"
          type="textarea"
          :rows="2"
          :label="__('The patient\'s request')"
          :placeholder="__('When and how it arrived: in writing, at the desk…')"
        />
        <ErrorMessage :message="error" />
      </div>
    </template>
    <template #actions>
      <div class="dialog-footer flex justify-end gap-2">
        <Button :label="__('Cancel')" @click="show = false" />
        <Button
          variant="solid"
          :label="obscured ? __('Reveal') : __('Obscure')"
          :loading="busy"
          @click="apply"
        />
      </div>
    </template>
  </Dialog>
</template>

<script setup>
import { Button, Dialog, ErrorMessage, FormControl, call } from 'frappe-ui'
import { ref, watch } from 'vue'

const props = defineProps({
  doctype: { type: String, required: true },
  name: { type: String, default: null },
  title: { type: String, default: '' },
  // when and by whom, under the title
  about: { type: String, default: '' },
  obscured: { type: Boolean, default: false },
})
const emit = defineEmits(['done'])
const show = defineModel({ type: Boolean })

const note = ref('')
const error = ref('')
const busy = ref(false)

watch(show, (open) => {
  if (open) {
    note.value = ''
    error.value = ''
  }
})

async function apply() {
  busy.value = true
  error.value = ''
  try {
    await call(
      props.obscured
        ? 'crm.clinica.dossier.reveal'
        : 'crm.clinica.dossier.obscure',
      { doctype: props.doctype, name: props.name, note: note.value },
    )
    show.value = false
    emit('done')
  } catch (e) {
    error.value = e.messages?.join(' ') || e.message
  } finally {
    busy.value = false
  }
}
</script>
