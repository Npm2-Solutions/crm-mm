<!--
  Modifications copyright (c) 2026, NPM2 Solutions Srl
-->
<!-- eslint-disable vue/no-v-html -->
<template>
  <!--
    The message being answered, quoted above the line — the same small copy of
    a bubble the conversation shows once it is sent.
  -->
  <div v-if="reply?.message" class="flex items-start gap-2 px-3 pt-2">
    <div
      class="min-w-0 flex-1 rounded-md border-l-4 bg-surface-alpha-gray-2 px-2 py-1.5"
      :class="
        reply.type == 'Incoming'
          ? 'border-outline-gray-4'
          : 'border-outline-blue-4'
      "
    >
      <div
        class="text-p-xs font-medium"
        :class="
          reply.type == 'Incoming' ? 'text-ink-gray-7' : 'text-ink-blue-8'
        "
      >
        {{ reply.from_name || __('You') }}
      </div>
      <div
        class="line-clamp-2 text-p-sm text-ink-gray-6"
        v-html="sanitizeHTML(reply.message)"
      />
    </div>
    <Button
      variant="ghost"
      icon="lucide-x"
      :aria-label="__('Cancel reply')"
      @click="reply = {}"
    />
  </div>
  <!-- WhatsApp only lets a business write freely for 24 hours after the
       customer's last message; outside that window Meta delivers an approved
       template and nothing else. This says so instead of letting the send fail,
       but it does not block it: what we know about the window is only as good
       as the incoming messages that reached us. -->
  <div
    v-if="!windowOpen && !isMobileView"
    class="mx-3 mt-2 flex flex-wrap items-center justify-between gap-x-3 gap-y-1.5 rounded-lg bg-surface-amber-1 px-3 py-2 ring-1 ring-inset ring-outline-amber-2"
  >
    <span class="min-w-0 flex-1 text-p-sm text-ink-amber-9">
      {{ windowNotice }}
    </span>
    <Button
      size="sm"
      :label="__('Send a template')"
      @click="emit('template')"
    />
  </div>
  <!-- On a phone, held either way, one line, the whole of it the way to the
       templates: two lines and a button took a third of the box, over a chat
       already short (sideways, they left it 90px) -->
  <button
    v-if="!windowOpen && isMobileView"
    type="button"
    class="mx-2 mt-1.5 flex min-h-9 w-[calc(100%-1rem)] items-center gap-2 rounded-lg bg-surface-amber-1 px-3 text-left text-p-sm text-ink-amber-9 ring-1 ring-inset ring-outline-amber-2 active:bg-surface-amber-2"
    @click="emit('template')"
  >
    <span class="lucide-clock size-4 shrink-0" aria-hidden="true" />
    <span class="min-w-0 flex-1 truncate">{{ windowNoticeShort }}</span>
    <span class="shrink-0 font-medium">
      {{ __('Choose', null, 'WhatsApp template') }}
    </span>
  </button>
  <!--
    Recording takes over the composer instead of hiding in it.

    The whole thing used to be one button: press to start, press to send. No way
    to stop without sending, no way to hear it first, and nothing on screen
    afterwards to say whether it had gone — a voice note is the one message you
    cannot glance at before it leaves, so it was the one that most needed
    checking.
  -->
  <div
    v-if="recording || voiceNote"
    class="flex items-center gap-3 px-3 py-2.5"
  >
    <Button
      variant="ghost"
      icon="lucide-trash-2"
      :aria-label="__('Discard')"
      :tooltip="__('Discard')"
      @click="discardRecording"
    />

    <template v-if="recording">
      <span
        class="size-2 shrink-0 animate-pulse rounded-full bg-surface-red-5"
      />
      <span class="shrink-0 text-p-base tabular-nums text-ink-red-6">
        {{ recordingLabel }}
      </span>
      <span class="truncate text-p-sm text-ink-gray-5">
        {{ __('Recording…') }}
      </span>
      <Button
        class="ml-auto shrink-0"
        variant="subtle"
        :label="__('Stop', null, 'Stop recording')"
        @click="stopRecording"
      />
    </template>

    <template v-else>
      <audio :src="voiceNote.url" controls class="h-8 min-w-0 flex-1" />
      <Button
        class="shrink-0"
        variant="solid"
        :label="sendingVoice ? __('Sending…') : __('Send')"
        :loading="sendingVoice"
        @click="sendRecording"
      />
    </template>
  </div>

  <!--
    What is written first, then the tools, then the button that sends — the
    same row as an email or a note. The attachment clip and the emoji used to
    sit before the words, so the text started a third of the way along the box
    and every channel wrote from a different place.
  -->
  <div v-else class="flex items-end gap-1 px-1.5 pb-1.5 pt-1" v-bind="$attrs">
    <!--
      One line, and as many as the message needs — up to a point, after which
      the chat above would be the one giving way. Focus used to jump it to six
      rows whatever was in it, so a «ok» got five empty lines under it and the
      conversation got pushed off screen to hold them.
    -->
    <Textarea
      ref="textareaRef"
      v-model="content"
      variant="ghost"
      class="min-h-9 w-full resize-none bg-transparent py-2 text-p-base text-ink-gray-9 placeholder-ink-gray-4"
      :rows="1"
      :placeholder="placeholder"
      @keydown.enter.stop="(e) => sendTextMessage(e)"
    />
    <div class="strumenti-compositore flex h-9 shrink-0 items-center">
      <!-- `private: false` is load-bearing. frappe_whatsapp hands Meta a link and
           Meta fetches it anonymously; a private Frappe file answers that fetch
           with a login page, so the message fails every time. FileUploader
           defaults to private, which is why nothing with a file ever left. -->
      <FileUploader
        :uploadArgs="{ private: false }"
        :validateFile="validateForWhatsApp"
        @success="(file) => uploadFile(file)"
      >
        <template #default="{ openFileSelector }">
          <Dropdown :options="uploadOptions(openFileSelector)">
            <Button
              variant="ghost"
              icon="lucide-paperclip"
              :aria-label="__('Attach a file')"
              :tooltip="__('Attach a file')"
            />
          </Dropdown>
        </template>
      </FileUploader>
      <!-- a phone's keyboard has its own -->
      <IconPicker
        v-if="!isMobileView"
        v-slot="{ togglePopover }"
        v-model="emoji"
        @update:modelValue="
          () => {
            content += emoji
            $refs.textareaRef.el.focus()
            capture('whatsapp_emoji_added')
          }
        "
      >
        <Button
          variant="ghost"
          :aria-label="__('Emoji')"
          :tooltip="__('Emoji')"
          @click="togglePopover"
        >
          <template #icon>
            <SmileIcon class="size-4 text-ink-gray-6" />
          </template>
        </Button>
      </IconPicker>
      <!-- the only way to open a conversation that has gone quiet for a day,
           so it lives beside the line, not behind a menu -->
      <Button
        variant="ghost"
        icon="lucide-file-text"
        :aria-label="__('Send a template')"
        :tooltip="__('Send a template')"
        @click="emit('template')"
      />
      <!--
        The microphone while there is nothing written, the arrow once there is:
        the one button WhatsApp keeps in that corner. Enter still sends; the
        arrow is for whoever does not know that, and on a phone there is no
        Enter.
      -->
      <Button
        v-if="content.trim()"
        class="ml-0.5"
        variant="solid"
        icon="lucide-send-horizontal"
        :aria-label="__('Send')"
        :tooltip="isMobileView ? __('Send') : `${__('Send')} (Enter)`"
        @click="sendTyped"
      />
      <Button
        v-else
        class="ml-0.5"
        variant="ghost"
        icon="lucide-mic"
        :aria-label="__('Record a voice message')"
        :tooltip="__('Record a voice message')"
        @click="startRecording"
      />
    </div>
  </div>
</template>

<script setup>
import IconPicker from '@/components/IconPicker.vue'
import SmileIcon from '@/components/Icons/SmileIcon.vue'
import { sanitizeHTML } from '@/utils'
import { isMobileView } from '@/composables/breakpoints'
import { markAnswered } from '@/composables/conversationState'
import { useDraft } from '@/composables/drafts'
import { useGrowingTextarea } from '@/composables/growingTextarea'
import { useTelemetry } from 'frappe-ui/frappe'
import {
  Button,
  createResource,
  Textarea,
  FileUploader,
  Dropdown,
  toast,
  dayjs,
  dayjsLocal,
} from 'frappe-ui'
import { ref, computed, nextTick, watch, onBeforeUnmount } from 'vue'

const props = defineProps({
  doctype: { type: String, default: '' },
})

const emit = defineEmits(['template'])

const doc = defineModel({ type: Object, default: () => ({}) })
const whatsapp = defineModel('whatsapp', { type: Object, default: () => ({}) })
const reply = defineModel('reply', { type: Object, default: () => ({}) })

const { capture } = useTelemetry()

const textareaRef = ref(null)
const emoji = ref('')

// What is being written to this person, kept per record like an email's
// draft: a look at another lead used to throw it away.
const content = useDraft('whatsappDraft', props.doctype, doc.value.name)

// As tall as what is in it: one line for «ok», six at most, because past that
// the composer would be eating the conversation it belongs to.
const { fit } = useGrowingTextarea(textareaRef, content)
// on a phone the line has three keys beside it: the long words went on two
// lines and doubled the box
const placeholder = computed(() =>
  reply.value?.message
    ? __('Write your reply…')
    : isMobileView.value
      ? __('WhatsApp message…')
      : __('Write a WhatsApp message…'),
)
const fileType = ref('')

// --- the 24-hour window -----------------------------------------------------
// Only a message *from* the customer opens it, which is why an echo of our own
// messages does not count here.
const lastIncomingAt = computed(() => {
  const messages = whatsapp.value?.data || []
  for (let i = messages.length - 1; i >= 0; i--) {
    if (messages[i].type === 'Incoming') return messages[i].creation
  }
  return null
})

const windowOpen = computed(() => {
  if (!lastIncomingAt.value) return false
  return dayjs().diff(dayjsLocal(lastIncomingAt.value), 'hour', true) < 24
})

const windowNotice = computed(() =>
  lastIncomingAt.value
    ? __(
        'More than 24 hours since this contact last wrote: WhatsApp only delivers an approved template now.',
      )
    : __(
        'This contact has never written here: WhatsApp only delivers an approved template until they reply.',
      ),
)

const windowNoticeShort = computed(() =>
  lastIncomingAt.value
    ? __('Over 24 hours: only a template')
    : __('Never written here: only a template'),
)

// What WhatsApp actually accepts, from Meta's media reference. A file outside
// this list is refused by Meta after the upload, and the chat used to show only
// "failed" — so it is refused here, by name, before anything is sent.
const WHATSAPP_MEDIA = {
  image: {
    extensions: ['jpg', 'jpeg', 'png'],
    megabytes: 5,
    label: 'JPEG, PNG',
  },
  video: { extensions: ['mp4', '3gp'], megabytes: 16, label: 'MP4, 3GP' },
  audio: {
    extensions: ['aac', 'amr', 'mp3', 'm4a', 'ogg'],
    megabytes: 16,
    label: 'AAC, AMR, MP3, M4A, OGG',
  },
  document: {
    extensions: ['txt', 'xls', 'xlsx', 'doc', 'docx', 'ppt', 'pptx', 'pdf'],
    megabytes: 100,
    label: 'PDF, DOC, DOCX, XLS, XLSX, PPT, PPTX, TXT',
  },
}

function validateForWhatsApp(file) {
  const rules = WHATSAPP_MEDIA[fileType.value]
  if (!rules) return null

  const extension = (file.name.split('.').pop() || '').toLowerCase()
  if (!rules.extensions.includes(extension)) {
    return __('WhatsApp does not accept .{0} here. It takes: {1}.', [
      extension || '?',
      rules.label,
    ])
  }
  if (file.size > rules.megabytes * 1024 * 1024) {
    return __('WhatsApp allows at most {0} MB for this kind of file.', [
      rules.megabytes,
    ])
  }
  return null
}

// --- voice messages ---------------------------------------------------------
// Recorded in the browser with MediaRecorder, uploaded like any other file and
// sent as an audio message, so it lands in the same chat as everything else.
const recording = ref(false)
const recordingSeconds = ref(0)
// What was recorded and not yet sent: `{ blob, url }`. Kept rather than sent
// straight away, so it can be heard — and thrown away — first.
const voiceNote = ref(null)
const sendingVoice = ref(false)
let recorder = null
let chunks = []
let ticker = null

const recordingLabel = computed(() => {
  const seconds = recordingSeconds.value
  return `${String(Math.floor(seconds / 60)).padStart(2, '0')}:${String(seconds % 60).padStart(2, '0')}`
})

// The codec is named, never left to the browser.
//
// Asking for `audio/mp4` and nothing more is how this failed the second time:
// Chrome answers that request with **Opus inside MP4**, a combination WhatsApp
// refuses — `audio/mp4` means AAC to Meta, and Opus is only allowed inside OGG.
// The file played fine in the browser that made it, the server sent the right
// Content-Type, and Meta still marked the message failed an hour later.
//
// So the list holds only pairings that are what they say they are: Opus in OGG,
// AAC in MP4. Plain `audio/ogg` is out too — it may be Vorbis, which Meta does
// not take either. If the browser can do none of them, better to say so than to
// record something that cannot be delivered.
const RECORDABLE = [
  'audio/ogg;codecs=opus',
  'audio/mp4;codecs=mp4a.40.2',
  'audio/aac',
]

function recordableType() {
  return RECORDABLE.find((type) => MediaRecorder.isTypeSupported?.(type)) || ''
}

async function startRecording() {
  if (
    !navigator.mediaDevices?.getUserMedia ||
    typeof MediaRecorder === 'undefined'
  ) {
    toast.error(__('This browser cannot record audio'))
    return
  }
  let stream
  try {
    stream = await navigator.mediaDevices.getUserMedia({ audio: true })
  } catch (e) {
    toast.error(__('Microphone access was denied'))
    return
  }
  const container = recordableType()
  if (!container) {
    stream.getTracks().forEach((track) => track.stop())
    toast.error(
      __(
        'This browser cannot record in a format WhatsApp accepts. Try Firefox, Safari, or your phone.',
      ),
    )
    return
  }

  chunks = []
  recorder = new MediaRecorder(stream, { mimeType: container })
  recorder.ondataavailable = (event) =>
    event.data.size && chunks.push(event.data)
  recorder.onstop = () => {
    stream.getTracks().forEach((track) => track.stop())
    clearInterval(ticker)
    recording.value = false
    if (!chunks.length || discarding) {
      discarding = false
      return
    }
    const blob = new Blob(chunks, { type: recorder.mimeType || container })
    voiceNote.value = { blob, url: URL.createObjectURL(blob) }
  }
  recorder.start()
  recording.value = true
  recordingSeconds.value = 0
  ticker = setInterval(() => (recordingSeconds.value += 1), 1000)
  capture('whatsapp_record_audio')
}

function stopRecording() {
  if (recorder && recorder.state !== 'inactive') recorder.stop()
}

// Set while a recording is being thrown away, so `onstop` knows not to keep
// what it collected. The recorder has no other way to say why it stopped.
let discarding = false

function forgetVoiceNote() {
  if (voiceNote.value?.url) URL.revokeObjectURL(voiceNote.value.url)
  voiceNote.value = null
  sendingVoice.value = false
}

function discardRecording() {
  if (recording.value) {
    discarding = true
    stopRecording()
  }
  forgetVoiceNote()
}

async function sendRecording() {
  const blob = voiceNote.value?.blob
  if (!blob || sendingVoice.value) return
  sendingVoice.value = true

  // `.mp4` matters. The browser hands back `audio/mp4` on Safari and recent
  // Chrome, and naming the file after the container is what lets the server say
  // it is audio when Meta comes to fetch it.
  const extension = (blob.type.split('/')[1] || 'ogg').split(';')[0]
  const form = new FormData()
  form.append('file', blob, `voice-${Date.now()}.${extension}`)
  form.append('is_private', 0)
  form.append('doctype', props.doctype)
  form.append('docname', doc.value.name)
  try {
    const response = await fetch('/api/method/upload_file', {
      method: 'POST',
      headers: { 'X-Frappe-CSRF-Token': window.csrf_token },
      body: form,
    })
    const data = await response.json()
    const fileUrl = data?.message?.file_url
    if (!fileUrl) throw new Error('no file_url')
    whatsapp.value.attach = fileUrl
    whatsapp.value.content_type = 'audio'
    forgetVoiceNote()
    sendWhatsAppMessage()
  } catch (e) {
    sendingVoice.value = false
    toast.error(__('Could not send the voice message'))
  }
}

function show() {
  nextTick(() => {
    fit()
    textareaRef.value?.el?.focus()
  })
}

function uploadFile(file) {
  whatsapp.value.attach = file.file_url
  whatsapp.value.content_type = fileType.value
  sendWhatsAppMessage()
  capture('whatsapp_upload_file')
}

// Enter sends at a desk. On a phone it is the key for a new line, the way it is
// in WhatsApp itself — there the arrow is how a message leaves — and a word
// being composed in an input method is not finished until it says so.
function sendTextMessage(event) {
  if (event.shiftKey || event.isComposing || isMobileView.value) return
  event.preventDefault()
  sendTyped()
}

// Enter and the arrow send the same way. Focus stays on the line: somebody who
// has just sent «un attimo» is about to send the next thing.
function sendTyped() {
  if (!content.value.trim()) return
  sendWhatsAppMessage()
  content.value = ''
  capture('whatsapp_send_message')
}

async function sendWhatsAppMessage() {
  let args = {
    reference_doctype: props.doctype,
    reference_name: doc.value.name,
    message: content.value,
    // no recipient: the record knows whose conversation this is, and the
    // backend reads it from there. A number sent from here would be a second
    // answer to a question that already has one.
    attach: whatsapp.value.attach || '',
    reply_to: reply.value?.name || '',
    content_type: whatsapp.value.content_type,
  }
  content.value = ''
  fileType.value = ''
  whatsapp.value.attach = ''
  whatsapp.value.content_type = 'text'
  reply.value = {}
  createResource({
    url: 'crm.api.whatsapp.create_whatsapp_message',
    params: args,
    auto: true,
    onSuccess: () => {
      whatsapp.value.reload()
      // nobody answers what they have not read
      markAnswered(args.reference_doctype, args.reference_name)
    },
    onError: (error) => {
      toast.error(error.messages?.[0] || __('Failed to send WhatsApp message'))
    },
  })
}

function uploadOptions(openFileSelector) {
  return [
    {
      label: __('Upload Document'),
      icon: 'file',
      onClick: () => {
        fileType.value = 'document'
        openFileSelector()
      },
    },
    {
      label: __('Upload Image'),
      icon: 'image',
      onClick: () => {
        fileType.value = 'image'
        openFileSelector('image/*')
      },
    },
    {
      label: __('Upload Video'),
      icon: 'video',
      onClick: () => {
        fileType.value = 'video'
        openFileSelector('video/*')
      },
    },
    {
      label: __('Upload Audio'),
      icon: 'mic',
      onClick: () => {
        fileType.value = 'audio'
        openFileSelector('audio/*')
      },
    },
  ]
}

onBeforeUnmount(() => {
  clearInterval(ticker)
  if (recorder && recorder.state !== 'inactive') {
    discarding = true
    recorder.stop()
  }
  forgetVoiceNote()
})

watch(reply, (value) => {
  if (value?.message) {
    show()
  }
})

defineExpose({ show })
</script>
