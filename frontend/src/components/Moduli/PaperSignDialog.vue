<!--
  Signing on paper: print the form as filled, have it signed, upload the scan,
  and attest it is a true copy of the original signed in front of you. The
  scan goes inside the form's PDF/A, with its SHA-256.
-->
<template>
  <Dialog v-model="show" :options="{ title: __('Sign on paper'), size: 'lg' }">
    <template #body-content>
      <ol class="flex flex-col gap-5">
        <li class="flex gap-3">
          <span
            class="grid size-6 flex-none place-items-center rounded-full bg-surface-gray-2 text-xs font-semibold text-ink-gray-7"
            >1</span
          >
          <div class="flex min-w-0 flex-1 flex-col gap-2">
            <span class="text-base font-medium text-ink-gray-8">
              {{ __('Print it with the answers so far') }}
            </span>
            <span class="text-p-sm text-ink-gray-5">
              {{
                __(
                  'The person reads it, completes it if needed, and signs where the lines are.',
                )
              }}
            </span>
            <Button
              class="w-fit"
              icon-left="printer"
              :label="__('Print the form')"
              :loading="printing"
              @click="print"
            />
          </div>
        </li>
        <li class="flex gap-3">
          <span
            class="grid size-6 flex-none place-items-center rounded-full bg-surface-gray-2 text-xs font-semibold text-ink-gray-7"
            >2</span
          >
          <div class="flex min-w-0 flex-1 flex-col gap-2">
            <span class="text-base font-medium text-ink-gray-8">
              {{ __('Upload the signed paper, scanned') }}
            </span>
            <span class="text-p-sm text-ink-gray-5">
              {{
                __(
                  'A PDF, a JPG or a PNG. The answers here must be the ones on the paper.',
                )
              }}
            </span>
            <FileUploader
              :uploadArgs="{
                doctype: 'CRM Form',
                docname: formId,
                private: true,
              }"
              :validateFile="validate"
              @success="(file) => (scan = file)"
            >
              <template #default="{ openFileSelector, uploading, progress }">
                <div class="flex min-w-0 flex-wrap items-center gap-2">
                  <Button
                    icon-left="upload"
                    :label="
                      uploading
                        ? __('Uploading {0}%', [progress])
                        : scan
                          ? __('Upload another')
                          : __('Upload the scan')
                    "
                    @click="openFileSelector"
                  />
                  <span
                    v-if="scan"
                    class="min-w-0 truncate text-sm text-ink-gray-7"
                  >
                    {{ scan.file_name }}
                  </span>
                </div>
              </template>
            </FileUploader>
          </div>
        </li>
        <li class="flex gap-3">
          <span
            class="grid size-6 flex-none place-items-center rounded-full bg-surface-gray-2 text-xs font-semibold text-ink-gray-7"
            >3</span
          >
          <label class="flex min-w-0 flex-1 cursor-pointer items-start gap-2">
            <Checkbox v-model="attest" class="touch-target mt-0.5 shrink-0" />
            <span class="text-base text-ink-gray-8">
              {{
                __(
                  'I attest that the scan is a true copy of the original, signed in front of me.',
                )
              }}
              <span class="block text-sm text-ink-gray-5">
                {{ __('The original on paper stays with the centre.') }}
              </span>
            </span>
          </label>
        </li>
      </ol>
      <ErrorMessage class="mt-4" :message="error" />
    </template>
    <template #actions>
      <div class="dialog-footer flex justify-end gap-2">
        <Button :label="__('Cancel')" @click="show = false" />
        <Button
          variant="solid"
          :label="__('Signed on paper')"
          :disabled="!scan || !attest"
          :loading="signing"
          @click="sign"
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
  FileUploader,
  call,
} from 'frappe-ui'
import { ref } from 'vue'

const props = defineProps({
  formId: { type: String, required: true },
  // the answers and who answers for the person, as on the page now
  answers: { type: Object, required: true },
  givenBy: { type: String, default: null },
})
const emit = defineEmits(['signed'])
const show = defineModel({ type: Boolean })

const scan = ref(null)
const attest = ref(false)
const error = ref('')
const printing = ref(false)
const signing = ref(false)

const KINDS = ['pdf', 'png', 'jpg', 'jpeg']

function validate(file) {
  const kind = (file.name.split('.').pop() || '').toLowerCase()
  if (!KINDS.includes(kind)) return __('The scan is a PDF, a JPG or a PNG')
}

async function print() {
  printing.value = true
  error.value = ''
  try {
    // what is printed is what is saved: save first
    await call('crm.moduli.compilazioni.save_answers', {
      name: props.formId,
      answers: JSON.stringify(props.answers),
    })
    window.open(
      `/api/method/crm.moduli.compilazioni.printable_form?name=${encodeURIComponent(props.formId)}`,
      '_blank',
    )
  } catch (e) {
    error.value = e.messages?.join(' ') || e.message
  } finally {
    printing.value = false
  }
}

async function sign() {
  signing.value = true
  error.value = ''
  try {
    const form = await call('crm.moduli.compilazioni.sign_on_paper', {
      name: props.formId,
      answers: JSON.stringify(props.answers),
      scan: scan.value.file_url,
      attest: 1,
      given_by: props.givenBy || '',
    })
    show.value = false
    emit('signed', form)
  } catch (e) {
    error.value = e.messages?.join(' ') || e.message
  } finally {
    signing.value = false
  }
}
</script>
