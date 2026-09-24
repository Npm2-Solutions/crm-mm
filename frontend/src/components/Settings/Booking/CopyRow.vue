<template>
  <div class="flex flex-col gap-1">
    <span class="text-xs text-ink-gray-5">{{ label }}</span>
    <div class="flex items-center gap-2">
      <code
        class="min-w-0 flex-1 truncate rounded bg-surface-gray-2 px-2 py-1.5 text-p-sm text-ink-gray-7"
      >
        {{ value }}
      </code>
      <Button variant="ghost" icon="lucide-copy" @click="copy" />
    </div>
  </div>
</template>

<script setup>
import { toast } from 'frappe-ui'

const props = defineProps({
  label: { type: String, default: '' },
  value: { type: String, default: '' },
})

async function copy() {
  try {
    await navigator.clipboard.writeText(props.value)
    toast.success(__('Copied'))
  } catch {
    toast.error(props.value)
  }
}
</script>
