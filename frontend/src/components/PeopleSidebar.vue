<!--
  The list, kept beside the record you are reading.

  Without it, answering five people means five trips back to the list, and each
  trip loses your place in it. With it the record page is the third pane of an
  inbox: who wrote, what they said, and the one you are answering — all at once,
  which is what every mail client has looked like for thirty years.

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
    </div>
  </div>
</template>

<script setup>
import ConversationList from '@/components/ConversationList.vue'
import { globalStore } from '@/stores/global'
import { Badge, LoadingIndicator, createResource } from 'frappe-ui'
import { computed, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { useRouter } from 'vue-router'

const props = defineProps({
  // the record being read, so the column can show where you are
  active: { type: String, default: '' },
  // «all» or «waiting» — the same two questions the Inbox view answers
  waiting: { type: Boolean, default: false },
})

const emit = defineEmits(['close'])

const router = useRouter()
const { $socket } = globalStore()

const pageLength = ref(30)

const ROWS = [
  'name',
  'lead_name',
  'first_name',
  'last_name',
  'image',
  'organization',
  'last_conversation_on',
  'last_conversation_channel',
  'last_conversation_direction',
  'last_conversation_preview',
  'conversation_unread',
]

const people = createResource({
  url: 'crm.api.doc.get_data',
  makeParams: () => ({
    doctype: 'CRM Lead',
    filters: props.waiting ? { conversation_unread: 1 } : {},
    order_by: 'last_conversation_on desc',
    rows: JSON.stringify(ROWS),
    page_length: pageLength.value,
    page_length_count: pageLength.value,
  }),
  auto: true,
})

const rows = computed(() => people.data?.data || [])

const unread = createResource({
  url: 'crm.api.conversations.unread',
  makeParams: () => ({
    records: rows.value.map((row) => ['CRM Lead', row.name]),
  }),
})

const waitingCount = computed(
  () => rows.value.filter((row) => row.conversation_unread).length,
)

watch(
  () => rows.value.map((row) => row.name).join(','),
  (names) => names && unread.fetch(),
  { immediate: true },
)

watch(
  () => props.waiting,
  () => people.reload(),
)

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
