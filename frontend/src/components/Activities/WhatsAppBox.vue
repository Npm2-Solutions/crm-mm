<!-- eslint-disable vue/no-v-html -->
<template>
  <div
    v-if="reply?.message"
    class="flex items-center justify-around gap-2 px-3 pt-2 sm:px-10"
  >
    <div
      class="mb-1 ml-13 flex-1 cursor-pointer rounded border-0 border-l-4 border-green-500 bg-surface-gray-2 p-2 text-base text-ink-gray-5"
      :class="reply.type == 'Incoming' ? 'border-green-500' : 'border-blue-400'"
    >
      <div
        class="mb-1 text-sm-bold"
        :class="
          reply.type == 'Incoming' ? 'text-ink-green-5' : 'text-ink-blue-link'
        "
      >
        {{ reply.from_name || __('You') }}
      </div>
      <div
        class="max-h-12 overflow-hidden"
        v-html="sanitizeHTML(reply.message)"
      />
    </div>

    <Button variant="ghost" icon="lucide-x" @click="reply = {}" />
  </div>
  <!-- WhatsApp only lets a business write freely for 24 hours after the
       customer's last message; outside that window Meta delivers an approved
       template and nothing else. This says so instead of letting the send fail,
       but it does not block it: what we know about the window is only as good
       as the incoming messages that reached us. -->
  <div
    v-if="!windowOpen"
    class="mx-3 mb-1 flex items-center justify-between gap-3 rounded border border-outline-amber-2 bg-surface-amber-1 px-3 py-2 sm:mx-10"
  >
    <span class="text-p-sm text-ink-gray-7">{{ windowNotice }}</span>
    <Button size="sm" :label="__('Send a template')" @click="emit('template')" />
  </div>
  <!-- Which of the person's numbers this is going to. One number, and there is
       nothing to choose: it says so and stays out of the way. -->
  <div
    v-if="recipients.data?.length"
    class="flex items-center gap-2 px-3 pt-2 text-p-sm text-ink-gray-5 sm:px-10"
  >
    <span>{{ __('To') }}</span>
    <Dropdown v-if="recipients.data.length > 1" :options="recipientOptions">
      <template #default="{ open }">
        <Button
          size="sm"
          variant="ghost"
          :label="recipient"
          :iconRight="open ? 'chevron-up' : 'chevron-down'"
        />
      </template>
    </Dropdown>
    <span v-else class="text-ink-gray-7">{{ recipient }}</span>
  </div>
  <div class="flex items-end gap-2 px-3 py-2.5 sm:px-10" v-bind="$attrs">
    <div class="flex h-8 items-center gap-2">
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
          <div class="flex items-center space-x-2">
            <Dropdown :options="uploadOptions(openFileSelector)">
              <span
                class="lucide-plus size-4.5 cursor-pointer text-ink-gray-5"
                aria-hidden="true"
              />
            </Dropdown>
          </div>
        </template>
      </FileUploader>
      <button
        v-if="!recording"
        class="lucide-mic size-4.5 cursor-pointer text-ink-gray-5"
        :title="__('Record a voice message')"
        aria-hidden="true"
        @click="startRecording"
      />
      <button
        v-else
        class="lucide-square size-4.5 cursor-pointer text-ink-red-5"
        :title="__('Stop and send')"
        aria-hidden="true"
        @click="stopRecording"
      />
      <span v-if="recording" class="text-sm tabular-nums text-ink-red-5">
        {{ recordingLabel }}
      </span>
      <IconPicker
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
        <SmileIcon
          class="flex size-4.5 cursor-pointer rounded-sm text-2xl leading-none text-ink-gray-4"
          @click="togglePopover"
        />
      </IconPicker>
    </div>
    <Textarea
      ref="textareaRef"
      v-model="content"
      type="textarea"
      class="min-h-8 w-full"
      :rows="rows"
      :placeholder="placeholder"
      @focus="rows = 6"
      @blur="rows = 1"
      @keydown.enter.stop="(e) => sendTextMessage(e)"
    />
  </div>
</template>

<script setup>
import IconPicker from '@/components/IconPicker.vue'
import SmileIcon from '@/components/Icons/SmileIcon.vue'
import { sanitizeHTML } from '@/utils'
import { useTelemetry } from 'frappe-ui/frappe'
import {
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

const rows = ref(1)
const textareaRef = ref(null)
const emoji = ref('')

// Which of the person's numbers this conversation is going out to. The primary
// comes first and is the default; the rest are there because somebody wrote the
// work line down too, and a reply to the wrong one goes nowhere.
const recipient = ref('')

const recipients = createResource({
  url: 'crm.api.whatsapp.get_recipients',
  makeParams: () => ({
    reference_doctype: props.doctype,
    reference_name: doc.value.name,
  }),
  onSuccess: (numbers) => {
    if (!numbers?.includes(recipient.value)) recipient.value = numbers?.[0] || ''
  },
})

watch(
  () => doc.value.name,
  (name) => {
    recipient.value = ''
    if (name) recipients.fetch()
  },
  { immediate: true },
)

const recipientOptions = computed(() =>
  (recipients.data || []).map((number) => ({
    label: number,
    onClick: () => (recipient.value = number),
  })),
)

const content = ref('')
const placeholder = ref(__('Type your message here...'))
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

// What WhatsApp actually accepts, from Meta's media reference. A file outside
// this list is refused by Meta after the upload, and the chat used to show only
// "failed" — so it is refused here, by name, before anything is sent.
const WHATSAPP_MEDIA = {
  image: { extensions: ['jpg', 'jpeg', 'png'], megabytes: 5, label: 'JPEG, PNG' },
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
let recorder = null
let chunks = []
let ticker = null

const recordingLabel = computed(() => {
  const seconds = recordingSeconds.value
  return `${String(Math.floor(seconds / 60)).padStart(2, '0')}:${String(seconds % 60).padStart(2, '0')}`
})

// Chrome records `audio/webm` by default, which WhatsApp refuses outright — the
// voice note was uploaded, sent, and rejected. OGG/Opus and MP4 are on Meta's
// accepted list; if the browser can do neither, better to say so than to record
// something that cannot be delivered.
function recordableType() {
  return (
    ['audio/ogg;codecs=opus', 'audio/ogg', 'audio/mp4'].find((type) =>
      MediaRecorder.isTypeSupported?.(type),
    ) || ''
  )
}

async function startRecording() {
  if (!navigator.mediaDevices?.getUserMedia || typeof MediaRecorder === 'undefined') {
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
      __('This browser can only record in a format WhatsApp does not accept'),
    )
    return
  }

  chunks = []
  recorder = new MediaRecorder(stream, { mimeType: container })
  recorder.ondataavailable = (event) => event.data.size && chunks.push(event.data)
  recorder.onstop = async () => {
    stream.getTracks().forEach((track) => track.stop())
    clearInterval(ticker)
    recording.value = false
    if (!chunks.length) return
    await uploadRecording(new Blob(chunks, { type: recorder.mimeType || container }))
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

async function uploadRecording(blob) {
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
    sendWhatsAppMessage()
  } catch (e) {
    toast.error(__('Could not send the voice message'))
  }
}

function show() {
  nextTick(() => textareaRef.value.el.focus())
}

function uploadFile(file) {
  whatsapp.value.attach = file.file_url
  whatsapp.value.content_type = fileType.value
  sendWhatsAppMessage()
  capture('whatsapp_upload_file')
}

function sendTextMessage(event) {
  if (event.shiftKey) return
  sendWhatsAppMessage()
  textareaRef.value.el?.blur()
  content.value = ''
  capture('whatsapp_send_message')
}

async function sendWhatsAppMessage() {
  let args = {
    reference_doctype: props.doctype,
    reference_name: doc.value.name,
    message: content.value,
    to: recipient.value || doc.value.mobile_no,
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
    onSuccess: () => whatsapp.value.reload(),
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
  if (recorder && recorder.state !== 'inactive') recorder.stop()
})

watch(reply, (value) => {
  if (value?.message) {
    show()
  }
})

defineExpose({ show })
</script>
