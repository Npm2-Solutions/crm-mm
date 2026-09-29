<template>
  <!--
    Email and the team's notes: always ready to be written in, the way the
    WhatsApp line is.

    Both used to start as a line that, clicked, turned into a form — To, CC,
    Subject, a bordered editor, a toolbar — and the form stayed until somebody
    pressed Discard, whether or not anything had been written. Now the line is
    the editor: it grows as you write, its tools are beside it, and what is
    not being used is folded into one line (EmailEditor.vue). Leaving it
    empty leaves nothing behind; leaving it written keeps the draft, per
    record, as before.

    The channel strip is not here: it is on the composer around this, which
    also lights up in the channel's colour while the cursor is in it. See
    Activities.vue.
  -->
  <div
    v-show="way === 'email'"
    @keydown.ctrl.enter.capture.stop="submitEmail"
    @keydown.meta.enter.capture.stop="submitEmail"
  >
    <EmailEditor
      ref="newEmailEditor"
      v-model:content="newEmail"
      v-model="doc"
      v-model:attachments="attachments"
      :draft="emailDraft"
      :submitButtonProps="{
        onClick: submitEmail,
        disabled: emailEmpty || sending.email,
      }"
      :discardButtonProps="{ onClick: () => discard('email') }"
      :doctype="doctype"
      :subject="subject"
      :placeholder="__('Write an email…')"
    />
    <!--
      Which signature goes under this email, said while it is written rather
      than put into the box: see utils/emailDraft.js. And it can be left off,
      for the one-line answer that does not need a letterhead.
    -->
    <div
      v-if="emailDraft && signatureLine"
      class="flex min-w-0 items-center gap-1.5 px-3 pb-2 text-p-xs text-ink-gray-5"
    >
      <span class="lucide-signature size-3 shrink-0" aria-hidden="true" />
      <span class="min-w-0 truncate" :class="{ 'line-through': !sign }">
        {{ signatureLine }}
      </span>
      <button
        type="button"
        class="shrink-0 rounded px-1 text-ink-gray-6 transition-colors hover:bg-surface-gray-2 hover:text-ink-gray-8"
        @click="sign = !sign"
      >
        {{ sign ? __('Leave off') : __('Sign') }}
      </button>
    </div>
  </div>
  <div
    v-show="way === 'comment'"
    @keydown.ctrl.enter.capture.stop="submitComment"
    @keydown.meta.enter.capture.stop="submitComment"
  >
    <CommentBox
      ref="newCommentEditor"
      v-model:content="newComment"
      v-model="doc"
      v-model:attachments="commentAttachments"
      :draft="commentDraft"
      :submitButtonProps="{
        onClick: submitComment,
        disabled: commentEmpty || sending.comment,
      }"
      :discardButtonProps="{ onClick: () => discard('comment') }"
      :doctype="doctype"
      :placeholder="__('Write a note for the team…')"
    />
  </div>
</template>

<script setup>
import EmailEditor from '@/components/EmailEditor.vue'
import CommentBox from '@/components/CommentBox.vue'
import { isContentEmpty } from '@/utils'
import {
  replyAddresses,
  replyDraft,
  replySubject,
  signaturePreview,
  signed,
  written,
} from '@/utils/emailDraft'
import { usersStore } from '@/stores/users'
import { markAnswered } from '@/composables/conversationState'
import { useDraft } from '@/composables/drafts'
import { useOnboarding, useTelemetry } from 'frappe-ui/frappe'
import { call, createResource, toast } from 'frappe-ui'
import { computed, nextTick, reactive, ref } from 'vue'

const props = defineProps({
  doctype: { type: String, default: 'CRM Lead' },
  // Which of the two this box writes: an email, or a note for the team. The
  // composer around it decides — WhatsApp and SMS have boxes of their own.
  way: { type: String, default: 'email' },
})

const doc = defineModel({ type: Object, default: () => ({}) })
const reload = defineModel('reload', { type: Boolean })

// `open`: somebody started writing from outside — a Reply, «Send an email» —
// and the composer around this has to be on that channel for it to be seen.
const emit = defineEmits(['scroll', 'open'])

const { getUser } = usersStore()
const { updateOnboardingStep } = useOnboarding('frappecrm')
const { capture } = useTelemetry()

// Drafts are kept per person and per record, so going to WhatsApp and back —
// or to another lead and back — finds the email where it was left.
function kept(what, initial = '', options) {
  return useDraft(what, props.doctype, doc.value.name, initial, options)
}
const FILES = {
  serializer: {
    read: (v) => (v ? JSON.parse(v) : []),
    write: (v) => JSON.stringify(v),
  },
}
const newEmail = kept('emailBoxContent')
const newComment = kept('commentBoxContent')
// one list each: a file attached to the email is not attached to the note
const attachments = kept('attachments', [], FILES)
const commentAttachments = kept('commentAttachments', [], FILES)
const newEmailEditor = ref(null)
const newCommentEditor = ref(null)

// «Mario Rossi (#CRM-LEAD-…)», once there is a record to name: before it has
// loaded there is nothing to say, and «(#undefined)» is not a subject.
const subject = computed(() => {
  if (!doc.value?.name) return ''
  const prefix = doc.value.lead_name || doc.value.organization || ''
  return prefix ? `${prefix} (#${doc.value.name})` : `#${doc.value.name}`
})

const signature = createResource({
  url: 'crm.api.get_user_signature',
  cache: 'user-email-signature',
  auto: true,
})
const signatureLine = computed(() => signaturePreview(signature.data))
// under this email or not: on unless somebody leaves it off, for this one
const sign = ref(true)

// something to keep, or to throw away: written, or attached
const emailDraft = computed(
  () => !isContentEmpty(newEmail.value) || attachments.value.length > 0,
)
const commentDraft = computed(
  () =>
    !isContentEmpty(newComment.value) || commentAttachments.value.length > 0,
)

// Something to send. A reply carries the email it answers from the moment
// Reply is pressed, and that alone is not a message.
const emailEmpty = computed(
  () =>
    isContentEmpty(written(newEmail.value)) ||
    !newEmailEditor.value?.toEmails?.length,
)
const commentEmpty = computed(() => isContentEmpty(newComment.value))

// on its way, so a second Ctrl+Enter does not send it twice
const sending = reactive({ email: false, comment: false })

async function deleteFiles(files) {
  await Promise.all(
    files.map((file) =>
      call('frappe.client.delete', { doctype: 'File', name: file.name }).catch(
        (error) => console.warn(`Failed to delete file ${file.name}:`, error),
      ),
    ),
  )
}

// Who an email goes to and what it is about, as they are now — to be put back
// if it has to be.
function header() {
  const editor = newEmailEditor.value
  if (!editor) return null
  return {
    subject: editor.subject,
    fromEmail: editor.fromEmail,
    toEmails: [...(editor.toEmails || [])],
    ccEmails: [...(editor.ccEmails || [])],
    bccEmails: [...(editor.bccEmails || [])],
    cc: editor.cc,
    bcc: editor.bcc,
  }
}

function restoreHeader(was) {
  const editor = newEmailEditor.value
  if (!editor || !was) return
  Object.assign(editor, was)
}

// The two ways, side by side, for the code that treats them alike.
const WAYS = {
  email: {
    text: newEmail,
    files: attachments,
    discarded: 'Email discarded',
  },
  comment: {
    text: newComment,
    files: commentAttachments,
    discarded: 'Note discarded',
  },
}

// Everything about a draft, to put it back after a failed send or an Undo.
function snapshot(which) {
  const way = WAYS[which]
  return {
    text: way.text.value,
    files: [...way.files.value],
    header: which === 'email' ? header() : null,
    sign: sign.value,
  }
}

function clear(which) {
  const way = WAYS[which]
  way.text.value = ''
  way.files.value = []
  if (which === 'email') {
    newEmailEditor.value?.reset?.()
    sign.value = true
  }
}

// The words back into a box. Through the editor, not only the draft: the
// editor takes a value equal to the last one it sent out for its own echo and
// ignores it — and a draft put back after an Undo is exactly that value, so
// the box stayed empty with the draft saved behind it.
function putText(which, html) {
  WAYS[which].text.value = html
  const box =
    which === 'comment' ? newCommentEditor.value : newEmailEditor.value
  box?.editor?.commands.setContent(html || '', { emitUpdate: true })
}

function restore(which, was) {
  const way = WAYS[which]
  putText(which, was.text)
  way.files.value = was.files
  if (which === 'email') {
    restoreHeader(was.header)
    sign.value = was.sign
  }
}

// Long enough to see the toast and change one's mind. The attached files are
// deleted only once it has passed: an Undo has to have something to undo.
const UNDO = 7000

/**
 * The trash beside Send. It sits a finger away from the button that sends,
 * so throwing a draft away can be taken back — for a few seconds, from the
 * toast that says it happened.
 */
function discard(which) {
  const was = snapshot(which)
  clear(which)
  let gone = false
  const timer = setTimeout(() => {
    gone = true
    deleteFiles(was.files)
  }, UNDO)
  toast.success(__(WAYS[which].discarded), {
    action: {
      label: __('Undo'),
      onClick: () => {
        clearTimeout(timer)
        restore(which, gone ? { ...was, files: [] } : was)
        open(which)
      },
    },
  })
}

async function submitEmail() {
  if (emailEmpty.value || sending.email) return
  const editor = newEmailEditor.value
  const was = snapshot('email')
  const args = {
    recipients: (editor.toEmails || []).join(', '),
    attachments: was.files.map((x) => x.name),
    cc: (editor.ccEmails || []).join(', '),
    bcc: (editor.bccEmails || []).join(', '),
    subject: editor.subject,
    content: sign.value ? signed(was.text, signature.data) : was.text,
    doctype: props.doctype,
    name: doc.value.name,
    send_email: 1,
    sender: editor.fromEmail || getUser().email,
    sender_full_name: getUser()?.full_name || undefined,
  }
  // Gone from the box the moment it is sent, as a message is; back in it if
  // sending fails, so nothing written is lost to an error.
  sending.email = true
  clear('email')
  // toast.promise returns the toast id (not the promise), so await the send
  // itself — otherwise the reload below fires before the email is committed and
  // the new email is missing from the refetched list.
  const sent = call('frappe.core.doctype.communication.email.make', args)
  toast.promise(sent, {
    loading: __('Sending email...'),
    success: __('Email sent'),
    error: (e) => e?.messages?.[0] || __('Failed to send email!'),
  })
  try {
    await sent
  } catch {
    if (!emailDraft.value) restore('email', was)
    return
  } finally {
    sending.email = false
  }
  if (was.files.length) capture('email_attachments_added')
  reload.value = true
  emit('scroll')
  // an email is an answer too — a note to colleagues is not
  markAnswered(props.doctype, doc.value.name)
  capture('email_sent', { doctype: props.doctype })
  updateOnboardingStep('send_first_email')
}

async function submitComment() {
  if (commentEmpty.value || sending.comment) return
  const was = snapshot('comment')
  sending.comment = true
  clear('comment')
  const sent = call('crm.api.comment.add_comment', {
    reference_doctype: props.doctype,
    reference_name: doc.value.name,
    content: was.text,
    attachments: was.files.map((x) => x.name),
  })
  toast.promise(sent, {
    loading: __('Sending comment...'),
    success: __('Comment sent'),
    error: (e) => e?.messages?.[0] || __('Failed to send comment!'),
  })
  try {
    await sent
  } catch {
    if (!commentDraft.value) restore('comment', was)
    return
  } finally {
    sending.comment = false
  }
  if (was.files.length) capture('comment_attachments_added')
  reload.value = true
  emit('scroll')
  capture('comment_sent', { doctype: props.doctype })
  updateOnboardingStep('add_first_comment')
}

/**
 * Start writing from outside the composer: «Reply» on an email, «Send an
 * email» in a menu, the channel's tab. The composer turns to this way (it
 * listens for `open`) and the cursor goes in — at the start for a reply, whose
 * quote is under the cursor, at the end otherwise.
 *
 * It replaces a `show` flag that was set to true to open the email: a flag
 * already true does not change, so the second Reply in a row opened nothing.
 */
function open(which = props.way, at = 'end') {
  emit('open', which)
  nextTick(() => {
    const box =
      which === 'comment' ? newCommentEditor.value : newEmailEditor.value
    box?.editor?.commands.focus(at)
  })
}

/**
 * Reply, or reply to all, to an email in the conversation: addressed to whom
 * it should go (utils/emailDraft.js), from the mailbox it reached, the email
 * quoted and folded under a line to write on — keeping whatever had already
 * been written.
 */
function reply(email, all = false) {
  const editor = newEmailEditor.value
  if (!editor || !email) return
  const ours = [
    getUser().email,
    ...(editor.fromOptions || []).map((option) => option.value),
  ]
  const { from, to, cc, bcc } = replyAddresses(email, ours, all)
  if (from) editor.fromEmail = from
  editor.toEmails = to
  editor.ccEmails = cc
  editor.bccEmails = bcc
  editor.cc = cc.length > 0
  editor.bcc = bcc.length > 0
  editor.subject = replySubject(email.subject)
  const hadWritten = !isContentEmpty(written(newEmail.value))
  newEmail.value = replyDraft(newEmail.value, email.content)
  // the cursor where the answer goes: the start of an empty line, or the end of
  // what was already there
  nextTick(() => open('email', hadWritten ? endOfWritten() : 'start'))
}

// the position just before a reply's quote, where what is written ends
function endOfWritten() {
  const doc = newEmailEditor.value?.editor?.state?.doc
  let at = null
  doc?.forEach((node, offset) => {
    if (at === null && node.attrs?.class === 'reply-to-content') at = offset
  })
  return at ? at - 1 : 'end'
}

defineExpose({ open, reply, editor: newEmailEditor })
</script>
