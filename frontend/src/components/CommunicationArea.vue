<template>
  <!--
    Nothing is open: the line you write on. Clicking it is what opens the editor
    — an email or a comment is usually one sentence, and meeting it with a
    toolbar and a subject line asks for a letter.

    The channel strip is not here: it is mounted once above this whole region,
    so it survives an editor opening. See Activities.vue.
  -->
  <ComposerBar
    v-if="!showEmailBox && !showCommentBox && !showWhatsAppBox"
    :channel="way"
    @open="openWay"
  />
  <div
    v-show="showEmailBox"
    @keydown.ctrl.enter.capture.stop="submitEmail"
    @keydown.meta.enter.capture.stop="submitEmail"
  >
    <EmailEditor
      ref="newEmailEditor"
      v-model:content="newEmail"
      v-model="doc"
      v-model:attachments="attachments"
      :submitButtonProps="{
        variant: 'solid',
        onClick: submitEmail,
        disabled: emailEmpty,
      }"
      :discardButtonProps="{
        onClick: async () => {
          await deleteAttachedFiles()
          showEmailBox = false
          newEmailEditor.subject = subject
          newEmailEditor.toEmails = doc.email ? [doc.email] : []
          newEmailEditor.ccEmails = []
          newEmailEditor.bccEmails = []
          newEmailEditor.cc = false
          newEmailEditor.bcc = false
          newEmail = ''
        },
      }"
      :editable="showEmailBox"
      :doctype="doctype"
      :subject="subject"
      :placeholder="
        __('Hi John, \n\nCan you please provide more details on this...')
      "
    />
  </div>
  <div
    v-show="showCommentBox"
    @keydown.ctrl.enter.capture.stop="submitComment"
    @keydown.meta.enter.capture.stop="submitComment"
  >
    <CommentBox
      ref="newCommentEditor"
      v-model:content="newComment"
      v-model="doc"
      v-model:attachments="attachments"
      :submitButtonProps="{
        variant: 'solid',
        onClick: submitComment,
        disabled: commentEmpty,
      }"
      :discardButtonProps="{
        onClick: async () => {
          await deleteAttachedFiles()
          showCommentBox = false
          newComment = ''
        },
      }"
      :editable="showCommentBox"
      :doctype="doctype"
      :placeholder="__('@John, can you please check this?')"
    />
  </div>
  <!-- mounted the first time it is opened, and kept afterwards: the box asks
       the backend which numbers this person has, and that question is not worth
       asking on every record somebody merely looks at -->
  <div v-if="whatsappEnabled && whatsappEverOpened" v-show="showWhatsAppBox">
    <!-- the same box as the WhatsApp tab, not a second one: recipient choice,
         media checks and templates behave identically wherever you write from -->
    <WhatsAppBox
      ref="whatsappBox"
      v-model="doc"
      v-model:whatsapp="whatsapp"
      v-model:reply="reply"
      :doctype="doctype"
      @scroll="emit('scroll')"
      @template="emit('template')"
    />
  </div>
</template>

<script setup>
import ComposerBar from '@/components/ComposerBar.vue'
import EmailEditor from '@/components/EmailEditor.vue'
import CommentBox from '@/components/CommentBox.vue'
import WhatsAppBox from '@/components/Activities/WhatsAppBox.vue'
import { whatsappEnabled } from '@/composables/whatsapp'
import { isContentEmpty } from '@/utils'
import { usersStore } from '@/stores/users'
import { useStorage } from '@vueuse/core'
import { useOnboarding, useTelemetry } from 'frappe-ui/frappe'
import { call, createResource, toast } from 'frappe-ui'
import { ref, watch, computed } from 'vue'

const props = defineProps({
  doctype: { type: String, default: 'CRM Lead' },
  // Which channel the stream above is showing. The box follows it, because a
  // picker that changes what you read and not what you write in is a picker
  // that will be ignored.
  channel: { type: String, default: 'all' },
})

const doc = defineModel({ type: Object, default: () => ({}) })
const reload = defineModel('reload', { type: Boolean })
const whatsapp = defineModel('whatsapp', { type: Object, default: () => ({}) })
const reply = defineModel('reply', { type: Object, default: () => ({}) })

const emit = defineEmits(['scroll', 'template', 'channel'])

const { getUser } = usersStore()
const { updateOnboardingStep } = useOnboarding('frappecrm')
const { capture } = useTelemetry()

// The channels somebody can write in. «all» and «call» are for reading only,
// so they leave the line set to whatever it was.
const WAYS_OF_WRITING = ['email', 'sms', 'whatsapp', 'comment']

const showEmailBox = ref(false)
const showCommentBox = ref(false)

// One box at a time: three open editors on the same record is nobody's idea of
// a conversation. Which way the line is set to write is remembered while the
// record is open, so somebody writing comments all afternoon is not put back on
// email every time. Declared here rather than beside `openWay`: the watch below
// is `immediate`, so it reads this while the setup body is still running.
const way = ref('email')

// A reading-only channel («all», «call») opens nothing by itself: there is no
// obvious channel to be writing in, and a composer that springs open steals the
// scroll. A channel with a box of its own closes what is open here, so an email
// editor is not left standing underneath a WhatsApp conversation.
watch(
  () => props.channel,
  (channel) => {
    if (channel === 'email') {
      showCommentBox.value = false
      showEmailBox.value = true
    } else if (channel === 'comment') {
      showEmailBox.value = false
      showCommentBox.value = true
    } else if (channel === 'whatsapp' || channel === 'sms') {
      showEmailBox.value = false
      showCommentBox.value = false
    }
    if (WAYS_OF_WRITING.includes(channel)) way.value = channel
  },
  { immediate: true },
)
const showWhatsAppBox = ref(false)
const whatsappEverOpened = ref(false)
const whatsappBox = ref(null)
const newEmail = useStorage(
  `emailBoxContent-${getUser().email}-${props.doctype}-${doc.value.name}`,
  '',
)
// A restored draft already carries its signature; this flag (persisted with the
// draft) stops setSignature from prepending another one on every reopen/reload.
const signatureAdded = useStorage(
  `emailSignatureAdded-${getUser().email}-${props.doctype}-${doc.value.name}`,
  false,
)
const newComment = useStorage(
  `commentBoxContent-${getUser().email}-${props.doctype}-${doc.value.name}`,
  '',
)
const newEmailEditor = ref(null)
const newCommentEditor = ref(null)

const attachments = useStorage(
  `attachments-${getUser().email}-${props.doctype}-${doc.value.name}`,
  [],
  localStorage,
  {
    serializer: {
      read: (v) => (v ? JSON.parse(v) : []),
      write: (v) => JSON.stringify(v),
    },
  },
)

const subject = computed(() => {
  let prefix = ''
  if (doc.value?.lead_name) {
    prefix = doc.value.lead_name
  } else if (doc.value?.organization) {
    prefix = doc.value.organization
  }
  return `${prefix} (#${doc.value.name})`
})

const signature = createResource({
  url: 'crm.api.get_user_signature',
  cache: 'user-email-signature',
  auto: true,
})

function setSignature(editor) {
  if (!signature.data || signatureAdded.value) return
  const sig = signature.data.replace(/\n/g, '<br>')
  let emailContent = editor.getHTML()
  emailContent = emailContent.startsWith('<p></p>')
    ? emailContent.slice(7)
    : emailContent
  editor.commands.setContent(sig + emailContent)
  editor.commands.focus('start')
  signatureAdded.value = true
}

// Clearing the draft (send / discard) resets the guard so the next fresh
// compose gets its signature again.
watch(newEmail, (value) => {
  if (!value) signatureAdded.value = false
})

watch(
  () => showEmailBox.value,
  (value) => {
    if (value) {
      let editor = newEmailEditor.value.editor
      editor.commands.focus()
      setSignature(editor)
    }
  },
)

watch(
  () => showCommentBox.value,
  (value) => {
    if (value) {
      newCommentEditor.value.editor.commands.focus()
    }
  },
)

const commentEmpty = computed(() => isContentEmpty(newComment.value))

const emailEmpty = computed(
  () =>
    isContentEmpty(newEmail.value) || !newEmailEditor.value?.toEmails?.length,
)

async function sendMail() {
  let fromEmail = newEmailEditor.value.fromEmail || getUser().email
  let recipients = newEmailEditor.value.toEmails
  let subject = newEmailEditor.value.subject
  let cc = newEmailEditor.value.ccEmails || []
  let bcc = newEmailEditor.value.bccEmails || []

  if (attachments.value.length) {
    capture('email_attachments_added')
  }
  await call('frappe.core.doctype.communication.email.make', {
    recipients: recipients.join(', '),
    attachments: attachments.value.map((x) => x.name),
    cc: cc.join(', '),
    bcc: bcc.join(', '),
    subject: subject,
    content: newEmail.value,
    doctype: props.doctype,
    name: doc.value.name,
    send_email: 1,
    sender: fromEmail,
    sender_full_name: getUser()?.full_name || undefined,
  })
}

async function sendComment() {
  let _attachments = attachments.value.length
    ? attachments.value.map((x) => x.name)
    : []

  let comment = await call('crm.api.comment.add_comment', {
    reference_doctype: props.doctype,
    reference_name: doc.value.name,
    content: newComment.value,
    attachments: _attachments,
  })

  if (comment && attachments.value.length) {
    capture('comment_attachments_added')
  }
}

async function deleteAttachedFiles() {
  if (!attachments.value || attachments.value.length === 0) return

  const deletePromises = attachments.value.map(async (file) => {
    try {
      await call('frappe.client.delete', {
        doctype: 'File',
        name: file.name,
      })
    } catch (error) {
      console.warn(`Failed to delete file ${file.name}:`, error)
    }
  })

  await Promise.all(deletePromises)

  attachments.value = []
}

async function submitEmail() {
  if (emailEmpty.value) return
  showEmailBox.value = false
  // toast.promise returns the toast id (not the promise), so await the send
  // itself — otherwise the reload below fires before the email is committed and
  // the new email is missing from the refetched list.
  const sending = sendMail()
  toast.promise(sending, {
    loading: __('Sending email...'),
    success: __('Email sent'),
    error: (e) => e?.messages?.[0] || __('Failed to send email!'),
  })
  try {
    await sending
  } catch {
    return
  }
  newEmail.value = ''
  attachments.value = []
  reload.value = true
  emit('scroll')
  capture('email_sent', { doctype: props.doctype })
  updateOnboardingStep('send_first_email')
}

async function submitComment() {
  if (commentEmpty.value) return
  showCommentBox.value = false
  const sending = sendComment()
  toast.promise(sending, {
    loading: __('Sending comment...'),
    success: __('Comment sent'),
    error: (e) => e?.messages?.[0] || __('Failed to send comment!'),
  })
  try {
    await sending
  } catch {
    return
  }
  newComment.value = ''
  attachments.value = []
  reload.value = true
  emit('scroll')
  capture('comment_sent', { doctype: props.doctype })
  updateOnboardingStep('add_first_comment')
}

function openWay(which) {
  way.value = which
  if (which === 'whatsapp') {
    whatsappEverOpened.value = true
  }
  // SMS has a box of its own, mounted by the caller when the channel is SMS:
  // choosing it here is choosing the channel, and the stream follows.
  emit('channel', which)
  const boxes = {
    email: showEmailBox,
    comment: showCommentBox,
    whatsapp: showWhatsAppBox,
  }
  Object.entries(boxes).forEach(([name, box]) => (box.value = name === which))
}

defineExpose({
  show: showEmailBox,
  showComment: showCommentBox,
  showWhatsApp: showWhatsAppBox,
  whatsappBox,
  editor: newEmailEditor,
})
</script>
