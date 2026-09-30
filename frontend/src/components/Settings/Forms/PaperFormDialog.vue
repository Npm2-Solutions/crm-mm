<!--
  A form from paper: the PDF the centre already prints, read by the assistant,
  proposed as fields to check. Nothing is saved but a draft, and only when the
  person building it says so; the register keeps what they changed.
-->
<template>
  <Dialog
    v-model="show"
    :options="{ title: __('From a paper form'), size: '3xl' }"
  >
    <template #body-content>
      <div class="flex flex-col gap-4">
        <p
          class="rounded-md bg-surface-gray-2 px-3 py-2 text-p-sm text-ink-gray-7"
        >
          {{
            __(
              'The assistant reads the PDF and proposes the fields, with the words of the paper. You check them here and in the builder: nothing is published by the assistant.',
            )
          }}
        </p>

        <template v-if="!proposal">
          <FileUploader
            :file-types="['application/pdf']"
            :upload-args="{ private: true }"
            @success="(file) => (fileUrl = file.file_url)"
          >
            <template #default="{ openFileSelector, uploading, progress }">
              <div class="flex flex-wrap items-center gap-3">
                <Button
                  :label="
                    uploading
                      ? __('Uploading {0}%', [progress])
                      : __('Choose the PDF')
                  "
                  icon-left="upload"
                  :loading="uploading"
                  @click="openFileSelector()"
                />
                <span
                  v-if="fileUrl"
                  class="min-w-0 truncate text-p-sm text-ink-gray-6"
                >
                  {{ fileUrl.split('/').pop() }}
                </span>
              </div>
            </template>
          </FileUploader>
        </template>

        <template v-else>
          <FormControl v-model="title" :label="__('Title')" />
          <div
            v-if="proposal.problems?.length"
            class="flex flex-col gap-1 rounded-md bg-surface-amber-1 px-3 py-2 text-p-sm text-ink-amber-8"
          >
            <span class="font-medium">
              {{ __('Still to put right in the builder') }}
            </span>
            <span v-for="(problem, i) in proposal.problems" :key="i">
              {{ problem.message || problem }}
            </span>
          </div>
          <div
            class="max-h-[50vh] overflow-y-auto rounded-md border border-outline-gray-2 p-4"
          >
            <FormRenderer :schema="proposal.schema" readonly />
          </div>
        </template>
        <ErrorMessage :message="error" />
      </div>
    </template>
    <template #actions>
      <div class="dialog-footer flex flex-wrap justify-end gap-2">
        <template v-if="!proposal">
          <Button :label="__('Cancel')" @click="show = false" />
          <Button
            variant="solid"
            :label="__('Read it')"
            :disabled="!fileUrl"
            :loading="busy"
            @click="read"
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
            :label="__('Create the draft')"
            :loading="busy === 'create'"
            @click="create"
          />
        </template>
      </div>
    </template>
  </Dialog>
</template>

<script setup>
import FormRenderer from '@/components/Moduli/FormRenderer.vue'
import {
  Button,
  Dialog,
  ErrorMessage,
  FileUploader,
  FormControl,
  call,
} from 'frappe-ui'
import { ref, watch } from 'vue'

const emit = defineEmits(['created'])
const show = defineModel({ type: Boolean })

const fileUrl = ref('')
const proposal = ref(null)
const title = ref('')
const busy = ref(false)
const error = ref('')

watch(show, (open) => {
  if (!open) return
  fileUrl.value = ''
  proposal.value = null
  title.value = ''
  busy.value = false
  error.value = ''
})

async function read() {
  busy.value = true
  error.value = ''
  try {
    const done = await call('crm.assistente.modulo_di_carta.propose', {
      file_url: fileUrl.value,
    })
    if (done.error) {
      error.value = __('The assistant did not answer: {0}', [done.error])
      return
    }
    proposal.value = done
    title.value = done.title || ''
  } catch (e) {
    error.value = e.messages?.join(' ') || e.message
  } finally {
    busy.value = false
  }
}

async function create() {
  busy.value = 'create'
  error.value = ''
  try {
    const done = await call('crm.assistente.modulo_di_carta.create_draft', {
      event: proposal.value.event,
      title: title.value,
      schema: JSON.stringify(proposal.value.schema),
    })
    show.value = false
    emit('created', done.template)
  } catch (e) {
    error.value = e.messages?.join(' ') || e.message
  } finally {
    busy.value = false
  }
}

async function discard() {
  busy.value = 'discard'
  try {
    await call('crm.assistente.modulo_di_carta.discard', {
      event: proposal.value.event,
    })
  } catch {
    /* thrown away all the same */
  } finally {
    busy.value = false
    show.value = false
  }
}
</script>
