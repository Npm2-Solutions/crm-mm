<template>
  <!--
    An email, written the way every message here is written: a line that grows
    as you type, with its tools and the send button beside it.

    It used to be a form that unfolded when the line was clicked — To, CC, BCC,
    Subject, a bordered editing area, a toolbar of headings — and stayed open
    until somebody pressed Discard. Who it goes to and what it is about are
    still here, in one line until they need more: the person whose record this
    is and a subject from the record, which is right nine times in ten. A click
    opens them; a reply that copies people in opens them by itself.
  -->
  <Editor
    ref="textEditor"
    v-model="content"
    :extensions="extensions"
    :placeholder="placeholder"
    :editable="editable"
    :upload-function="(file) => uploadFile(file, doctype, modelValue.name)"
    @focus="onFocus"
  >
    <div class="w-full">
      <button
        v-if="!expanded"
        type="button"
        class="mx-1.5 mt-1 flex w-[calc(100%-0.75rem)] min-w-0 items-center gap-1.5 rounded-md px-2 py-1 text-left text-p-sm text-ink-gray-5 transition-colors hover:bg-surface-gray-2"
        :aria-label="__('Recipients and subject')"
        @click="expanded = true"
      >
        <span class="shrink-0">{{ __('To') }}</span>
        <span
          class="min-w-0 truncate"
          :class="toEmails.length ? 'text-ink-gray-8' : 'text-ink-amber-8'"
        >
          {{ toEmails.length ? toEmails.join(', ') : __('nobody yet') }}
        </span>
        <template v-if="subject">
          <span class="shrink-0" aria-hidden="true">·</span>
          <span class="min-w-0 flex-1 truncate">{{ subject }}</span>
        </template>
        <span
          class="lucide-chevron-down ml-auto size-3.5 shrink-0"
          aria-hidden="true"
        />
      </button>
      <div v-else class="flex flex-col gap-1 px-3 pt-1.5">
        <div v-if="from.length" class="flex items-center gap-2">
          <span class="w-14 shrink-0 text-p-sm text-ink-gray-5 max-md:w-12">
            {{ __('From') }}
          </span>
          <FormControl
            v-model="fromEmail"
            type="select"
            variant="ghost"
            class="min-w-0 flex-1"
            :options="from"
          />
        </div>
        <!-- a long address gives way; CC, BCC and the fold do not -->
        <div class="flex items-start gap-2">
          <span
            class="mt-1.5 w-14 shrink-0 text-p-sm text-ink-gray-5 max-md:w-12"
          >
            {{ __('To') }}
          </span>
          <EmailMultiSelect
            v-model="toEmails"
            class="min-w-0 flex-1"
            variant="ghost"
            :validate="validateEmail"
            :fetchContacts="true"
            :error-message="
              (value) => __('{0} is an invalid email address', [value])
            "
          />
          <div class="flex shrink-0 items-center gap-0.5">
            <Button
              :label="__('CC')"
              variant="ghost"
              size="sm"
              :class="cc ? '!bg-surface-gray-3' : '!text-ink-gray-5'"
              @click="toggleCC()"
            />
            <Button
              :label="__('BCC')"
              variant="ghost"
              size="sm"
              :class="bcc ? '!bg-surface-gray-3' : '!text-ink-gray-5'"
              @click="toggleBCC()"
            />
            <Button
              variant="ghost"
              size="sm"
              icon="lucide-chevron-up"
              :tooltip="__('Fold into one line')"
              :aria-label="__('Fold into one line')"
              @click="expanded = false"
            />
          </div>
        </div>
        <div v-if="cc" class="flex items-center gap-2">
          <span class="w-14 shrink-0 text-p-sm text-ink-gray-5 max-md:w-12">
            {{ __('CC') }}
          </span>
          <EmailMultiSelect
            ref="ccInput"
            v-model="ccEmails"
            class="min-w-0 flex-1"
            variant="ghost"
            :fetchContacts="true"
            :validate="validateEmail"
            :error-message="
              (value) => __('{0} is an invalid email address', [value])
            "
          />
        </div>
        <div v-if="bcc" class="flex items-center gap-2">
          <span class="w-14 shrink-0 text-p-sm text-ink-gray-5 max-md:w-12">
            {{ __('BCC') }}
          </span>
          <EmailMultiSelect
            ref="bccInput"
            v-model="bccEmails"
            class="min-w-0 flex-1"
            variant="ghost"
            :fetchContacts="true"
            :validate="validateEmail"
            :error-message="
              (value) => __('{0} is an invalid email address', [value])
            "
          />
        </div>
        <div class="flex items-center gap-2">
          <span class="w-14 shrink-0 text-p-sm text-ink-gray-5 max-md:w-12">
            {{ __('Subject') }}
          </span>
          <input
            v-model="subject"
            class="min-w-0 flex-1 border-none bg-transparent px-2 py-1 text-p-base text-ink-gray-9 hover:bg-transparent focus:border-none focus:!shadow-none focus-visible:!ring-0"
          />
        </div>
      </div>

      <!-- headings, lists, links: there when asked for, not before -->
      <div
        v-if="formatting"
        class="mx-1.5 mt-1 overflow-x-auto rounded-md bg-surface-gray-2 px-1 dark:bg-surface-gray-3"
      >
        <EditorFixedMenu :items="fullToolbar" />
      </div>

      <div class="flex items-end gap-1 px-1.5 pb-1.5 pt-0.5">
        <!-- a reply's quote is folded away, as it is in the email once sent -->
        <EditorContent
          class="composer-text min-w-0 flex-1 [&_p.reply-to-content]:hidden"
          :class="showQuote ? '' : '[&_p.reply-to-content~*]:hidden'"
        />
        <div class="flex h-9 shrink-0 items-center">
          <Button
            variant="ghost"
            :icon="EmailTemplateIcon"
            :tooltip="__('Insert an email template')"
            :aria-label="__('Insert an email template')"
            @click="showEmailTemplateSelectorModal = true"
          />
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
          <!-- a phone's keyboard has its own -->
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
            :tooltip="__('Discard this email')"
            :aria-label="__('Discard this email')"
            v-bind="discardButtonProps || {}"
          />
          <Button
            class="ml-0.5"
            variant="solid"
            icon="lucide-send-horizontal"
            :tooltip="`${__('Send')} (${submitShortcutLabel})`"
            :aria-label="__('Send')"
            v-bind="submitButtonProps || {}"
          />
        </div>
      </div>

      <button
        v-if="quoting"
        type="button"
        class="mx-2.5 mb-1.5 flex items-center gap-1 rounded px-1 py-0.5 text-p-xs text-ink-gray-5 transition-colors hover:bg-surface-gray-2 hover:text-ink-gray-7"
        :aria-expanded="showQuote ? 'true' : 'false'"
        @click="showQuote = !showQuote"
      >
        <span class="lucide-quote size-3" aria-hidden="true" />
        {{
          showQuote
            ? __('Hide the email being answered')
            : __('Show the email being answered')
        }}
      </button>
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
  <EmailTemplateSelectorModal
    v-model="showEmailTemplateSelectorModal"
    :doctype="doctype"
    @apply="applyEmailTemplate"
  />
</template>

<script setup>
import IconPicker from '@/components/IconPicker.vue'
import SmileIcon from '@/components/Icons/SmileIcon.vue'
import EmailTemplateIcon from '@/components/Icons/EmailTemplateIcon.vue'
import AttachmentIcon from '@/components/Icons/AttachmentIcon.vue'
import AttachmentItem from '@/components/AttachmentItem.vue'
import EmailMultiSelect from '@/components/Controls/EmailMultiSelect.vue'
import EmailTemplateSelectorModal from '@/components/Modals/EmailTemplateSelectorModal.vue'
import {
  buildEditorExtensions,
  fullToolbar,
  uploadFile,
} from '@/components/editor/config'
import { Button, FileUploader, call, FormControl } from 'frappe-ui'
import {
  Editor,
  EditorContent,
  EditorFixedMenu,
  EditorTableMenu,
} from 'frappe-ui/editor'
import { useTelemetry } from 'frappe-ui/frappe'
import { useDocument } from '@/data/document'
import { validateEmail, submitShortcutLabel } from '@/utils'
import { quotes } from '@/utils/emailDraft'
import { isMobileView } from '@/composables/breakpoints'
import Paragraph from '@tiptap/extension-paragraph'
import { ref, computed, nextTick, inject, watch } from 'vue'

const props = defineProps({
  placeholder: { type: String, default: null },
  editable: { type: Boolean, default: true },
  doctype: { type: String, default: 'CRM Lead' },
  subject: { type: String, default: __('Email From Lead') },
  editorProps: { type: Object, default: () => ({}) },
  submitButtonProps: { type: Object, default: () => ({}) },
  discardButtonProps: { type: Object, default: () => ({}) },
  // something written or attached, which is when there is something to discard
  draft: { type: Boolean, default: false },
})

const emit = defineEmits(['focus'])

const CustomParagraph = Paragraph.extend({
  addAttributes() {
    return {
      class: {
        default: null,
        renderHTML: (attributes) => {
          if (!attributes.class) {
            return {}
          }
          return {
            class: `${attributes.class}`,
          }
        },
      },
    }
  },
})

const modelValue = defineModel({ type: Object })
const attachments = defineModel('attachments', {
  type: Array,
  default: () => [],
})
const content = defineModel('content', { type: String, default: '' })

const { capture } = useTelemetry()
const { user: sessionUser } = inject('session')
const { document: user } = useDocument('User', sessionUser)

const textEditor = ref(null)
const cc = ref(false)
const bcc = ref(false)
const emoji = ref('')
// the recipients and the subject unfolded from their one line
const expanded = ref(false)
// the headings-and-lists bar
const formatting = ref(false)
// a reply's quote, unfolded
const showQuote = ref(false)

const subject = ref(props.subject)

// The same trap as the To field below, for the subject: it is proposed from the
// record, the record is usually still loading when the composer is set up, and
// a copy taken once read «(#undefined)» for good. It follows the proposal until
// somebody writes a subject of their own — then it is theirs.
watch(
  () => props.subject,
  (proposed, before) => {
    if (subject.value === before) subject.value = proposed
  },
)
const fromEmail = ref('')
const toEmails = ref(modelValue.value.email ? [modelValue.value.email] : [])

/**
 * The person whose record this is, already in the To field.
 *
 * This ran once, when the component was created — and at that moment the record
 * is still being fetched, so `email` was almost always undefined and the field
 * stayed empty. The address arrived a moment later and nothing was watching for
 * it, which is why the recipient had to be typed on a screen that knew perfectly
 * well who it was for. (The discard handler set it correctly, which is the tell:
 * somebody noticed the empty field and fixed the one path that ran late enough.)
 *
 * Only into an empty field: a reply fills it with the sender, and somebody who
 * has chosen an address is not to be second-guessed.
 */
watch(
  () => modelValue.value?.email,
  (email) => {
    if (email && !toEmails.value.length) toEmails.value = [email]
  },
  { immediate: true },
)
const ccEmails = ref([])
const bccEmails = ref([])
const ccInput = ref(null)
const bccInput = ref(null)

const extensions = buildEditorExtensions({
  starterKit: { paragraph: false },
  extra: [CustomParagraph],
})

const from = computed(() => {
  if (!user.doc || !user.doc.user_emails?.length) return []
  let emails = user.doc.user_emails.map((e) => {
    return {
      label: e.email_account + ' <' + e.email_id + '>',
      value: e.email_id,
    }
  })

  if (emails.length == 1 && emails[0].email_id === sessionUser) return []

  return emails
})

watch(
  from,
  (fromOptions) => {
    if (!fromOptions.find((f) => f.value === fromEmail.value)) {
      fromEmail.value = fromOptions.length ? fromOptions[0].value : ''
    }
  },
  { immediate: true },
)

const editor = computed(() => textEditor.value?.editor)

// answering an email, which is carried quoted under what is written
const quoting = computed(() => quotes(content.value))

function removeAttachment(attachment) {
  attachments.value = attachments.value.filter((a) => a !== attachment)
}

const showEmailTemplateSelectorModal = ref(false)

async function applyEmailTemplate(template) {
  let data = await call(
    'frappe.email.doctype.email_template.email_template.get_email_template',
    {
      template_name: template.name,
      doc: modelValue.value,
    },
  )

  if (template.subject) {
    subject.value = data.subject
  }

  if (template.response) {
    content.value = data.message
  }
  showEmailTemplateSelectorModal.value = false
  capture('email_template_applied', { doctype: props.doctype })
}

function appendEmoji() {
  editor.value.commands.insertContent(emoji.value)
  editor.value.commands.focus()
  emoji.value = ''
  capture('emoji_inserted_in_email', { emoji: emoji.value })
}

// Writing to nobody is the one thing about the recipients that cannot wait:
// they unfold the moment somebody starts writing without any. And a reply that
// copies people in says so by showing them.
function onFocus() {
  if (!toEmails.value.length) expanded.value = true
  emit('focus')
}

watch([cc, bcc], ([copied, blind]) => {
  if (copied || blind) expanded.value = true
})

// A new email to the person of this record, as the box starts: after one is
// sent, or thrown away.
function reset() {
  subject.value = props.subject
  toEmails.value = modelValue.value?.email ? [modelValue.value.email] : []
  ccEmails.value = []
  bccEmails.value = []
  cc.value = false
  bcc.value = false
  expanded.value = false
  showQuote.value = false
}

function toggleCC() {
  cc.value = !cc.value
  if (cc.value) nextTick(() => ccInput.value.setFocus())
}

function toggleBCC() {
  bcc.value = !bcc.value
  if (bcc.value) nextTick(() => bccInput.value.setFocus())
}

defineExpose({
  editor,
  subject,
  cc,
  bcc,
  fromEmail,
  toEmails,
  ccEmails,
  bccEmails,
  expanded,
  formatting,
  fromOptions: from,
  reset,
})
</script>
