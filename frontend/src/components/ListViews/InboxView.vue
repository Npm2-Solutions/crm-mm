<!--
  People, read as conversations.

  This is the List view's sibling, not a different page: the rows come from the
  same resource, with the same filters and the same saved view. Only the order
  and the shape of a row change — which is the whole difference between a
  directory and an inbox.
-->
<template>
  <div class="flex flex-1 flex-col overflow-hidden">
    <div ref="scroller" class="flex-1 overflow-y-auto" @scroll="onScroll">
      <div class="mx-auto w-full max-w-3xl divide-y divide-outline-gray-1">
        <ConversationList
          :rows="rows"
          :unread="unread.data || {}"
          doctype="CRM Lead"
          @open="(row) => emit('open', row)"
        />
      </div>
      <div
        v-if="!rows.length && !loading"
        class="flex h-full flex-col items-center justify-center gap-2 text-ink-gray-4"
      >
        <InboxIcon class="h-8 w-8" />
        <span class="text-lg font-medium">{{ __('Nothing here') }}</span>
        <span class="text-sm">
          {{ __('Conversations appear here as soon as somebody writes.') }}
        </span>
      </div>
    </div>
  </div>
</template>

<script setup>
import ConversationList from '@/components/ConversationList.vue'
import InboxIcon from '@/components/Icons/InboxIcon.vue'
import { globalStore } from '@/stores/global'
import { createResource } from 'frappe-ui'
import { computed, onBeforeUnmount, onMounted, ref, watch } from 'vue'

const props = defineProps({
  rows: { type: Array, default: () => [] },
  loading: { type: Boolean, default: false },
})

const emit = defineEmits(['open', 'loadMore'])

const { $socket } = globalStore()
const scroller = ref(null)

// How many each person is waiting on, asked for the rows on screen and nobody
// else. A count over the whole table would be a query that grows with the CRM
// to answer a question about twenty rows.
const unread = createResource({
  url: 'crm.api.conversations.unread',
  makeParams: () => ({
    records: props.rows.map((row) => ['CRM Lead', row.name]),
  }),
})

const names = computed(() => props.rows.map((row) => row.name).join(','))
watch(names, () => props.rows.length && unread.fetch(), { immediate: true })

function onScroll(event) {
  const { scrollTop, scrollHeight, clientHeight } = event.target
  if (scrollHeight - scrollTop - clientHeight < 120) emit('loadMore')
}

// A message arriving changes the order of this list, so it has to be told
function refresh() {
  unread.fetch()
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
