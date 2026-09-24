<template>
  <div
    v-if="title !== 'Data'"
    class="flex items-center justify-between text-lg-medium sm:mx-10 sm:mb-4 sm:mt-8"
  >
    <div class="flex h-8 items-center text-2xl-semibold text-ink-gray-8">
      {{ __(title) }}
    </div>
    <!--
      The channel picker. It changes the stream *and* the box underneath: picking
      WhatsApp and then typing into an email composer was the whole reason the
      four tabs existed.
    -->
    <div v-if="title == 'Activity'" class="flex items-center gap-2">
      <div
        class="flex items-center gap-0.5 rounded-lg bg-surface-gray-2 p-0.5 text-p-sm"
      >
        <button
          v-for="option in channelOptions"
          :key="option.key"
          class="flex items-center gap-1.5 rounded-md px-2 py-1"
          :class="
            channel === option.key
              ? 'bg-surface-white text-ink-gray-8 shadow-sm'
              : 'text-ink-gray-6 hover:text-ink-gray-8'
          "
          @click="channel = option.key"
        >
          <component :is="option.icon" v-if="option.icon" class="size-3.5" />
          <span>{{ __(option.label) }}</span>
          <span v-if="option.count" class="text-ink-gray-4">
            {{ option.count }}
          </span>
        </button>
      </div>
      <!-- templates are the only way to open a conversation that has gone cold
           past 24 hours, so the button belongs beside the WhatsApp channel -->
      <Button
        v-if="channel === 'whatsapp'"
        :label="__('Send Template')"
        @click="showWhatsappTemplates = true"
      />
      <Button
        variant="solid"
        iconLeft="plus"
        :label="__(newLabel)"
        @click="startNew"
      />
    </div>
    <MultiActionButton
      v-else-if="title == 'Calls'"
      variant="solid"
      :options="callActions"
    />
    <Button
      v-else-if="title == 'Events'"
      variant="solid"
      @click="modalRef.showEvent()"
    >
      <template #prefix>
        <EventIcon class="h-4 w-4" />
      </template>
      <span>{{ __('Schedule an Event') }}</span>
    </Button>
    <Button
      v-else-if="title == 'Notes'"
      variant="solid"
      :label="__('New Note')"
      iconLeft="plus"
      @click="modalRef.showNote()"
    />
    <Button
      v-else-if="title == 'Tasks'"
      variant="solid"
      :label="__('New Task')"
      iconLeft="plus"
      @click="modalRef.showTask()"
    />
    <Button
      v-else-if="title == 'Attachments'"
      variant="solid"
      :label="__('Upload Attachment')"
      iconLeft="plus"
      @click="showFilesUploader = true"
    />
    <Dropdown v-else :options="defaultActions" @click.stop>
      <template #default="{ open }">
        <Button
          variant="solid"
          class="flex items-center gap-1"
          :label="__('New')"
          iconLeft="plus"
          :iconRight="open ? 'chevron-up' : 'chevron-down'"
        />
      </template>
    </Dropdown>
  </div>
</template>
<script setup>
import MultiActionButton from '@/components/MultiActionButton.vue'
import Email2Icon from '@/components/Icons/Email2Icon.vue'
import CommentIcon from '@/components/Icons/CommentIcon.vue'
import EventIcon from '@/components/Icons/EventIcon.vue'
import PhoneIcon from '@/components/Icons/PhoneIcon.vue'
import NoteIcon from '@/components/Icons/NoteIcon.vue'
import TaskIcon from '@/components/Icons/TaskIcon.vue'
import AttachmentIcon from '@/components/Icons/AttachmentIcon.vue'
import WhatsAppIcon from '@/components/Icons/WhatsAppIcon.vue'
import SMSIcon from '@/components/Icons/SMSIcon.vue'
import { globalStore } from '@/stores/global'
import { whatsappEnabled } from '@/composables/whatsapp'
import { smsEnabled } from '@/composables/sms'
import { callEnabled } from '@/composables/telephony'
import { Dropdown } from 'frappe-ui'
import { computed, h } from 'vue'

const props = defineProps({
  tabs: { type: Array, default: () => [] },
  title: { type: String, default: '' },
  doc: { type: Object, default: () => ({}) },
  modalRef: { type: Object, default: () => ({}) },
  whatsappBox: { type: Object, default: () => ({}) },
  smsBox: { type: Object, default: () => ({}) },
  counts: { type: Object, default: () => ({}) },
})

const channel = defineModel('channel', { type: String, default: 'all' })

// Only the channels this site actually has. An SMS chip on a CRM with no
// Twilio is a promise it cannot keep.
const channelOptions = computed(() =>
  [
    { key: 'all', label: 'All' },
    { key: 'email', label: 'Email', icon: Email2Icon },
    {
      key: 'whatsapp',
      label: 'WhatsApp',
      icon: WhatsAppIcon,
      condition: () => whatsappEnabled.value,
    },
    {
      key: 'sms',
      label: 'SMS',
      icon: SMSIcon,
      condition: () => smsEnabled.value,
    },
    { key: 'comment', label: 'Comments', icon: CommentIcon },
  ]
    .filter((option) => !option.condition || option.condition())
    .map((option) => ({ ...option, count: props.counts?.[option.key] || 0 })),
)

// One button, and it writes in the channel you are reading.
const NEW_LABEL = {
  all: 'New',
  email: 'New Email',
  whatsapp: 'New Message',
  sms: 'New SMS',
  comment: 'New Comment',
}

const newLabel = computed(() => NEW_LABEL[channel.value] || 'New')

function startNew() {
  if (channel.value === 'whatsapp') return props.whatsappBox?.show?.()
  if (channel.value === 'sms') return props.smsBox?.show?.()
  if (channel.value === 'comment') return (emailBox.value.showComment = true)
  if (channel.value === 'email') return (emailBox.value.show = true)
  // «All»: writing needs a channel, and email is the one every record has
  emailBox.value.show = true
}

const { makeCall } = globalStore()

const tabIndex = defineModel({ type: Number })
const showWhatsappTemplates = defineModel('showWhatsappTemplates', {
  type: Boolean,
})
const showFilesUploader = defineModel('showFilesUploader', { type: Boolean })
const emailBox = defineModel('emailBox', { type: Object, default: () => ({}) })

const defaultActions = computed(() => {
  let actions = [
    {
      icon: h(Email2Icon, { class: 'h-4 w-4' }),
      label: __('Email'),
      onClick: () => (emailBox.value.show = true),
    },
    {
      icon: h(CommentIcon, { class: 'h-4 w-4' }),
      label: __('Comment'),
      onClick: () => (emailBox.value.showComment = true),
    },
    {
      icon: h(EventIcon, { class: 'h-4 w-4' }),
      label: __('Schedule an Event'),
      onClick: () => props.modalRef.showEvent(),
    },
    {
      icon: h(PhoneIcon, { class: 'h-4 w-4' }),
      label: __('Log a Call'),
      onClick: () => props.modalRef.createCallLog(),
    },
    {
      icon: h(PhoneIcon, { class: 'h-4 w-4' }),
      label: __('Make a Call'),
      onClick: () => makeCall(props.doc.mobile_no),
      condition: () => callEnabled.value,
    },
    {
      icon: h(NoteIcon, { class: 'h-4 w-4' }),
      label: __('Note'),
      onClick: () => props.modalRef.showNote(),
    },
    {
      icon: h(TaskIcon, { class: 'h-4 w-4' }),
      label: __('Task'),
      onClick: () => props.modalRef.showTask(),
    },
    {
      icon: h(AttachmentIcon, { class: 'h-4 w-4' }),
      label: __('Upload Attachment'),
      onClick: () => (showFilesUploader.value = true),
    },
    {
      icon: h(WhatsAppIcon, { class: 'h-4 w-4' }),
      label: __('WhatsApp Message'),
      onClick: () => (tabIndex.value = getTabIndex('WhatsApp')),
      condition: () => whatsappEnabled.value,
    },
    {
      icon: h(SMSIcon, { class: 'h-4 w-4' }),
      label: __('SMS'),
      onClick: () => (tabIndex.value = getTabIndex('SMS')),
      condition: () => smsEnabled.value,
    },
  ]
  return actions.filter((action) =>
    action.condition ? action.condition() : true,
  )
})

function getTabIndex(name) {
  return props.tabs.findIndex((tab) => tab.name === name)
}

const callActions = computed(() => {
  let actions = [
    {
      label: __('Log a Call'),
      icon: 'plus',
      onClick: () => props.modalRef.createCallLog(),
    },
    {
      label: __('Make a Call'),
      icon: h(PhoneIcon, { class: 'h-4 w-4' }),
      onClick: () => makeCall(props.doc.mobile_no),
      condition: () => callEnabled.value,
    },
  ]

  return actions.filter((action) =>
    action.condition ? action.condition() : true,
  )
})
</script>
