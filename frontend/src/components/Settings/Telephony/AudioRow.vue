<template>
  <div class="flex items-start justify-between gap-8 py-3 pl-2 pr-1">
    <div class="flex flex-col min-w-0">
      <div class="text-p-base-medium text-ink-gray-7">{{ label }}</div>
      <div v-if="description" class="text-p-sm text-ink-gray-5">
        {{ description }}
      </div>
      <a
        v-if="url"
        :href="url"
        target="_blank"
        rel="noopener"
        class="mt-1 truncate text-p-sm text-ink-blue-3 hover:underline"
      >
        {{ fileName }}
      </a>
    </div>
    <div class="flex shrink-0 items-center gap-1">
      <FileUploader
        :upload-args="{ private: false, folder: 'Home/Attachments' }"
        :validateFile="validateIsAudioFile"
        @success="(file) => emit('picked', file.file_url)"
      >
        <template #default="{ openFileSelector, uploading, progress, error }">
          <div class="flex items-center gap-2">
            <ErrorMessage :message="error" />
            <Button
              :loading="uploading"
              :label="
                uploading ? `${progress}%` : url ? __('Replace') : __('Upload')
              "
              @click="openFileSelector()"
            />
          </div>
        </template>
      </FileUploader>
      <Button
        v-if="url"
        icon="x"
        variant="ghost"
        :tooltip="__('Remove')"
        @click="emit('cleared')"
      />
    </div>
  </div>
</template>

<script setup>
import { ErrorMessage, FileUploader } from 'frappe-ui'
import { computed } from 'vue'

const props = defineProps({
  label: { type: String, default: '' },
  description: { type: String, default: '' },
  url: { type: String, default: '' },
})

const emit = defineEmits(['picked', 'cleared'])

const fileName = computed(() => props.url?.split('/').pop() || props.url || '')

function validateIsAudioFile(file) {
  const extension = file.name.split('.').pop().toLowerCase()
  if (!['mp3', 'wav'].includes(extension)) {
    return __('Only MP3 and WAV files can be played to callers')
  }
}
</script>
