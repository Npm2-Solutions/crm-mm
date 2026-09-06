<template>
  <div class="flex flex-col gap-1.5">
    <span class="text-xs text-ink-gray-5">{{ label }}</span>
    <div class="flex items-center gap-3">
      <img
        v-if="url"
        :src="url"
        alt=""
        class="size-14 rounded-lg border border-outline-gray-2 object-contain p-1"
      />
      <div
        v-else
        class="size-14 rounded-lg border border-dashed border-outline-gray-2"
      />
      <div class="flex flex-col gap-1">
        <FileUploader
          :fileTypes="['image/*']"
          :validateFile="validate"
          @success="(file) => emit('update', file.file_url)"
        >
          <template #default="{ openFileSelector, uploading }">
            <Button
              :loading="uploading"
              :label="url ? __('Replace') : __('Upload')"
              @click="openFileSelector"
            />
          </template>
        </FileUploader>
        <Button
          v-if="url"
          variant="ghost"
          size="sm"
          :label="__('Remove')"
          @click="emit('update', '')"
        />
      </div>
    </div>
  </div>
</template>

<script setup>
import { FileUploader } from 'frappe-ui'

defineProps({
  label: { type: String, default: '' },
  url: { type: String, default: '' },
})

const emit = defineEmits(['update'])

// Uploads land public by default, which is what a website image has to be — a private
// File would 403 for every visitor. Size is capped so a 12 MB photo never becomes a hero.
function validate(file) {
  if (file.size > 5 * 1024 * 1024) return __('Images must be under 5 MB')
}
</script>
