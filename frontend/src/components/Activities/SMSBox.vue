<template>
  <div class="px-1.5 pb-1.5 pt-1" v-bind="$attrs">
    <div class="flex items-end gap-1">
      <Textarea
        ref="textareaRef"
        v-model="content"
        variant="ghost"
        class="min-h-9 w-full resize-none bg-transparent py-2 text-p-base text-ink-gray-9 placeholder-ink-gray-4"
        :rows="1"
        :placeholder="__('Write a text message…')"
        @keydown.enter.stop="(e) => sendTextMessage(e)"
      />
      <div class="flex h-9 shrink-0 items-center">
        <Button
          variant="solid"
          icon="lucide-send-horizontal"
          :aria-label="__('Send')"
          :tooltip="isMobileView ? __('Send') : `${__('Send')} (Enter)`"
          :disabled="!content.trim()"
          @click="sendSMS"
        />
      </div>
    </div>
    <!--
      The one message whose length costs money, so it says how long it is the
      way the carrier counts it: past 160 characters it is two messages, and a
      single «È» — which the SMS alphabet does not have — makes it 70 a message
      without anybody noticing.
    -->
    <div
      v-if="content"
      class="flex items-center justify-end gap-2 px-2 pb-0.5 text-p-xs tabular-nums text-ink-gray-5"
    >
      <Tooltip
        v-if="length.unicode"
        :text="
          __(
            'A character outside the SMS alphabet (an emoji, or È) makes every message hold 70 characters instead of 160.',
          )
        "
      >
        <span class="text-ink-amber-7">{{ __('Special characters') }}</span>
      </Tooltip>
      <span>
        {{ length.characters }}/{{ length.perSegment * length.segments }}
      </span>
      <span v-if="length.segments > 1" class="font-medium text-ink-gray-7">
        {{ __('{0} messages', [length.segments]) }}
      </span>
    </div>
  </div>
</template>

<script setup>
import { isMobileView } from '@/composables/breakpoints'
import { markAnswered } from '@/composables/conversationState'
import { useDraft } from '@/composables/drafts'
import { useGrowingTextarea } from '@/composables/growingTextarea'
import { smsSegments } from '@/utils/conversation'
import { useTelemetry } from 'frappe-ui/frappe'
import { createResource, Textarea, Tooltip, toast } from 'frappe-ui'
import { computed, ref, nextTick } from 'vue'

defineOptions({ inheritAttrs: false })

const props = defineProps({
  doctype: { type: String, default: '' },
})

const doc = defineModel({ type: Object, default: () => ({}) })
const sms = defineModel('sms', { type: Object, default: () => ({}) })

const { capture } = useTelemetry()

const textareaRef = ref(null)
// kept per record, like every other draft
const content = useDraft('smsDraft', props.doctype, doc.value.name)

// as tall as what is in it, up to six lines
const { fit } = useGrowingTextarea(textareaRef, content)

const length = computed(() => smsSegments(content.value))

function show() {
  nextTick(() => {
    fit()
    textareaRef.value?.el?.focus()
  })
}

// Enter sends at a desk; on a phone it is a new line, and the arrow sends.
function sendTextMessage(event) {
  if (event.shiftKey || event.isComposing || isMobileView.value) return
  event.preventDefault()
  sendSMS()
}

function sendSMS() {
  if (!content.value.trim()) return
  const message = content.value
  content.value = ''
  capture('sms_send_message')
  createResource({
    url: 'crm.api.sms.send_sms',
    params: {
      reference_doctype: props.doctype,
      reference_name: doc.value.name,
      to: doc.value.mobile_no,
      message,
    },
    auto: true,
    onSuccess: () => {
      sms.value.reload()
      // nobody answers what they have not read
      markAnswered(props.doctype, doc.value.name)
    },
    onError: (error) => {
      // what was written is not lost to a failed send
      content.value = content.value || message
      toast.error(error.messages?.[0] || __('Failed to send SMS'))
    },
  })
}

defineExpose({ show })
</script>
