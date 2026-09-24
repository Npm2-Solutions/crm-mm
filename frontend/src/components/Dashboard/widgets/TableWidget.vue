<template>
  <div class="flex h-full flex-col">
    <div
      v-if="!rows.length"
      class="flex flex-1 items-center justify-center px-6 pb-6 text-center text-sm text-ink-gray-5"
    >
      {{ answer.empty || __('Nothing here') }}
    </div>
    <div v-else class="min-h-0 flex-1 overflow-auto px-2 pb-2">
      <table class="w-full border-separate border-spacing-0 text-sm">
        <thead class="sticky top-0 z-[1] bg-surface-elevation-1">
          <tr>
            <th
              v-for="column in answer.columns"
              :key="column.key"
              scope="col"
              class="whitespace-nowrap border-b border-outline-gray-1 px-2 py-1.5 text-xs font-medium text-ink-gray-5"
              :class="numeric(column) ? 'text-right' : 'text-left'"
            >
              {{ column.label }}
            </th>
          </tr>
        </thead>
        <tbody>
          <tr
            v-for="(row, index) in rows"
            :key="index"
            class="hover:bg-surface-gray-1"
          >
            <td
              v-for="column in answer.columns"
              :key="column.key"
              class="border-b border-outline-gray-1 px-2 py-1.5"
              :class="
                numeric(column)
                  ? 'text-right tabular-nums text-ink-gray-8'
                  : 'text-ink-gray-8'
              "
            >
              <span
                v-if="column.format === 'user'"
                class="flex min-w-0 items-center gap-2"
              >
                <UserAvatar
                  :user="row[column.key]"
                  size="sm"
                  class="shrink-0"
                />
                <span class="truncate">{{
                  row.name ||
                  getUser(row[column.key])?.full_name ||
                  row[column.key]
                }}</span>
              </span>
              <span v-else-if="numeric(column)">
                {{ cell(row[column.key], column) }}
              </span>
              <span
                v-else
                class="block max-w-64 truncate"
                :title="row[column.key]"
              >
                {{ row[column.key] || '–' }}
              </span>
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

<script setup>
import UserAvatar from '@/components/UserAvatar.vue'
import { usersStore } from '@/stores/users'
import { formatValue } from '@/utils/dashboard'
import { computed } from 'vue'

const props = defineProps({
  answer: { type: Object, required: true },
  locale: { type: String, default: undefined },
})

const { getUser } = usersStore()

const rows = computed(() => props.answer.rows || [])

function numeric(column) {
  return !['text', 'user'].includes(column.format)
}

function cell(value, column) {
  if (value == null) return '–'
  return formatValue(value, column.format, {
    locale: props.locale,
    currency: props.answer.currency,
    compact: false,
  })
}
</script>
