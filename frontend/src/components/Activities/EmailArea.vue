<!--
  Modifications copyright (c) 2026, NPM2 Solutions Srl
-->
<template>
  <!--
    Bare means this is sitting inside the house bubble, which already draws the
    card, the sender and the clock. What stays is what only an email has: the
    subject, who else it went to, the body, and the two reply buttons — losing
    those would push anybody who lives in «All» back out to the email view to
    answer a message they are already reading.
  -->
  <div
    class="flex flex-col text-base transition-all duration-300 ease-in-out"
    :class="
      bare
        ? ''
        : 'cursor-pointer rounded-md bg-surface-elevation-1 px-3 py-1.5 shadow-sm'
    "
  >
    <div
      class="-mb-0.5 flex items-center justify-between gap-2 truncate text-ink-gray-9"
    >
      <div class="flex items-center gap-2 truncate">
        <span v-if="!bare">{{ activity.data.sender_full_name }}</span>
        <span v-if="!bare" class="sm:flex hidden text-sm text-ink-gray-5">
          {{ '<' + activity.data.sender + '>' }}
        </span>
        <Badge
          v-if="activity.communication_type == 'Automated Message'"
          :label="__('Notification')"
          variant="subtle"
          theme="green"
        />
      </div>
      <div class="flex items-center gap-2 shrink-0">
        <Badge
          v-if="status.label"
          :label="__(status.label)"
          variant="subtle"
          :theme="status.color"
        />
        <TimelineTimestamp v-if="!bare" :date="activity.communication_date" />
        <div v-if="puo('conversazioni.usa')" class="flex gap-0.5">
          <Button
            :tooltip="__('Reply', null, 'Answer a message')"
            :aria-label="__('Reply', null, 'Answer a message')"
            variant="ghost"
            class="text-ink-gray-7"
            :icon="ReplyIcon"
            @click="reply(activity.data)"
          />
          <Button
            :tooltip="__('Reply All')"
            :aria-label="__('Reply All')"
            variant="ghost"
            :icon="ReplyAllIcon"
            class="text-ink-gray-7"
            @click="reply(activity.data, true)"
          />
        </div>
      </div>
    </div>
    <div class="flex flex-col gap-1 text-base leading-5 text-ink-gray-8">
      <div>{{ activity.data.subject }}</div>
      <div>
        <span class="mr-1 text-ink-gray-5"> {{ __('To') }}: </span>
        <span>{{ activity.data.recipients }}</span>
        <span v-if="activity.data.cc">, </span>
        <span v-if="activity.data.cc" class="mr-1 text-ink-gray-5">
          {{ __('CC') }}:
        </span>
        <span v-if="activity.data.cc">{{ activity.data.cc }}</span>
        <span v-if="activity.data.bcc">, </span>
        <span v-if="activity.data.bcc" class="mr-1 text-ink-gray-5">
          {{ __('BCC') }}:
        </span>
        <span v-if="activity.data.bcc">{{ activity.data.bcc }}</span>
      </div>
    </div>
    <div class="border-0 border-t mt-3 mb-1 border-outline-elevation-2" />
    <EmailContent :content="activity.data.content" />
    <div v-if="activity.data?.attachments?.length" class="flex flex-wrap gap-2">
      <AttachmentItem
        v-for="a in activity.data.attachments"
        :key="a.file_url"
        :label="a.file_name"
        :url="a.file_url"
      />
    </div>
  </div>
</template>
<script setup>
import ReplyIcon from '@/components/Icons/ReplyIcon.vue'
import ReplyAllIcon from '@/components/Icons/ReplyAllIcon.vue'
import AttachmentItem from '@/components/AttachmentItem.vue'
import EmailContent from '@/components/Activities/EmailContent.vue'
import { Badge } from 'frappe-ui'
import TimelineTimestamp from '@/components/Activities/TimelineTimestamp.vue'
import { usersStore } from '@/stores/users'
import { computed } from 'vue'

const props = defineProps({
  activity: { type: Object, default: () => ({}) },
  emailBox: { type: Object, default: () => ({}) },
  // the house bubble draws the card, the sender and the clock in the mixed chat
  bare: { type: Boolean, default: false },
})

const { puo } = usersStore()

// The composer knows who a reply goes to and from which mailbox; this only
// says which email, and whether to everybody on it.
function reply(email, all = false) {
  props.emailBox?.reply?.(email, all)
}

const status = computed(() => {
  let _status = props.activity?.data?.delivery_status
  let indicator_color = 'red'
  if (['Sent', 'Clicked'].includes(_status)) {
    indicator_color = 'green'
  } else if (['Sending', 'Scheduled'].includes(_status)) {
    indicator_color = 'orange'
  } else if (['Opened', 'Read'].includes(_status)) {
    indicator_color = 'blue'
  } else if (_status == 'Error') {
    indicator_color = 'red'
  }
  return { label: _status, color: indicator_color }
})
</script>
