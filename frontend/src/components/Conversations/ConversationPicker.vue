<!--
  Copyright (c) 2026, NPM2 Solutions Srl and contributors
  For license information, please see license.txt

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
    class="flex w-full shrink-0 flex-col overflow-hidden bg-surface-base sm:w-80 sm:border-r"
  >
    <div class="flex shrink-0 flex-col gap-2 px-3 pb-2 pt-2.5">
      <div class="flex min-w-0 items-center justify-between gap-2">
        <Dropdown :options="viewOptions" placement="left">
          <template #default="{ open }">
            <button
              class="flex max-w-full items-center gap-1.5 rounded-md px-1.5 py-1 text-left transition-colors hover:bg-surface-gray-2"
            >
              <span
                class="min-w-0 truncate text-lg font-semibold text-ink-gray-9"
              >
                {{ __(labelOf(view), null, VISTA) }}
              </span>
              <span
                v-if="countOf(view) && !search"
                class="shrink-0 rounded-full bg-surface-gray-2 px-1.5 text-p-xs font-medium tabular-nums text-ink-gray-6"
              >
                {{ countOf(view) }}
              </span>
              <!-- while searching, the view is not what is on screen: a name
                 you type is looked for everywhere, so saying «Aperte» would
                 be a lie -->
              <span
                v-if="search"
                class="shrink-0 text-p-xs italic text-ink-gray-5"
              >
                {{ __('everywhere') }}
              </span>
              <component
                :is="open ? LucideChevronUp : LucideChevronDown"
                class="size-4 shrink-0 text-ink-gray-5"
              />
            </button>
          </template>
        </Dropdown>
        <!--
          Unread is not a view but a filter over the one open: the unread among
          the open, among the parked, among the handled. It narrows a view,
          never a search — a name typed is somebody wanted, read or not.
        -->
        <Tooltip
          v-if="!search"
          :text="__('Only the ones with something nobody here has read yet')"
        >
          <button
            class="flex shrink-0 items-center gap-1.5 rounded-full px-2.5 py-1 text-p-sm font-medium transition-colors"
            :class="
              onlyUnread
                ? 'bg-surface-blue-2 text-ink-blue-8 ring-1 ring-outline-blue-2'
                : 'text-ink-gray-6 hover:bg-surface-gray-2'
            "
            :aria-pressed="onlyUnread ? 'true' : 'false'"
            @click="onlyUnread = !onlyUnread"
          >
            <span
              class="size-2 shrink-0 rounded-full bg-surface-blue-7"
              aria-hidden="true"
            />
            {{ __('Unread') }}
            <span v-if="unreadIn(view)" class="tabular-nums">
              {{ unreadIn(view) }}
            </span>
          </button>
        </Tooltip>
      </div>
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

    <div ref="contenitore" class="flex-1 overflow-y-auto" @scroll="onScroll">
      <TiraPerAggiornare v-bind="tira" />
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
        class="flex flex-col items-center gap-2 px-6 py-10 text-center"
      >
        <span
          class="lucide-message-circle-check size-6 text-ink-gray-4"
          aria-hidden="true"
        />
        <span class="text-p-sm text-ink-gray-5">{{ empty }}</span>
      </div>
    </div>
  </div>
</template>

<script setup>
import ConversationList from '@/components/ConversationList.vue'
import TiraPerAggiornare from '@/components/Mobile/TiraPerAggiornare.vue'
import { useTiraPerAggiornare } from '@/composables/tiraPerAggiornare'
import LucideChevronDown from '~icons/lucide/chevron-down'
import LucideChevronUp from '~icons/lucide/chevron-up'
import LucideSearch from '~icons/lucide/search'
import { Dropdown, LoadingIndicator, TextInput, Tooltip } from 'frappe-ui'
import { computed, ref } from 'vue'

const props = defineProps({
  rows: { type: Array, default: () => [] },
  unread: { type: Object, default: () => ({}) },
  // how many are in each view, for the numbers in the selector
  counts: { type: Object, default: () => ({}) },
  loading: { type: Boolean, default: false },
  active: { type: String, default: '' },
  // the list pulled down from its top on a phone: what reloads it, a promise
  aggiorna: { type: Function, default: null },
})

const emit = defineEmits(['open', 'loadMore'])

const contenitore = ref(null)
const tira = useTiraPerAggiornare(contenitore, () => props.aggiorna?.())

const view = defineModel('view', { type: String, default: 'open' })
const search = defineModel('search', { type: String, default: '' })
const onlyUnread = defineModel('onlyUnread', { type: Boolean, default: false })

// Four. A fifth would be a way of asking something these four already answer,
// and a menu you have to read is a menu that slows you down every morning.
//
// «Waiting for a reply» is not «unread»: you can have read something this
// morning and still owe the answer, and that one is what costs money. Unread
// is the filter beside the selector, over whichever of these is open. Put off
// and handled are here because without them the two buttons in the header
// would make a conversation vanish with no way back to it — and each line says
// what brings a conversation back out of it, which is the question somebody
// has when they cannot find one.
const VIEWS = [
  { value: 'open', label: 'Open', about: 'Everything still going on' },
  {
    value: 'unanswered',
    label: 'Waiting for a reply',
    about: 'They wrote last',
  },
  {
    value: 'snoozed',
    label: 'Put off until later',
    about: 'Back at the time chosen, or when they write',
  },
  {
    value: 'handled',
    label: 'Handled',
    about: 'Back in Open as soon as they write',
  },
]

// a view names many conversations: «Gestite», where the header says «Gestita»
const VISTA = 'Conversation view'

function labelOf(which) {
  return VIEWS.find((one) => one.value === which)?.label || 'Open'
}

function countOf(which) {
  return props.counts?.[which] || 0
}

function unreadIn(which) {
  return props.counts?.[`${which}_unread`] || 0
}

const viewOptions = computed(() =>
  VIEWS.map((one) => ({
    label: countOf(one.value)
      ? `${__(one.label, null, VISTA)} · ${countOf(one.value)}`
      : __(one.label, null, VISTA),
    description: __(one.about),
    selected: one.value === view.value,
    onClick: () => (view.value = one.value),
  })),
)

// An empty list means something different in every view, and «nothing found»
// would be wrong in most of them.
const empty = computed(() => {
  if (search.value) return __('Nobody matches that')
  if (onlyUnread.value) return __('Nothing unread here')
  if (view.value === 'unanswered') return __('Nobody is waiting for an answer')
  if (view.value === 'snoozed') return __('Nothing put off for later')
  if (view.value === 'handled') return __('Nothing handled yet')
  return __('Nothing open. Everything is handled.')
})

function onScroll(event) {
  const { scrollTop, scrollHeight, clientHeight } = event.target
  if (scrollHeight - scrollTop - clientHeight < 160) emit('loadMore')
}
</script>
