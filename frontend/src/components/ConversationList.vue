<!--
  The people, in the order they last said something.

  One row, one person: who, when, the last thing said and by whom, and whether
  anything is waiting. Everything else about them is one click away, in the
  conversation itself.

  The time is a messenger's time — the clock today, «Ieri», the weekday this
  week, the date after that. It was «3 days ago» on every row, which says the
  same thing forty times and never which of two rows came first.
-->
<template>
  <div class="flex flex-col py-1">
    <button
      v-for="row in rows"
      :key="row.name"
      class="mx-1.5 flex items-center gap-3 rounded-lg px-2.5 py-2.5 text-left transition-colors"
      :class="
        row.name === active ? 'bg-surface-gray-3' : 'hover:bg-surface-gray-2'
      "
      :aria-current="row.name === active ? 'true' : undefined"
      @click="emit('open', row)"
    >
      <PersonAvatar :name="titleOf(row)" :image="row.image" size="lg" />
      <div class="min-w-0 flex-1">
        <div class="flex items-baseline gap-2">
          <span
            class="min-w-0 flex-1 truncate text-base"
            :class="
              isUnread(row)
                ? 'font-semibold text-ink-gray-9'
                : 'font-medium text-ink-gray-8'
            "
          >
            {{ titleOf(row) }}
          </span>
          <!-- a conversation put off says when it comes back instead -->
          <span
            v-if="row.conversation_snoozed_until"
            class="flex shrink-0 items-center gap-1 text-p-xs text-ink-orange-8"
          >
            <span class="lucide-clock size-3" aria-hidden="true" />
            {{ later(row.conversation_snoozed_until) }}
          </span>
          <span
            v-else-if="row.last_conversation_on"
            class="shrink-0 text-p-xs tabular-nums"
            :class="
              isUnread(row) ? 'font-medium text-ink-blue-8' : 'text-ink-gray-5'
            "
          >
            {{ when(row.last_conversation_on) }}
          </span>
        </div>
        <div class="mt-0.5 flex items-center gap-1.5">
          <component
            :is="channelIcon(row.last_conversation_channel)"
            v-if="row.last_conversation_channel"
            class="size-3.5 shrink-0 text-ink-gray-5"
          />
          <span
            class="min-w-0 flex-1 truncate text-p-sm"
            :class="isUnread(row) ? 'text-ink-gray-8' : 'text-ink-gray-5'"
          >
            <span
              v-if="row.last_conversation_direction === 'Outgoing'"
              class="text-ink-gray-5"
            >
              {{ __('You') }}:
            </span>
            {{ row.last_conversation_preview || noWordsYet(row) }}
          </span>
          <!-- whose it is, when it is somebody's -->
          <Tooltip
            v-if="row.conversation_assigned_to"
            :text="
              __('Assigned to {0}', [nameOf(row.conversation_assigned_to)])
            "
          >
            <span class="shrink-0">
              <UserAvatar :user="row.conversation_assigned_to" size="xs" />
            </span>
          </Tooltip>
          <!--
            The count, and only when there is one to give. A badge showing «0»
            is a badge saying nothing, and a row with nothing waiting should
            look like a row with nothing waiting.
          -->
          <span
            v-if="waiting(row)"
            class="flex h-5 min-w-5 shrink-0 items-center justify-center rounded-full bg-surface-blue-7 px-1.5 text-2xs font-semibold tabular-nums text-ink-base"
          >
            {{ waiting(row) }}
          </span>
          <span
            v-else-if="row.conversation_unread"
            class="size-2.5 shrink-0 rounded-full bg-surface-blue-7"
            :aria-label="__('Unread')"
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
import PersonAvatar from '@/components/Conversations/PersonAvatar.vue'
import UserAvatar from '@/components/UserAvatar.vue'
import { usersStore } from '@/stores/users'
import { laterLabel, listTime } from '@/utils/conversation'
import { Tooltip, dayjsLocal } from 'frappe-ui'

const props = defineProps({
  rows: { type: Array, default: () => [] },
  // how many messages each person is waiting on, keyed «doctype:name»
  unread: { type: Object, default: () => ({}) },
  doctype: { type: String, default: 'CRM Lead' },
  // the one being read, so the column says where you are
  active: { type: String, default: '' },
})

const emit = defineEmits(['open'])

const { getUser } = usersStore()

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

function nameOf(user) {
  return getUser(user)?.full_name || user
}

// the server's clock, moved onto the reader's before it is compared with now
function local(at) {
  return dayjsLocal(at).format('YYYY-MM-DD HH:mm:ss')
}

function when(at) {
  return listTime(local(at), dayjsLocal().format('YYYY-MM-DD HH:mm:ss'))
}

function later(at) {
  return laterLabel(local(at), dayjsLocal().format('YYYY-MM-DD HH:mm:ss'))
}

// A person with no conversation is not an error: it is most of the list on the
// first day. Saying so is better than an empty line that looks like a failure.
function noWordsYet(row) {
  return row.last_conversation_on ? '' : __('No messages yet')
}

function waiting(row) {
  return props.unread[`${props.doctype}:${row.name}`] || 0
}

function isUnread(row) {
  return Boolean(row.conversation_unread || waiting(row))
}
</script>
