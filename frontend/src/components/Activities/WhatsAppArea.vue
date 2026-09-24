<!-- eslint-disable vue/no-v-html -->
<template>
  <div>
    <div
      v-for="whatsapp in messages"
      :key="whatsapp.name"
      class="activity group flex gap-2"
      :class="[
        whatsapp.type == 'Outgoing' ? 'flex-row-reverse' : '',
        whatsapp.reaction ? 'mb-7' : 'mb-3',
      ]"
    >
      <div
        :id="whatsapp.name"
        class="group/message wa-bubble relative max-w-[90%] rounded-lg p-1.5 pl-2 text-base shadow-sm"
        :class="whatsapp.type == 'Outgoing' ? 'wa-out' : 'wa-in'"
      >
        <div
          v-if="hasFailed(whatsapp)"
          class="absolute -top-2 right-0 flex items-center gap-1"
        >
          <Badge theme="red" :label="__('failed')" />
          <Button
            size="sm"
            variant="subtle"
            :label="__('Retry')"
            :loading="retrying == whatsapp.name"
            @click="retry(whatsapp)"
          />
        </div>
        <div
          v-if="whatsapp.is_reply"
          class="mb-1 cursor-pointer rounded border-0 border-l-4 bg-surface-gray-3 p-2 text-ink-gray-5"
          :class="
            whatsapp.reply_to_type == 'Incoming'
              ? 'border-green-500'
              : 'border-blue-400'
          "
          @click="() => scrollToMessage(whatsapp.reply_to)"
        >
          <div
            class="mb-1 text-sm-bold"
            :class="
              whatsapp.reply_to_type == 'Incoming'
                ? 'text-ink-green-5'
                : 'text-ink-blue-link'
            "
          >
            {{ whatsapp.reply_to_from || __('You') }}
          </div>
          <div class="flex flex-col gap-2 max-h-12 overflow-hidden">
            <div v-if="whatsapp.header" class="text-base-semibold">
              {{ whatsapp.header }}
            </div>
            <div v-html="formatWhatsAppMessage(whatsapp.reply_message)" />
            <div v-if="whatsapp.footer" class="text-xs text-ink-gray-5">
              {{ whatsapp.footer }}
            </div>
          </div>
        </div>
        <div class="flex gap-2 justify-between">
          <div
            v-if="!hasFailed(whatsapp)"
            class="absolute -right-0.5 -top-0.5 flex cursor-pointer gap-1 rounded-full bg-surface-base pb-2 pl-2 pr-1.5 pt-1.5 opacity-0 group-hover/message:opacity-100"
            :style="{
              background:
                'radial-gradient(circle at 50% 50%, rgba(255, 255, 255, 1) 0%, rgba(255, 255, 255, 1) 35%, rgba(238, 130, 238, 0) 100%)',
            }"
          >
            <Dropdown :options="messageOptions(whatsapp)">
              <span
                class="lucide-chevron-down size-4 text-ink-gray-5"
                aria-hidden="true"
              />
            </Dropdown>
          </div>
          <div
            v-if="whatsapp.reaction"
            class="absolute -bottom-5 flex gap-1 rounded-full border bg-surface-base p-1 pb-[3px] shadow-sm"
          >
            <div class="flex size-4 items-center justify-center">
              {{ whatsapp.reaction }}
            </div>
          </div>
          <div
            v-if="whatsapp.message_type == 'Template'"
            class="flex flex-col gap-2"
          >
            <div v-if="whatsapp.header" class="text-base-semibold">
              {{ whatsapp.header }}
            </div>
            <div v-html="formatWhatsAppMessage(whatsapp.template)" />
            <div v-if="whatsapp.footer" class="text-xs text-ink-gray-5">
              {{ whatsapp.footer }}
            </div>
          </div>
          <div
            v-else-if="whatsapp.content_type == 'text'"
            v-html="formatWhatsAppMessage(whatsapp.message)"
          />
          <div
            v-else-if="whatsapp.content_type == 'button'"
            v-html="formatWhatsAppMessage(whatsapp.message)"
          />
          <div v-else-if="whatsapp.content_type == 'image'">
            <img
              :src="whatsapp.attach"
              class="h-40 cursor-pointer rounded-md"
              @click="() => openFileInAnotherTab(whatsapp.attach)"
            />
            <div
              v-if="!whatsapp.message.startsWith('/files/')"
              class="mt-1.5"
              v-html="formatWhatsAppMessage(whatsapp.message)"
            />
          </div>
          <!--
            A document bubble said «Document» and nothing else: not the file
            name, not its kind, and the only way to find out was to click and
            hope. Which is the one thing a document needs to say.
          -->
          <div
            v-else-if="whatsapp.content_type == 'document'"
            class="flex min-w-0 cursor-pointer items-center gap-2"
            @click="() => openFileInAnotherTab(whatsapp.attach)"
          >
            <DocumentIcon class="size-8 shrink-0 rounded-md text-ink-gray-4" />
            <div class="min-w-0">
              <div class="truncate text-p-sm-medium text-ink-gray-8">
                {{ documentName(whatsapp) }}
              </div>
              <div class="text-p-xs uppercase text-ink-gray-5">
                {{ documentKind(whatsapp) || __('Document') }}
              </div>
            </div>
          </div>
          <div
            v-else-if="whatsapp.content_type == 'audio'"
            class="flex items-center gap-2"
          >
            <audio :src="whatsapp.attach" controls class="cursor-pointer" />
          </div>
          <div
            v-else-if="whatsapp.content_type == 'video'"
            class="flex-col items-center gap-2"
          >
            <video
              :src="whatsapp.attach"
              controls
              class="h-40 cursor-pointer rounded-md"
            />
            <div
              v-if="!whatsapp.message.startsWith('/files/')"
              class="mt-1.5"
              v-html="formatWhatsAppMessage(whatsapp.message)"
            />
          </div>
          <div class="-mb-1 flex shrink-0 items-end gap-1 text-ink-gray-5">
            <Tooltip :text="formatDate(whatsapp.creation, 'ddd, MMM D, YYYY')">
              <div class="text-2xs">
                {{ formatDate(whatsapp.creation, 'hh:mm a') }}
              </div>
            </Tooltip>
            <div v-if="whatsapp.type == 'Outgoing'">
              <CheckIcon
                v-if="['sent', 'Success'].includes(whatsapp.status)"
                class="size-4"
              />
              <DoubleCheckIcon
                v-else-if="['read', 'delivered'].includes(whatsapp.status)"
                class="size-4"
                :class="{ 'text-ink-blue-5': whatsapp.status == 'read' }"
              />
            </div>
          </div>
        </div>
      </div>
      <div
        v-if="!hasFailed(whatsapp)"
        class="flex items-center justify-center opacity-0 transition-all ease-in group-hover:opacity-100"
      >
        <IconPicker
          v-slot="{ togglePopover }"
          v-model="emoji"
          v-model:reaction="reaction"
          @update:modelValue="() => reactOnMessage(whatsapp.name, emoji)"
        >
          <Button
            class="rounded-full !size-6 mt-0.5"
            @click="() => (reaction = true) && togglePopover()"
          >
            <template #icon>
              <ReactIcon class="text-ink-gray-3" />
            </template>
          </Button>
        </IconPicker>
      </div>
    </div>
  </div>
</template>

<script setup>
import IconPicker from '@/components/IconPicker.vue'
import CheckIcon from '@/components/Icons/CheckIcon.vue'
import DoubleCheckIcon from '@/components/Icons/DoubleCheckIcon.vue'
import DocumentIcon from '@/components/Icons/DocumentIcon.vue'
import ReactIcon from '@/components/Icons/ReactIcon.vue'
import { formatDate, sanitizeHTML } from '@/utils'
import { useTelemetry } from 'frappe-ui/frappe'
import { Tooltip, Dropdown, createResource, toast } from 'frappe-ui'
import { ref } from 'vue'

defineProps({
  messages: { type: Array, default: () => [] },
})

const list = defineModel({ type: Object })

const { capture } = useTelemetry()

function openFileInAnotherTab(url) {
  window.open(url, '_blank')
}

function formatWhatsAppMessage(message) {
  // if message contains _text_, make it italic
  message = message.replace(/_(.*?)_/g, '<i>$1</i>')
  // if message contains *text*, make it bold
  message = message.replace(/\*(.*?)\*/g, '<b>$1</b>')
  // if message contains ~text~, make it strikethrough
  message = message.replace(/~(.*?)~/g, '<s>$1</s>')
  // if message contains ```text```, make it monospace
  message = message.replace(/```(.*?)```/g, '<code>$1</code>')
  // if message contains `text`, make it inline code
  message = message.replace(/`(.*?)`/g, '<code>$1</code>')
  // if message contains > text, make it a blockquote
  message = message.replace(/^> (.*)$/gm, '<blockquote>$1</blockquote>')
  // if contain /n, make it a new line
  message = message.replace(/\n/g, '<br>')
  // if contains *<space>text, make it a bullet point
  message = message.replace(/\* (.*?)(?=\s*\*|$)/g, '<li>$1</li>')
  message = message.replace(/- (.*?)(?=\s*-|$)/g, '<li>$1</li>')
  message = message.replace(/(\d+)\. (.*?)(?=\s*(\d+)\.|$)/g, '<li>$2</li>')

  return sanitizeHTML(message)
}

const emoji = ref('')
const reaction = ref(true)

function reactOnMessage(name, emoji) {
  createResource({
    url: 'crm.api.whatsapp.react_on_whatsapp_message',
    params: {
      emoji,
      reply_to_name: name,
    },
    auto: true,
    onSuccess() {
      capture('whatsapp_react_on_message')
      list.value.reload()
    },
    onError(error) {
      toast.error(
        error.messages?.[0] || __('Failed to add reaction to the message'),
      )
    },
  })
}

const reply = defineModel('reply', { type: Object, default: () => ({}) })

// Meta's webhook says `failed` in lowercase; a send that never left says
// `Failed`. Only the first was recognised, so a message that failed here showed
// no badge at all — and neither had any way back.
/**
 * The name of the file in a document bubble.
 *
 * An outgoing file no longer travels as `/files/…`: it goes through the signed
 * endpoint that tells Meta what it is, and the real name is a query parameter
 * there. Reading only the path would show `media` for every document sent.
 */
function documentName(message) {
  const raw = String(message?.attach || '')
  const named = /[?&]file=([^&#]+)/.exec(raw)
  const path = (named ? decodeURIComponent(named[1]) : raw).split('?')[0]
  const file = decodeURIComponent(path.split('/').pop() || '')
  // an incoming file arrives with a name Meta made up, so the caption — which
  // is what the sender actually wrote — is the better title when there is one
  return message?.message && !message.message.startsWith('/files/')
    ? message.message
    : file || __('Document')
}

function documentKind(message) {
  const name = documentName(message)
  const dot = name.lastIndexOf('.')
  return dot > 0 ? name.slice(dot + 1) : ''
}

function hasFailed(whatsapp) {
  return (whatsapp.status || '').toLowerCase() == 'failed'
}

const retrying = ref('')

function retry(whatsapp) {
  retrying.value = whatsapp.name
  createResource({
    url: 'crm.api.whatsapp.retry_whatsapp_message',
    params: { name: whatsapp.name },
    auto: true,
    onSuccess: () => {
      retrying.value = ''
      toast.success(__('Sent'))
      list.value.reload()
    },
    onError: (error) => {
      retrying.value = ''
      // Meta's own reason, which is the whole point of retrying by hand
      toast.error(error.messages?.[0] || __('It failed again'))
    },
  })
}
const replyMode = ref(false)

function messageOptions(message) {
  return [
    {
      label: 'Reply',
      onClick: () => {
        replyMode.value = true
        reply.value = {
          ...message,
          message: formatWhatsAppMessage(message.message),
        }
      },
    },
    // {
    //   label: 'Forward',
    //   onClick: () => console.log('Forward'),
    // },
    // {
    //   label: 'Delete',
    //   onClick: () => console.log('Delete'),
    // },
  ]
}

function scrollToMessage(name) {
  const element = document.getElementById(name)
  element.scrollIntoView({ behavior: 'smooth' })

  // Highlight the message
  element.classList.add('bg-yellow-100')
  setTimeout(() => {
    element.classList.remove('bg-yellow-100')
  }, 1000)
}
</script>

<style scoped>
/*
  WhatsApp's own two colours, because a conversation is read by side and by
  shade at once. Both bubbles were the same grey, which left the alignment doing
  all the work — and alignment alone is the first thing that goes when a bubble
  is wide.

  Written as literals rather than theme tokens: these are somebody else's brand,
  and pretending they are ours would mean a theme change quietly restyling
  WhatsApp.
*/
.wa-bubble {
  color: #111b21;
}
.wa-in {
  background-color: #ffffff;
}
.wa-out {
  background-color: #d9fdd3;
}

@media (prefers-color-scheme: dark) {
  .wa-bubble {
    color: #e9edef;
  }
  .wa-in {
    background-color: #202c33;
  }
  .wa-out {
    background-color: #005c4b;
  }
}
</style>
