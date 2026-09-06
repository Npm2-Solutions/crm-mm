<template>
  <div class="mx-auto flex w-full max-w-3xl flex-col gap-3 px-4 py-6">
    <div class="flex items-center justify-between">
      <div class="flex flex-wrap gap-1.5">
        <Button
          v-for="status in STATUSES"
          :key="status"
          size="sm"
          :variant="filter === status ? 'solid' : 'outline'"
          :label="__(status)"
          @click="((filter = status), enrollments.reload())"
        />
      </div>
      <Button
        variant="ghost"
        icon="lucide-refresh-cw"
        :label="__('Refresh')"
        @click="enrollments.reload()"
      />
    </div>

    <div
      v-if="enrollments.data?.length"
      class="divide-y divide-outline-gray-1 rounded-lg border border-outline-gray-2"
    >
      <div v-for="row in enrollments.data" :key="row.name">
        <button
          class="flex w-full items-center gap-3 px-3 py-2 text-left hover:bg-surface-gray-1"
          @click="toggle(row)"
        >
          <FeatherIcon
            :name="expanded === row.name ? 'chevron-down' : 'chevron-right'"
            class="size-4 shrink-0 text-ink-gray-5"
          />
          <span class="min-w-0 flex-1 truncate text-base text-ink-gray-8">
            {{ row.title || row.reference_name }}
          </span>
          <span class="shrink-0 text-xs text-ink-gray-5">
            {{ dayjs(row.modified).fromNow() }}
          </span>
          <Badge
            size="sm"
            :theme="THEMES[row.status]"
            :label="__(row.status)"
          />
        </button>

        <div
          v-if="expanded === row.name"
          class="border-t border-outline-gray-1 bg-surface-gray-1 px-4 py-3"
        >
          <div v-if="detail.loading" class="text-sm text-ink-gray-5">
            {{ __('Loading…') }}
          </div>
          <ol v-else class="flex flex-col gap-2">
            <li
              v-for="(log, index) in detail.data?.logs || []"
              :key="index"
              class="flex items-start gap-2 text-sm"
            >
              <FeatherIcon
                :name="LOG_ICONS[log.status] || 'circle'"
                class="mt-0.5 size-3.5 shrink-0"
                :class="LOG_COLORS[log.status]"
              />
              <div class="min-w-0 flex-1">
                <span class="font-medium text-ink-gray-7">
                  {{ stepLabel(log.action) }}
                </span>
                <span class="text-ink-gray-5"> — {{ log.detail }}</span>
              </div>
              <span class="shrink-0 text-xs text-ink-gray-4">
                {{ dayjs(log.creation).format('DD/MM HH:mm') }}
              </span>
            </li>
            <li
              v-if="!(detail.data?.logs || []).length"
              class="text-sm text-ink-gray-5"
            >
              {{ __('No steps have run yet.') }}
            </li>
          </ol>
        </div>
      </div>
    </div>
    <div v-else class="py-8 text-center text-sm text-ink-gray-4">
      {{ __('No records have been enrolled yet.') }}
    </div>
  </div>
</template>

<script setup>
import { Badge, Button, FeatherIcon, createResource, dayjs } from 'frappe-ui'
import { ref } from 'vue'
import { stepLabel } from '@/utils/automation'

const props = defineProps({
  automation: { type: String, required: true },
})

const STATUSES = ['All', 'Active', 'Waiting', 'Completed', 'Exited', 'Failed']

const THEMES = {
  Active: 'blue',
  Waiting: 'orange',
  Completed: 'green',
  Exited: 'gray',
  Failed: 'red',
}

const LOG_ICONS = {
  Success: 'check-circle',
  Failed: 'alert-triangle',
  Skipped: 'corner-down-right',
}

const LOG_COLORS = {
  Success: 'text-ink-green-3',
  Failed: 'text-ink-red-3',
  Skipped: 'text-ink-gray-5',
}

const filter = ref('All')
const expanded = ref(null)

const enrollments = createResource({
  url: 'crm.api.automation.get_enrollments',
  makeParams: () => ({ automation: props.automation, status: filter.value }),
  auto: true,
})

const detail = createResource({
  url: 'crm.api.automation.get_enrollment_detail',
  makeParams: () => ({ name: expanded.value }),
})

function toggle(row) {
  if (expanded.value === row.name) {
    expanded.value = null
    return
  }
  expanded.value = row.name
  detail.fetch()
}
</script>
