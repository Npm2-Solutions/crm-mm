<!--
  The list, kept beside the record you are reading.

  Without it, answering five people means five trips back to the list, and each
  trip loses your place in it. With it the record page is the third pane of an
  inbox: who wrote, what they said, and the one you are answering — all at once,
  which is what every mail client has looked like for thirty years.

  And it behaves like a chat list, because that is what it is: newest
  conversation first, a search, and the same two questions the Inbox answers —
  everybody, or only the ones still waiting.

  It is opt-in and it is remembered, because the same page is also used to read
  one person's file on a narrow screen, and a column stealing a third of the
  width is wrong there.
-->
<template>
  <div
    class="flex w-72 shrink-0 flex-col overflow-hidden border-r bg-surface-white"
  >
    <div class="flex h-[45px] shrink-0 items-center gap-2 border-b px-3">
      <span class="text-base font-medium text-ink-gray-8">
        {{ __('People') }}
      </span>
      <Badge
        v-if="waitingCount"
        :label="String(waitingCount)"
        theme="green"
        size="sm"
      />
      <Button
        class="ml-auto"
        variant="ghost"
        icon="lucide-panel-left-close"
        :tooltip="__('Hide the list')"
        @click="emit('close')"
      />
    </div>

    <div class="flex shrink-0 flex-col gap-2 border-b px-3 py-2">
      <!-- A name, a company, a number: whichever one somebody remembers. -->
      <TextInput
        v-model="search"
        type="text"
        :placeholder="__('Search')"
        @input="searchLater"
      >
        <template #prefix>
          <LucideSearch class="size-4 text-ink-gray-4" />
        </template>
      </TextInput>
      <div class="flex items-center gap-2">
        <div class="flex flex-1 items-center rounded bg-surface-gray-2 p-0.5">
          <button
            v-for="choice in CHOICES"
            :key="String(choice.value)"
            class="flex-1 rounded px-2 py-1 text-sm transition-colors"
            :class="
              waitingOnly === choice.value
                ? 'bg-surface-white text-ink-gray-9 shadow-sm'
                : 'text-ink-gray-6 hover:text-ink-gray-8'
            "
            @click="waitingOnly = choice.value"
          >
            {{ __(choice.label) }}
          </button>
        </div>
        <!-- the same filter builder the list uses, on the same doctype: one way
           of saying «only the ones from Facebook», not a second one -->
        <!--
          Read-only into Filter on purpose. It only ever *reads* the list — the
          rows and the filters currently on them — and answers with the filters
          somebody built. Handing it the resource with v-model would be asking
          to be assigned a const.
        -->
        <Filter
          :modelValue="asList"
          doctype="CRM Lead"
          :hideLabel="true"
          @update="applyFilters"
        />
      </div>
    </div>

    <div class="flex-1 overflow-y-auto" @scroll="onScroll">
      <ConversationList
        :rows="rows"
        :unread="unread.data || {}"
        :active="active"
        doctype="CRM Lead"
        @open="open"
      />
      <div
        v-if="people.loading"
        class="flex justify-center py-4 text-ink-gray-4"
      >
        <LoadingIndicator class="size-4" />
      </div>
      <div
        v-else-if="!rows.length"
        class="px-3 py-6 text-center text-p-sm text-ink-gray-4"
      >
        {{
          search || waitingOnly
            ? __('Nobody matches that')
            : __('No people yet')
        }}
      </div>
    </div>
  </div>
</template>

<script setup>
import ConversationList from '@/components/ConversationList.vue'
import Filter from '@/components/Filter.vue'
import LucideSearch from '~icons/lucide/search'
import { globalStore } from '@/stores/global'
import { usePeopleSidebar } from '@/composables/usePeopleSidebar'
import {
  Badge,
  LoadingIndicator,
  TextInput,
  createResource,
  debounce,
} from 'frappe-ui'
import { computed, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { useRouter } from 'vue-router'

const props = defineProps({
  // the record being read, so the column can show where you are
  active: { type: String, default: '' },
})

const emit = defineEmits(['close'])

const router = useRouter()
const { $socket } = globalStore()

const CHOICES = [
  { value: false, label: 'All' },
  { value: true, label: 'Waiting' },
]

const search = ref('')
// remembered across records, unlike the search: «only the ones waiting» is how
// somebody is working this morning, and retyping it on every person opened
// would make it not worth setting
const { waitingOnly } = usePeopleSidebar()
const filters = ref({})
const pageLength = ref(30)

// One endpoint rather than the generic list one: a search across a name, a
// company and a number is an OR across three columns, which a list of AND
// filters cannot say — somebody typing a surname was told there was nobody.
const people = createResource({
  url: 'crm.api.conversations.people',
  makeParams: () => ({
    search: search.value,
    waiting: waitingOnly.value ? 1 : 0,
    filters: filters.value,
    limit: pageLength.value,
  }),
  auto: true,
})

const rows = computed(() => people.data || [])

const unread = createResource({
  url: 'crm.api.conversations.unread',
  makeParams: () => ({
    records: rows.value.map((row) => ['CRM Lead', row.name]),
  }),
})

// what Filter needs to see: the rows it is filtering, and the filters already on
// them, so it opens showing what is in force
const asList = computed(() => ({
  data: rows.value,
  params: { filters: filters.value },
}))

const waitingCount = computed(
  () => rows.value.filter((row) => row.conversation_unread).length,
)

watch(
  () => rows.value.map((row) => row.name).join(','),
  (names) => names && unread.fetch(),
  { immediate: true },
)

// typing is not a request per keystroke
const searchLater = debounce(() => {
  pageLength.value = 30
  people.reload()
}, 300)

watch(waitingOnly, () => {
  pageLength.value = 30
  people.reload()
})

function applyFilters(chosen) {
  filters.value = chosen || {}
  pageLength.value = 30
  people.reload()
}

function open(row) {
  if (row.name === props.active) return
  router.push({ name: 'Lead', params: { leadId: row.name } })
}

function onScroll(event) {
  const { scrollTop, scrollHeight, clientHeight } = event.target
  if (scrollHeight - scrollTop - clientHeight > 120) return
  if (people.loading) return
  if (rows.value.length < pageLength.value) return
  pageLength.value += 30
  people.reload()
}

// somebody wrote: this column is an inbox, so it has to move
function refresh() {
  people.reload()
}

onMounted(() => {
  $socket.on('crm_sms_message', refresh)
  $socket.on('whatsapp_message', refresh)
})

onBeforeUnmount(() => {
  $socket.off('crm_sms_message', refresh)
  $socket.off('whatsapp_message', refresh)
})
</script>
