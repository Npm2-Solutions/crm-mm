<!--
  Modifications copyright (c) 2026, NPM2 Solutions Srl
-->
<template>
  <!--
    A note for the team, written like every other message: a line that grows,
    its tools and the send button beside it. The formatting bar comes when
    asked for.
  -->
  <Editor
    ref="commentEditor"
    v-model="content"
    :extensions="extensions"
    :placeholder="placeholder"
    :editable="editable"
    :upload-function="(file) => uploadFile(file, doctype, modelValue.name)"
  >
    <div class="w-full">
      <div
        v-if="formatting"
        class="mx-1.5 mt-1.5 overflow-x-auto rounded-md bg-surface-gray-2 px-1 dark:bg-surface-gray-3"
      >
        <EditorFixedMenu :items="toolbarFor(isMobileView)" />
      </div>
      <div class="flex items-end gap-1 p-1.5">
        <EditorContent class="composer-text min-w-0 flex-1" />
        <div class="flex h-9 shrink-0 items-center">
          <FileUploader
            :upload-args="{
              doctype: doctype,
              docname: modelValue.name,
              private: true,
            }"
            @success="(f) => attachments.push(f)"
          >
            <template #default="{ openFileSelector }">
              <Button
                variant="ghost"
                :icon="AttachmentIcon"
                :tooltip="__('Attach a file')"
                :aria-label="__('Attach a file')"
                @click="openFileSelector()"
              />
            </template>
          </FileUploader>
          <IconPicker
            v-if="!isMobileView"
            v-slot="{ togglePopover }"
            v-model="emoji"
            @update:modelValue="() => appendEmoji()"
          >
            <Button
              variant="ghost"
              :icon="SmileIcon"
              :tooltip="__('Emoji')"
              :aria-label="__('Emoji')"
              @click="togglePopover()"
            />
          </IconPicker>
          <Button
            variant="ghost"
            icon="lucide-type"
            :class="formatting ? '!bg-surface-gray-3' : ''"
            :tooltip="__('Formatting')"
            :aria-label="__('Formatting')"
            :aria-pressed="formatting ? 'true' : 'false'"
            @click="formatting = !formatting"
          />
          <Button
            v-if="draft"
            variant="ghost"
            icon="lucide-trash-2"
            :tooltip="__('Discard this note')"
            :aria-label="__('Discard this note')"
            v-bind="discardButtonProps || {}"
          />
          <Button
            class="ml-0.5"
            variant="solid"
            icon="lucide-send-horizontal"
            :tooltip="`${__('Add note')} (${submitShortcutLabel})`"
            :aria-label="__('Add note')"
            v-bind="submitButtonProps || {}"
          />
        </div>
      </div>
      <div v-if="attachments.length" class="flex flex-wrap gap-2 px-3 pb-2">
        <AttachmentItem
          v-for="a in attachments"
          :key="a.file_url"
          :label="a.file_name"
        >
          <template #suffix>
            <span
              class="lucide-x h-3.5"
              aria-hidden="true"
              @click.stop="removeAttachment(a)"
            />
          </template>
        </AttachmentItem>
      </div>
      <EditorTableMenu />
    </div>
  </Editor>
</template>
<script setup>
import IconPicker from '@/components/IconPicker.vue'
import SmileIcon from '@/components/Icons/SmileIcon.vue'
import AttachmentIcon from '@/components/Icons/AttachmentIcon.vue'
import AttachmentItem from '@/components/AttachmentItem.vue'
import {
  buildEditorExtensions,
  toolbarFor,
  uploadFile,
} from '@/components/editor/config'
import { submitShortcutLabel } from '@/utils'
import { isMobileView } from '@/composables/breakpoints'
import { usersStore } from '@/stores/users'
import { useTelemetry } from 'frappe-ui/frappe'
import { Button, FileUploader } from 'frappe-ui'
import {
  Editor,
  EditorContent,
  EditorFixedMenu,
  EditorTableMenu,
} from 'frappe-ui/editor'
import { ref, computed } from 'vue'

defineProps({
  placeholder: { type: String, default: null },
  editable: { type: Boolean, default: true },
  doctype: { type: String, default: 'CRM Lead' },
  editorProps: { type: Object, default: () => ({}) },
  submitButtonProps: { type: Object, default: () => ({}) },
  discardButtonProps: { type: Object, default: () => ({}) },
  // something written or attached, which is when there is something to discard
  draft: { type: Boolean, default: false },
})

const modelValue = defineModel({ type: Object })
const attachments = defineModel('attachments', {
  type: Array,
  default: () => [],
})
const content = defineModel('content', { type: String, default: '' })

const { users: usersList } = usersStore()
const { capture } = useTelemetry()

const commentEditor = ref(null)
const emoji = ref('')
// the headings-and-lists bar
const formatting = ref(false)

const editor = computed(() => commentEditor.value?.editor)

const users = computed(
  () =>
    usersList.data?.crmUsers
      ?.filter((user) => user.enabled)
      .map((user) => ({
        id: user.name,
        label: user.full_name?.trim() || user.name,
      })) || [],
)

const extensions = buildEditorExtensions({ mentions: () => users.value })

function appendEmoji() {
  editor.value.commands.insertContent(emoji.value)
  editor.value.commands.focus()
  emoji.value = ''
  capture('emoji_inserted_in_comment', { emoji: emoji.value })
}

function removeAttachment(attachment) {
  attachments.value = attachments.value.filter((a) => a !== attachment)
}

defineExpose({ editor })
</script>
