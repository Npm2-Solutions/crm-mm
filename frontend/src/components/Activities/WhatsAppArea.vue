<!-- eslint-disable vue/no-v-html -->
<template>
  <div>
    <!--
      Bare: inside the mixed chat the house bubble draws the frame — side,
      clock, ticks, failure, reaction — so this renders only what it alone
      knows: what was quoted, and what was said.
    -->
    <template v-if="bare">
      <div
        v-for="whatsapp in messages"
        :id="whatsapp.name"
        :key="whatsapp.name"
        class="min-w-0 break-words"
      >
        <WhatsAppQuote
          v-if="whatsapp.is_reply && whatsapp.reply_to"
          :message="whatsapp"
          @jump="scrollToMessage"
        />
        <WhatsAppContent :message="whatsapp" />
      </div>
    </template>

    <!--
      The WhatsApp view: WhatsApp's own bubble, on WhatsApp's own paper. The
      green and the paper are what make it a WhatsApp conversation rather than
      a list of messages, so they stay here and only here.
    -->
    <template v-else>
      <!--
        Focusable, so a tap shows what can be done to it (see below). The row
        rather than the bubble, so that a tap on one of the buttons keeps the
        focus in it and the bar keeps taking taps: Safari gives a tapped button
        no focus, and with the bubble the focusable one the focus left the
        message altogether.
      -->
      <div
        v-for="(whatsapp, index) in messages"
        :key="whatsapp.name"
        tabindex="-1"
        class="activity group/bubble relative flex items-center gap-1.5 outline-none"
        :class="[
          whatsapp.type == 'Outgoing' ? 'flex-row-reverse' : '',
          whatsapp.reaction ? 'mb-4' : '',
        ]"
      >
        <div
          :id="whatsapp.name"
          class="wa-bubble bubble-lift relative min-w-0 max-w-full rounded-lg px-2 pb-1 pt-1.5 text-base"
          :class="[
            whatsapp.type == 'Outgoing' ? 'wa-out' : 'wa-in',
            tailOf(index)
              ? whatsapp.type == 'Outgoing'
                ? 'bubble-tail-out rounded-tr-none'
                : 'bubble-tail-in rounded-tl-none'
              : '',
            hasFailed(whatsapp) ? 'ring-1 ring-inset ring-outline-red-3' : '',
          ]"
        >
          <WhatsAppQuote
            v-if="whatsapp.is_reply && whatsapp.reply_to"
            :message="whatsapp"
            @jump="scrollToMessage"
          />
          <!--
            The words and the clock share a line while they fit and part when
            they do not: a flex row that wraps. «ok» stays one line with its
            time beside it; a paragraph takes the width and the time drops to
            the corner underneath, the way WhatsApp itself does it.
          -->
          <div class="flex flex-wrap items-end gap-x-2">
            <div class="min-w-0 break-words">
              <WhatsAppContent :message="whatsapp" />
            </div>
            <div
              class="-mb-0.5 ml-auto flex shrink-0 items-center gap-1 pt-0.5 text-2xs leading-none text-ink-gray-5"
            >
              <!--
                Failed, in the message's own space: it used to be a badge and a
                button pinned over the top corner, sitting on the first word and
                on the clock.
              -->
              <template v-if="hasFailed(whatsapp)">
                <span class="flex items-center gap-1 text-ink-red-6">
                  <span
                    class="lucide-circle-alert size-3.5"
                    aria-hidden="true"
                  />
                  {{ __('Not delivered') }}
                </span>
                <button
                  class="mr-1.5 font-medium text-ink-red-6 underline-offset-2 hover:underline disabled:opacity-60"
                  :disabled="Boolean(retrying)"
                  @click="retry(whatsapp)"
                >
                  {{ retrying == whatsapp.name ? __('Sending…') : __('Retry') }}
                </button>
              </template>
              <!--
                Written on the phone, not here. The same number is used from the
                CRM and from the WhatsApp app in somebody's pocket, and both
                halves land in this one chat. Without saying which is which,
                «did I answer this, or did a colleague answer from his phone?»
                has no answer a week later.
              -->
              <Tooltip
                v-if="whatsapp.written_on_the_phone"
                :text="__('Sent from the phone')"
              >
                <span class="lucide-smartphone size-3" aria-hidden="true" />
              </Tooltip>
              <Tooltip :text="formatDate(whatsapp.creation, 'ddd, D MMM YYYY')">
                <span class="tabular-nums">
                  {{ clockOf(whatsapp.creation) }}
                </span>
              </Tooltip>
              <template
                v-if="whatsapp.type == 'Outgoing' && !hasFailed(whatsapp)"
              >
                <Tooltip
                  v-if="['sent', 'success'].includes(lower(whatsapp.status))"
                  :text="__('Sent')"
                >
                  <span class="inline-flex">
                    <CheckIcon class="size-3.5" />
                  </span>
                </Tooltip>
                <Tooltip
                  v-else-if="
                    ['read', 'delivered'].includes(lower(whatsapp.status))
                  "
                  :text="
                    lower(whatsapp.status) == 'read'
                      ? __('Read by them')
                      : __('Delivered to their phone')
                  "
                >
                  <span class="inline-flex">
                    <DoubleCheckIcon
                      class="size-3.5"
                      :class="{
                        'text-ink-blue-7': lower(whatsapp.status) == 'read',
                      }"
                    />
                  </span>
                </Tooltip>
              </template>
            </div>
          </div>
          <span
            v-if="whatsapp.reaction"
            class="absolute -bottom-3 flex h-6 min-w-6 items-center justify-center rounded-full bg-surface-elevation-2 px-1 text-sm leading-none shadow-sm ring-1 ring-outline-gray-1"
            :class="whatsapp.type == 'Outgoing' ? 'right-3' : 'left-3'"
          >
            {{ whatsapp.reaction }}
          </span>
        </div>
        <!--
          Reply and react show with the pointer on the message, and — where
          there is no pointer, on a phone — once the message is tapped: they
          were hover-only, and a finger cannot hover, so nobody on a phone
          could answer a message by quoting it. There they are a bar above the
          message (`azioni-della-bolla`, index.css), leaving the bubble the
          row's whole width.
        -->
        <MessageActions
          v-if="!hasFailed(whatsapp)"
          class="azioni-della-bolla opacity-0 transition-opacity focus-within:opacity-100 group-focus-within/bubble:opacity-100 group-hover/bubble:opacity-100"
          :data-lato="whatsapp.type == 'Outgoing' ? 'out' : 'in'"
          @reply="answer(whatsapp)"
          @react="(emoji) => react(whatsapp, emoji)"
        />
      </div>
    </template>
  </div>
</template>

<script setup>
import CheckIcon from '@/components/Icons/CheckIcon.vue'
import DoubleCheckIcon from '@/components/Icons/DoubleCheckIcon.vue'
import MessageActions from '@/components/Activities/MessageActions.vue'
import WhatsAppContent from '@/components/Activities/WhatsAppContent.vue'
import WhatsAppQuote from '@/components/Activities/WhatsAppQuote.vue'
import { useWhatsAppActions } from '@/composables/whatsappActions'
import { formatDate } from '@/utils'
import {
  clockOf as clock,
  hasFailed as failed,
  opensRun,
} from '@/utils/conversation'
import { Tooltip, dayjsLocal } from 'frappe-ui'
import { appLocale } from '@/utils/locale'

const props = defineProps({
  messages: { type: Array, default: () => [] },
  // inside the mixed chat the bubble is drawn by the house component, so this
  // one renders only what it alone knows: the quote and the message
  bare: { type: Boolean, default: false },
  // whether the bubble carries its tail, when the caller knows (one message
  // at a time, from the stream); left out, each message works it out from the
  // one before it
  tail: { type: Boolean, default: null },
})

function tailOf(index) {
  return props.tail ?? opensRun(props.messages, index)
}

const list = defineModel({ type: Object })
const reply = defineModel('reply', { type: Object, default: () => ({}) })

const { retrying, retry, react, answer } = useWhatsAppActions({ list, reply })

function lower(value) {
  return String(value || '').toLowerCase()
}

function hasFailed(message) {
  return failed({ ...message, activity_type: 'whatsapp' })
}

// the reader's clock, in the reader's words — the day is on the marker above
function clockOf(at) {
  return at
    ? clock(dayjsLocal(at).format('YYYY-MM-DD HH:mm:ss'), appLocale())
    : ''
}

function scrollToMessage(name) {
  const element = document.getElementById(name)
  if (!element) return
  element.scrollIntoView({ behavior: 'smooth', block: 'center' })
  // a moment of highlight, so the eye finds which one it jumped to
  element.classList.add('wa-flash')
  setTimeout(() => element.classList.remove('wa-flash'), 1200)
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

  Dark by the app's theme, not the computer's. They followed
  `prefers-color-scheme`, so a CRM switched to dark on a laptop left in light
  mode showed WhatsApp's white bubbles on a dark page, and the other way round.

  Written `[data-theme='dark'] .wa-in`, which Vue scopes on its last part.
  They were `:global([data-theme='dark']) .wa-in`, and Vue compiles that to
  `[data-theme=dark]` alone: the dark colours landed on the page's <html> and
  the bubbles stayed light.
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
[data-theme='dark'] .wa-bubble {
  color: #e9edef;
}
[data-theme='dark'] .wa-in {
  background-color: #202c33;
}
[data-theme='dark'] .wa-out {
  background-color: #005c4b;
}

.wa-flash {
  animation: wa-flash 1.2s ease-out;
}
@keyframes wa-flash {
  0%,
  40% {
    box-shadow: 0 0 0 3px rgb(250 204 21 / 0.6);
  }
  100% {
    box-shadow: none;
  }
}
</style>
