<!--
  Where the new messages begin.

  A conversation opened with something unread in it used to look exactly like
  one without: the count was on the row in the list, and inside, nothing said
  which of forty bubbles were the ones it was counting. Every messenger answers
  it with a line across the thread, and so does this one.

  It also says, where it matters, the one thing the screen cannot show: whether
  the customer is told. On WhatsApp the blue ticks go when somebody here reads
  the conversation — with the button, by answering, by marking it handled —
  and only if the site sends them at all. Opening it, as you just did, is not
  one of those moments, and this is the place to say so.

  Blue while unread; grey once read, and still there until you move on, so it
  does not vanish from under the messages it points at.
-->
<template>
  <div
    class="flex items-center gap-3 px-3 py-2 sm:px-4"
    role="separator"
    data-new-line
    :aria-label="caption ? `${title}. ${caption}` : title"
  >
    <span
      class="flex-1 border-t"
      :class="unread ? 'border-outline-blue-3' : 'border-outline-gray-3'"
      aria-hidden="true"
    />
    <span
      class="flex max-w-[80%] flex-col items-center rounded-lg px-3 py-1 text-center shadow-sm"
      :class="
        unread
          ? 'bg-surface-blue-2 text-ink-blue-8'
          : 'bg-surface-elevation-2 text-ink-gray-6 dark:bg-surface-gray-2'
      "
    >
      <span class="text-p-xs font-semibold">{{ title }}</span>
      <span v-if="caption" class="text-p-xs">{{ caption }}</span>
    </span>
    <span
      class="flex-1 border-t"
      :class="unread ? 'border-outline-blue-3' : 'border-outline-gray-3'"
      aria-hidden="true"
    />
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  count: { type: Number, default: 0 },
  // still unread, or read since the conversation was opened
  unread: { type: Boolean, default: true },
  // whether any of the new ones came by WhatsApp, the channel with blue ticks
  whatsapp: { type: Boolean, default: false },
  // whether this site sends read receipts at all
  receipts: { type: Boolean, default: false },
})

const title = computed(() =>
  props.count === 1
    ? __('1 new message')
    : __('{0} new messages', [props.count]),
)

const caption = computed(() => {
  if (!props.whatsapp) return props.unread ? '' : __('Read')
  if (!props.receipts) {
    return props.unread
      ? __('They get no blue ticks from this CRM')
      : __('Read · they get no blue ticks from this CRM')
  }
  return props.unread
    ? __('They see the blue ticks when you reply or mark it read')
    : __('Read · they have the blue ticks')
})
</script>
