<!--
  The left column: which conversation you are reading, and how to find it.

  A chat list, so it behaves like one — the base view is everything still going
  on, with whoever is waiting at the top, and a search that looks wherever a
  name might be.

  The other views live behind a selector rather than beside it. Four chips in a
  320px column could only ever carry four words, so the questions an inbox is
  actually asked — who is waiting for an answer, what is mine, what nobody has
  picked up — had nowhere to go. A selector holds as many as are worth having,
  says how many are in each, and leaves the column to the conversations.
-->
<template>
  <div
    class="flex w-full shrink-0 flex-col overflow-hidden bg-surface-white sm:w-80 sm:border-r"
  >
    <div class="flex shrink-0 flex-col gap-2 border-b px-3 py-2.5">
      <Dropdown :options="viewOptions" placement="left">
        <template #default="{ open }">
          <button
            class="flex w-full items-center gap-2 rounded px-1.5 py-1 text-left transition-colors hover:bg-surface-gray-2"
          >
            <span
              class="min-w-0 truncate text-base font-medium text-ink-gray-8"
            >
              {{ __(labelOf(view)) }}
            </span>
            <span v-if="countOf(view)" class="text-p-sm text-ink-gray-5">
              {{ countOf(view) }}
            </span>
            <component
              :is="open ? LucideChevronUp : LucideChevronDown"
              class="ml-auto size-4 shrink-0 text-ink-gray-5"
            />
          </button>
        </template>
      </Dropdown>
      <TextInput
        v-model="search"
        type="text"
        :placeholder="__('Search a name, a company, a number')"
      >
        <template #prefix>
          <LucideSearch class="size-4 text-ink-gray-4" />
        </template>
      </TextInput>
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
import LucideChevronDown from '~icons/lucide/chevron-down'
import LucideChevronUp from '~icons/lucide/chevron-up'
import LucideSearch from '~icons/lucide/search'
import { Dropdown, LoadingIndicator, TextInput } from 'frappe-ui'
import { computed } from 'vue'

const props = defineProps({
  rows: { type: Array, default: () => [] },
  unread: { type: Object, default: () => ({}) },
  // how many are in each view, for the numbers in the selector
  counts: { type: Object, default: () => ({}) },
  loading: { type: Boolean, default: false },
  active: { type: String, default: '' },
})

const emit = defineEmits(['open', 'loadMore'])

const view = defineModel('view', { type: String, default: 'open' })
const search = defineModel('search', { type: String, default: '' })

// «Waiting for a reply» is not «unread»: you can have read something this
// morning and still owe the answer, and that one is what costs money. Keeping
// both is the whole reason this is a selector and not a switch.
const VIEWS = [
  { value: 'open', label: 'Open' },
  { value: 'unanswered', label: 'Waiting for a reply' },
  { value: 'unread', label: 'Unread' },
  { value: 'mine', label: 'Assigned to me' },
  { value: 'unassigned', label: 'Nobody assigned' },
  { value: 'snoozed', label: 'Put off until later' },
  { value: 'handled', label: 'Dealt with' },
  { value: 'all', label: 'Everything' },
]

function labelOf(which) {
  return VIEWS.find((one) => one.value === which)?.label || 'Open'
}

function countOf(which) {
  return props.counts?.[which] || 0
}

const viewOptions = computed(() =>
  VIEWS.map((one) => ({
    label: countOf(one.value)
      ? `${__(one.label)} · ${countOf(one.value)}`
      : __(one.label),
    onClick: () => (view.value = one.value),
  })),
)

// An empty list means something different in every view, and «nothing found»
// would be wrong in most of them.
const empty = computed(() => {
  if (search.value) return __('Nobody matches that')
  if (view.value === 'open')
    return __('Nothing open. Everything is dealt with.')
  if (view.value === 'unanswered') return __('Nobody is waiting for an answer')
  if (view.value === 'unread') return __('Nothing left to read')
  if (view.value === 'mine') return __('Nothing assigned to you')
  if (view.value === 'unassigned') return __('Everything has somebody on it')
  if (view.value === 'snoozed') return __('Nothing put off for later')
  if (view.value === 'handled') return __('Nothing dealt with yet')
  return __('No conversations yet')
})

function onScroll(event) {
  const { scrollTop, scrollHeight, clientHeight } = event.target
  if (scrollHeight - scrollTop - clientHeight < 160) emit('loadMore')
}
</script>
