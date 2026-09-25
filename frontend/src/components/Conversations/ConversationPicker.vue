<!--
  The left column: which conversation you are reading, and how to find it.

  A chat list, so it behaves like one — newest first, a search that looks
  wherever a name might be, and four chips for the four questions somebody
  actually asks of a pile of conversations.
-->
<template>
  <div
    class="flex w-full shrink-0 flex-col overflow-hidden bg-surface-white sm:w-80 sm:border-r"
  >
    <div class="flex shrink-0 flex-col gap-2 border-b px-3 py-2.5">
      <TextInput
        v-model="search"
        type="text"
        :placeholder="__('Search a name, a company, a number')"
      >
        <template #prefix>
          <LucideSearch class="size-4 text-ink-gray-4" />
        </template>
      </TextInput>
      <div class="flex items-center rounded bg-surface-gray-2 p-0.5">
        <button
          v-for="choice in STATES"
          :key="choice.value"
          class="flex-1 rounded px-2 py-1 text-sm transition-colors"
          :class="
            state === choice.value
              ? 'bg-surface-white text-ink-gray-9 shadow-sm'
              : 'text-ink-gray-6 hover:text-ink-gray-8'
          "
          @click="state = choice.value"
        >
          {{ __(choice.label) }}
        </button>
      </div>
    </div>

    <div class="flex-1 overflow-y-auto" @scroll="onScroll">
      <ConversationList
        :rows="rows"
        :unread="unread"
        :active="active"
        doctype="CRM Lead"
        @open="(row) => emit('open', row)"
      />
      <div v-if="loading" class="flex justify-center py-4 text-ink-gray-4">
        <LoadingIndicator class="size-4" />
      </div>
      <div
        v-else-if="!rows.length"
        class="px-4 py-8 text-center text-p-sm text-ink-gray-4"
      >
        {{ empty }}
      </div>
    </div>
  </div>
</template>

<script setup>
import ConversationList from '@/components/ConversationList.vue'
import LucideSearch from '~icons/lucide/search'
import { LoadingIndicator, TextInput } from 'frappe-ui'
import { computed } from 'vue'

defineProps({
  rows: { type: Array, default: () => [] },
  unread: { type: Object, default: () => ({}) },
  loading: { type: Boolean, default: false },
  active: { type: String, default: '' },
})

const emit = defineEmits(['open', 'loadMore'])

const state = defineModel('state', { type: String, default: 'open' })
const search = defineModel('search', { type: String, default: '' })

// Open is the default because it is the pile: what is left when you take away
// what has been dealt with and what was put off on purpose.
const STATES = [
  { value: 'open', label: 'Open' },
  { value: 'snoozed', label: 'Snoozed' },
  { value: 'handled', label: 'Handled' },
  { value: 'all', label: 'All' },
]

// An empty list means four different things here, and «nothing found» would be
// wrong for three of them.
const empty = computed(() => {
  if (search.value) return __('Nobody matches that')
  if (state.value === 'open')
    return __('Nothing open. Everything is dealt with.')
  if (state.value === 'snoozed') return __('Nothing put off for later')
  if (state.value === 'handled') return __('Nothing dealt with yet')
  return __('No conversations yet')
})

function onScroll(event) {
  const { scrollTop, scrollHeight, clientHeight } = event.target
  if (scrollHeight - scrollTop - clientHeight < 160) emit('loadMore')
}
</script>
