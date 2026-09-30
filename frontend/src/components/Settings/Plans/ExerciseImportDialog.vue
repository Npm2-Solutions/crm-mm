<!--
  exercises-dataset into the library: 1,324 exercises, how they are done in
  Italian step by step, the names in English to rename here. The data are MIT;
  the pictures © Gym visual, authorised to NPM2 Solutions, shown only from where
  the agency hosts them. Imported again, the pictures and the muscles are the
  dataset's, the words stay the centre's.
-->
<template>
  <Dialog
    v-model="show"
    :options="{ title: __('Import exercises'), size: 'lg' }"
  >
    <template #body-content>
      <div v-if="!result" class="flex flex-col gap-3">
        <p class="text-p-base text-ink-gray-7">
          {{
            __(
              'exercises-dataset: 1,324 exercises with how they are done, step by step, in Italian. The names are in English: rename them here when a trainer has read them.',
            )
          }}
        </p>
        <p class="text-p-sm text-ink-gray-6">
          {{
            __(
              'The data are under the MIT licence. The animations and pictures are © Gym visual, which authorised NPM2 Solutions: they appear only where the agency hosts them, and the assistant never uses them.',
            )
          }}
        </p>
        <p
          class="rounded-md px-3 py-2 text-p-sm"
          :class="
            hasMedia
              ? 'bg-surface-gray-2 text-ink-gray-7'
              : 'bg-surface-amber-1 text-ink-amber-8'
          "
        >
          {{
            hasMedia
              ? __('The pictures come from where the agency hosts them.')
              : __(
                  'No pictures yet: the agency says where it hosts them, and they appear without importing again.',
                )
          }}
        </p>
        <FileUploader
          :file-types="['.json']"
          :upload-args="{ private: true }"
          @success="(file) => (fileUrl = file.file_url)"
        >
          <template #default="{ openFileSelector, uploading, progress }">
            <div class="flex flex-wrap items-center gap-3">
              <Button
                icon-left="upload"
                :loading="uploading"
                :label="
                  uploading
                    ? __('Uploading {0}%', [progress])
                    : __('Upload exercises.json')
                "
                @click="openFileSelector()"
              />
              <span class="min-w-0 text-p-sm text-ink-gray-6">
                {{
                  fileUrl
                    ? fileUrl.split('/').pop()
                    : __('Without a file it is downloaded from GitHub.')
                }}
              </span>
            </div>
          </template>
        </FileUploader>
        <ErrorMessage :message="error" />
      </div>
      <div v-else class="flex flex-col gap-2">
        <p class="text-p-base text-ink-gray-8">
          {{
            __('{0} exercises added, {1} updated.', [
              result.created,
              result.updated,
            ])
          }}
        </p>
      </div>
    </template>
    <template #actions>
      <div class="dialog-footer flex justify-end gap-2">
        <Button
          v-if="!result"
          variant="solid"
          :label="__('Import')"
          :loading="busy"
          @click="importExercises"
        />
        <Button v-else :label="__('Done')" @click="show = false" />
      </div>
    </template>
  </Dialog>
</template>

<script setup>
import { Button, Dialog, ErrorMessage, FileUploader, call } from 'frappe-ui'
import { ref, watch } from 'vue'

defineProps({ hasMedia: { type: Boolean, default: false } })
const emit = defineEmits(['imported'])
const show = defineModel({ type: Boolean })

const fileUrl = ref('')
const busy = ref(false)
const error = ref('')
const result = ref(null)

watch(show, (open) => {
  if (!open) return
  fileUrl.value = ''
  error.value = ''
  result.value = null
})

async function importExercises() {
  busy.value = true
  error.value = ''
  try {
    result.value = await call('crm.piani.librerie.import_exercises', {
      file_url: fileUrl.value || null,
    })
    emit('imported')
  } catch (e) {
    error.value = e.messages?.join(' ') || e.message
  } finally {
    busy.value = false
  }
}
</script>
