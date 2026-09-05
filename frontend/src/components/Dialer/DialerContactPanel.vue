<template>
  <div class="flex flex-col gap-5">
    <!-- who is on the line -->
    <div>
      <div class="flex items-start justify-between gap-3">
        <div class="min-w-0">
          <div class="text-base font-medium text-ink-gray-9 truncate">
            {{ context?.display_name || context?.number }}
          </div>
          <div class="text-sm text-ink-gray-5">{{ context?.number }}</div>
        </div>
        <Badge
          v-if="record?.status"
          :label="record.status"
          variant="subtle"
          theme="gray"
        />
      </div>

      <dl v-if="record" class="mt-3 flex flex-col gap-1.5">
        <div
          v-for="row in recordRows"
          :key="row.label"
          class="flex gap-2 text-sm"
        >
          <dt class="w-24 shrink-0 text-ink-gray-5">{{ row.label }}</dt>
          <dd class="min-w-0 truncate text-ink-gray-8">{{ row.value }}</dd>
        </div>
      </dl>
      <p v-else class="mt-3 text-sm text-ink-gray-5">
        {{ __('This number is not linked to a lead or a deal.') }}
      </p>
    </div>

    <!-- what is already booked -->
    <div>
      <div class="mb-2 flex items-center justify-between">
        <span class="text-sm font-medium text-ink-gray-7">
          {{ __('Appointments') }}
        </span>
        <Button
          size="sm"
          :label="__('Book')"
          :disabled="!record"
          :tooltip="
            record ? undefined : __('Link the call to a lead or deal to book')
          "
          @click="emit('book')"
        >
          <template #prefix>
            <FeatherIcon name="calendar" class="h-3.5 w-3.5" />
          </template>
        </Button>
      </div>
      <div
        v-if="context?.appointments?.length"
        class="divide-y divide-outline-gray-1 rounded-md border border-outline-gray-2"
      >
        <div
          v-for="a in context.appointments"
          :key="a.name"
          class="flex items-center justify-between gap-2 px-2.5 py-2 text-sm"
        >
          <span class="min-w-0 truncate text-ink-gray-8">
            {{ a.title || a.service }}
          </span>
          <span class="shrink-0 text-xs text-ink-gray-5">
            {{ formatDate(a.starts_on, 'D MMM, HH:mm') }}
          </span>
        </div>
      </div>
      <p v-else class="text-sm text-ink-gray-5">
        {{ __('Nothing booked yet.') }}
      </p>
    </div>

    <!-- how the conversation has gone so far -->
    <div v-if="context?.recent_calls?.length">
      <div class="mb-2 text-sm font-medium text-ink-gray-7">
        {{ __('Recent calls') }}
      </div>
      <div
        class="divide-y divide-outline-gray-1 rounded-md border border-outline-gray-2"
      >
        <div
          v-for="c in context.recent_calls"
          :key="c.name"
          class="flex items-center justify-between gap-2 px-2.5 py-2 text-sm"
        >
          <span class="flex min-w-0 items-center gap-1.5">
            <FeatherIcon
              :name="
                c.type === 'Incoming' ? 'phone-incoming' : 'phone-outgoing'
              "
              class="h-3.5 w-3.5 shrink-0 text-ink-gray-5"
            />
            <span class="truncate text-ink-gray-8">{{ __(c.status) }}</span>
            <FeatherIcon
              v-if="c.transcription_status === 'Completed'"
              name="file-text"
              class="h-3.5 w-3.5 shrink-0 text-ink-gray-4"
              :title="__('Transcribed')"
            />
          </span>
          <span class="shrink-0 text-xs text-ink-gray-5">
            {{ formatDate(c.creation, 'D MMM, HH:mm') }}
          </span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { formatDate } from '@/utils'
import { Badge, FeatherIcon } from 'frappe-ui'
import { computed } from 'vue'

const props = defineProps({
  context: { type: Object, default: null },
})

const emit = defineEmits(['book'])

const record = computed(() => props.context?.record || null)

const recordRows = computed(() => {
  const r = record.value
  if (!r) return []
  return [
    { label: __('Organisation'), value: r.organization },
    { label: __('Email'), value: r.email },
    { label: __('Mobile'), value: r.mobile_no },
    { label: __('Owner'), value: r.lead_owner || r.deal_owner },
  ].filter((row) => row.value)
})
</script>
