<!--
  The people, in the order they last said something.

  The same rows serve two places, because they are the same list: the Inbox view
  of People, and the column beside a record that lets you walk from one person to
  the next without going back to the list. Writing them twice would have meant
  two ideas of what a conversation row is, and they would have drifted apart by
  the second change.
-->
<template>
  <div class="flex flex-col">
    <button
      v-for="row in rows"
      :key="row.name"
      class="flex w-full items-center gap-3 border-l-2 px-3 py-2.5 text-left transition-colors"
      :class="
        row.name === active
          ? 'border-outline-gray-4 bg-surface-gray-2'
          : 'border-transparent hover:bg-surface-gray-1'
      "
      @click="emit('open', row)"
    >
      <Avatar
        size="lg"
        class="shrink-0"
        :label="titleOf(row)"
        :image="row.image || row.organization_logo"
      />
      <div class="min-w-0 flex-1">
        <div class="flex items-baseline gap-2">
          <span
            class="truncate text-base text-ink-gray-9"
            :class="row.conversation_unread ? 'font-semibold' : 'font-medium'"
          >
            {{ titleOf(row) }}
          </span>
          <span
            v-if="row.last_conversation_on"
            class="ml-auto shrink-0 text-xs"
            :class="
              row.conversation_unread ? 'text-ink-gray-7' : 'text-ink-gray-4'
            "
          >
            {{ timeAgo(row.last_conversation_on) }}
          </span>
        </div>
        <div class="mt-0.5 flex items-center gap-1.5">
          <component
            :is="channelIcon(row.last_conversation_channel)"
            v-if="row.last_conversation_channel"
            class="size-3 shrink-0 text-ink-gray-4"
          />
          <span
            class="truncate text-sm"
            :class="
              row.conversation_unread ? 'text-ink-gray-8' : 'text-ink-gray-5'
            "
          >
            <span
              v-if="row.last_conversation_direction === 'Outgoing'"
              class="text-ink-gray-4"
            >
              {{ __('You') }}:
            </span>
            {{ row.last_conversation_preview || noWordsYet(row) }}
          </span>
          <!--
            The count, and only when there is one to give. A badge showing «0»
            is a badge saying nothing, and a row with nothing waiting should
            look like a row with nothing waiting.
          -->
          <span
            v-if="waiting(row)"
            class="ml-auto shrink-0 rounded-full bg-surface-green-3 px-1.5 text-xs font-medium tabular-nums text-ink-white"
          >
            {{ waiting(row) }}
          </span>
          <span
            v-else-if="row.conversation_unread"
            class="ml-auto size-2 shrink-0 rounded-full bg-surface-green-3"
          />
        </div>
      </div>
    </button>
  </div>
</template>

<script setup>
import WhatsAppIcon from '@/components/Icons/WhatsAppIcon.vue'
import SMSIcon from '@/components/Icons/SMSIcon.vue'
import Email2Icon from '@/components/Icons/Email2Icon.vue'
import DotIcon from '@/components/Icons/DotIcon.vue'
import { timeAgo } from '@/utils'
import { Avatar } from 'frappe-ui'

const props = defineProps({
  rows: { type: Array, default: () => [] },
  // how many messages each person is waiting on, keyed «doctype:name»
  unread: { type: Object, default: () => ({}) },
  doctype: { type: String, default: 'CRM Lead' },
  // the one being read, so the column says where you are
  active: { type: String, default: '' },
})

const emit = defineEmits(['open'])

const ICONS = {
  WhatsApp: WhatsAppIcon,
  SMS: SMSIcon,
  Email: Email2Icon,
}

function channelIcon(channel) {
  return ICONS[channel] || DotIcon
}

function titleOf(row) {
  return (
    row.lead_name ||
    row.organization ||
    [row.first_name, row.last_name].filter(Boolean).join(' ') ||
    row.name
  )
}

// A person with no conversation is not an error: it is most of the list on the
// first day. Saying so is better than an empty line that looks like a failure.
function noWordsYet(row) {
  return row.last_conversation_on ? '' : __('No messages yet')
}

function waiting(row) {
  return props.unread[`${props.doctype}:${row.name}`] || 0
}
</script>
