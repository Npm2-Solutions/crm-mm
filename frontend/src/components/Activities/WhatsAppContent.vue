<!-- eslint-disable vue/no-v-html -->
<!--
  What a WhatsApp message says, whatever it is made of: words, a template, a
  picture, a sticker, a document, a voice note, a video. No frame, no clock:
  whoever draws the bubble draws those.
-->
<template>
  <div v-if="message.message_type == 'Template'" class="flex flex-col gap-1.5">
    <div v-if="message.header" class="text-base-semibold">
      {{ message.header }}
    </div>
    <div v-html="formatWhatsAppMessage(message.template)" />
    <div v-if="message.footer" class="text-xs text-ink-gray-5">
      {{ message.footer }}
    </div>
  </div>
  <div
    v-else-if="['text', 'button'].includes(message.content_type)"
    v-html="formatWhatsAppMessage(message.message)"
  />
  <!-- a sticker is a picture: it was falling through to nothing at all, so a
     sticker sent from the phone arrived as an empty bubble -->
  <div v-else-if="['image', 'sticker'].includes(message.content_type)">
    <img
      v-if="message.attach"
      :src="message.attach"
      class="max-w-full cursor-pointer rounded-md"
      :class="message.content_type == 'sticker' ? 'h-28' : 'max-h-64'"
      @click="open(message.attach)"
    />
    <!-- the row is written the moment the webhook arrives and the file is
       fetched from Meta right after, so for a second there is a message with
       no picture yet -->
    <div
      v-else
      class="flex h-40 w-40 items-center justify-center rounded-md bg-surface-alpha-gray-2"
    >
      <LoadingIndicator class="size-5 text-ink-gray-5" />
    </div>
    <div
      v-if="hasCaption(message)"
      class="mt-1.5"
      v-html="formatWhatsAppMessage(message.message)"
    />
  </div>
  <!--
    A document bubble said «Document» and nothing else: not the file name, not
    its kind, and the only way to find out was to click and hope. Which is the
    one thing a document needs to say.
  -->
  <button
    v-else-if="message.content_type == 'document'"
    class="flex min-w-0 max-w-full items-center gap-2 rounded-md bg-surface-alpha-gray-2 p-2 text-left"
    @click="open(message.attach)"
  >
    <DocumentIcon class="size-8 shrink-0 rounded-md text-ink-gray-5" />
    <span class="min-w-0">
      <span class="block truncate text-p-sm-medium">
        {{ documentName(message) }}
      </span>
      <span class="block text-p-xs uppercase text-ink-gray-5">
        {{ documentKind(message) || __('Document') }}
      </span>
    </span>
  </button>
  <div v-else-if="message.content_type == 'audio'" class="min-w-0">
    <audio
      v-if="message.attach"
      :src="message.attach"
      controls
      class="h-10 w-64 max-w-full"
    />
    <div v-else class="flex items-center gap-2 py-2 text-ink-gray-5">
      <LoadingIndicator class="size-4" />
      <span class="text-p-sm">{{ __('Loading...') }}</span>
    </div>
  </div>
  <div v-else-if="message.content_type == 'video'">
    <video
      v-if="message.attach"
      :src="message.attach"
      controls
      class="max-h-64 max-w-full rounded-md"
    />
    <div
      v-else
      class="flex h-40 w-40 items-center justify-center rounded-md bg-surface-alpha-gray-2"
    >
      <LoadingIndicator class="size-5 text-ink-gray-5" />
    </div>
    <div
      v-if="hasCaption(message)"
      class="mt-1.5"
      v-html="formatWhatsAppMessage(message.message)"
    />
  </div>
  <div
    v-else-if="message.message"
    v-html="formatWhatsAppMessage(message.message)"
  />
</template>

<script setup>
import DocumentIcon from '@/components/Icons/DocumentIcon.vue'
import { fileNameOf } from '@/utils/conversation'
import { formatWhatsAppMessage } from '@/utils/whatsappText'
import { LoadingIndicator } from 'frappe-ui'

defineProps({
  message: { type: Object, required: true },
})

function open(url) {
  if (url) window.open(url, '_blank')
}

// A photo arrives with no words of its own most of the time, and what is stored
// then is nothing. The old rows say `/files/…`, which was never a caption
// either: it was the file's own path, written into the message field.
function hasCaption(message) {
  const said = String(message?.message || '')
  return Boolean(said) && !said.startsWith('/files/')
}

/**
 * The name of the file in a document bubble.
 *
 * An outgoing file no longer travels as `/files/…`: it goes through the signed
 * endpoint that tells Meta what it is, and the real name is a query parameter
 * there. Reading only the path would show `media` for every document sent.
 */
function documentName(message) {
  // an incoming file arrives with a name Meta made up, so the caption — which
  // is what the sender actually wrote — is the better title when there is one
  if (hasCaption(message)) return message.message
  return fileNameOf(message?.attach) || __('Document')
}

function documentKind(message) {
  const name = documentName(message)
  const dot = name.lastIndexOf('.')
  return dot > 0 ? name.slice(dot + 1) : ''
}
</script>

<style scoped>
/*
  A list inside a bubble.

  The padding is the whole point. A marker is drawn outside the item's content
  box, so a list with no padding of its own draws its bullets in whatever lies
  to the left — which on a bubble is its own padding, and then the edge: the
  dots ended up outside the bubble, in the margin beside it. Half a rem of room
  puts them back inside, and keeps a wrapped line indented under its own text
  instead of under the bullet.

  `:deep` because the message is written with v-html: these rules have to reach
  content this component did not render itself.
*/
:deep(.wa-list) {
  margin: 0.125rem 0;
  padding-left: 0.75rem;
  list-style-position: outside;
}
:deep(.wa-list > li) {
  margin: 0;
}
:deep(ul.wa-list) {
  list-style-type: disc;
}
:deep(ol.wa-list) {
  list-style-type: decimal;
}
:deep(blockquote) {
  margin: 0.125rem 0;
  border-left: 3px solid currentColor;
  padding-left: 0.5rem;
  opacity: 0.85;
}
</style>
