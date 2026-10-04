<!--
  Modifications copyright (c) 2026, NPM2 Solutions Srl
-->
<template>
  <div :id="activity.name">
    <!--
      Inside the chat: one line — who, that it is a note for the team, when.
      «Administrator added a comment · 2 hours ago» said the kind of thing in a
      sentence and the time in a different unit from every clock around it.
    -->
    <div
      v-if="bare"
      class="mb-1 flex min-w-0 items-center gap-1.5 text-p-xs text-ink-amber-8"
    >
      <CommentIcon class="size-3.5 shrink-0" />
      <span class="min-w-0 truncate font-medium">
        {{ activity.owner_name }}
      </span>
      <span class="shrink-0 text-ink-amber-7">· {{ __('Internal note') }}</span>
      <span class="ml-auto shrink-0 tabular-nums text-ink-gray-5">
        {{ time }}
      </span>
      <Dropdown
        v-if="isOwner && !editing"
        :options="menuOptions"
        placement="right"
        @click="confirmingDelete = false"
      >
        <Button
          icon="lucide-more-horizontal"
          variant="ghost"
          class="touch-target !h-5 !w-5 -mr-1"
          :aria-label="__('Options')"
        />
      </Dropdown>
    </div>
    <div
      v-else
      class="mb-1 flex items-center justify-stretch gap-2 py-1 text-base"
    >
      <div class="inline-flex items-center flex-wrap gap-1 text-ink-gray-5">
        <UserAvatar class="mr-1" :user="activity.owner" size="md" />
        <span class="font-medium text-ink-gray-8">
          {{ activity.owner_name }}
        </span>
        <span>{{ __('added a') }}</span>
        <span class="max-w-xs truncate font-medium text-ink-gray-8">
          {{ __('comment') }}
        </span>
      </div>
      <div class="ml-auto flex items-center gap-1 whitespace-nowrap">
        <TimelineTimestamp :date="activity.creation" />
        <Dropdown
          v-if="isOwner && !editing"
          :options="menuOptions"
          placement="right"
          @click="confirmingDelete = false"
        >
          <Button
            :aria-label="__('Options')"
            icon="lucide-more-horizontal"
            variant="ghost"
            class="!h-6 !w-6"
          />
        </Dropdown>
      </div>
    </div>
    <!--
      The same card a logged call gets: a note and a call are both something
      that happened, written down — and two surfaces for one kind of thing made
      the stream read as two streams laid on top of each other.
    -->
    <!--
      Bare means the card in the chat is already the box. Drawing a second one
      inside it gave every internal comment a white panel inside an amber panel
      inside the stream — three frames for one sentence.
    -->
    <div
      class="text-base leading-6 text-ink-gray-9 transition-all duration-300 ease-in-out"
      :class="
        bare
          ? ''
          : 'rounded-md border border-outline-elevation-2 bg-surface-elevation-1 px-3 py-[7.5px]'
      "
    >
      <template v-if="editing">
        <RichTextField
          :content="editContent"
          editor-class="prose-sm max-w-none min-h-[3rem]"
          @change="editContent = $event"
        />
        <div class="mt-2 flex justify-end gap-2">
          <Button :label="__('Cancel')" @click="cancelEdit" />
          <Button
            variant="solid"
            :label="__('Save')"
            :loading="saving"
            @click="saveEdit"
          />
        </div>
      </template>
      <template v-else>
        <!-- eslint-disable-next-line vue/no-v-html -->
        <div class="prose-f" v-html="sanitizeHTML(activity.content)" />
        <div
          v-if="activity.attachments?.length"
          class="mt-2 flex flex-wrap gap-2"
        >
          <AttachmentItem
            v-for="a in activity.attachments"
            :key="a.file_url"
            :label="a.file_name"
            :url="a.file_url"
          />
        </div>
      </template>
    </div>
  </div>
</template>
<script setup>
import UserAvatar from '@/components/UserAvatar.vue'
import CommentIcon from '@/components/Icons/CommentIcon.vue'
import AttachmentItem from '@/components/AttachmentItem.vue'
import RichTextField from '@/components/RichTextField.vue'
import { Dropdown, Button, call, toast } from 'frappe-ui'
import TimelineTimestamp from '@/components/Activities/TimelineTimestamp.vue'
import { sanitizeHTML, ConfirmDelete } from '@/utils'
import { sessionStore } from '@/stores/session'
import { computed, ref } from 'vue'

const props = defineProps({
  activity: { type: Object, default: () => ({}) },
  // the card in the chat is already the box
  bare: { type: Boolean, default: false },
  // the clock, in the chat's own format — the day is on the marker above
  time: { type: String, default: '' },
})

const emit = defineEmits(['reload'])

const { user } = sessionStore()

const isOwner = computed(() => props.activity.owner === user)

const editing = ref(false)
const saving = ref(false)
const editContent = ref('')
const confirmingDelete = ref(false)

const menuOptions = computed(() => [
  {
    label: __('Edit'),
    icon: 'edit-2',
    onClick: startEdit,
  },
  ...ConfirmDelete({
    onConfirmDelete: deleteComment,
    isConfirmingDelete: confirmingDelete,
  }),
])

function startEdit() {
  editContent.value = props.activity.content || ''
  editing.value = true
}

function cancelEdit() {
  editing.value = false
  editContent.value = ''
}

async function saveEdit() {
  if (editContent.value === props.activity.content) {
    editing.value = false
    return
  }
  saving.value = true
  try {
    await call('frappe.client.set_value', {
      doctype: 'Comment',
      name: props.activity.name,
      fieldname: 'content',
      value: editContent.value,
    })
    editing.value = false
    emit('reload')
  } catch {
    toast.error(__('Failed to update comment'))
  } finally {
    saving.value = false
  }
}

async function deleteComment() {
  try {
    await call('frappe.client.delete', {
      doctype: 'Comment',
      name: props.activity.name,
    })
    emit('reload')
  } catch {
    toast.error(__('Failed to delete comment'))
  }
}
</script>
