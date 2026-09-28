<!--
  Who you are talking to, and what you decide about it.

  The middle of the screen had no name on it. The person was in the column on
  the right — as «CRM-LEAD-2026-00128» when the conversation had been opened
  from a link — and the three decisions that take a conversation off the pile
  sat there too, at the far edge from the words they are decisions about. Every
  inbox puts both where the eye already is: the name over the thread, and
  «done» and «later» beside it.
-->
<template>
  <div
    class="flex h-14 shrink-0 items-center gap-2 border-b bg-surface-base px-2 sm:gap-3 sm:px-4"
  >
    <Button
      v-if="back"
      variant="ghost"
      icon="lucide-arrow-left"
      :aria-label="__('Back to the list')"
      @click="emit('back')"
    />
    <button
      class="flex min-w-0 flex-1 items-center gap-3 rounded-lg py-1 text-left"
      :class="details ? 'hover:opacity-80' : 'cursor-default'"
      :tabindex="details ? 0 : -1"
      @click="details && emit('details')"
    >
      <PersonAvatar :name="title" :image="person.image" size="md" />
      <span class="min-w-0">
        <span class="flex min-w-0 items-center gap-2">
          <span class="truncate text-base font-semibold text-ink-gray-9">
            {{ title }}
          </span>
          <!-- what was decided, said once, next to the name it is about -->
          <Badge
            v-if="snoozedUntil"
            size="sm"
            theme="orange"
            :label="__('Back {0}', [laterLabel(snoozedUntil)])"
          />
          <Badge
            v-else-if="handled"
            size="sm"
            theme="green"
            :label="__('Dealt with')"
          />
        </span>
        <span v-if="subtitle" class="block truncate text-p-xs text-ink-gray-5">
          {{ subtitle }}
        </span>
      </span>
    </button>

    <div class="flex shrink-0 items-center gap-1">
      <!--
        Read is a thing somebody says, not a thing that happens when a chat is
        glanced at — so while it is unread, saying so is the first button, with
        its words; once read, the way back is only an icon.
      -->
      <Button
        v-if="unread"
        :variant="wide ? 'subtle' : 'ghost'"
        :label="wide ? __('Mark as read') : undefined"
        :icon="wide ? undefined : 'lucide-check-check'"
        :iconLeft="wide ? 'lucide-check-check' : undefined"
        :tooltip="wide ? undefined : __('Mark as read')"
        :aria-label="__('Mark as read')"
        :loading="busy === 'read'"
        @click="setRead(true)"
      />
      <Button
        v-else
        variant="ghost"
        icon="lucide-eye-off"
        :tooltip="__('Mark as unread')"
        :aria-label="__('Mark as unread')"
        :loading="busy === 'read'"
        @click="setRead(false)"
      />
      <Dropdown :options="snoozeOptions" align="end">
        <Button
          variant="ghost"
          icon="lucide-clock"
          :tooltip="__('Put off until later')"
          :aria-label="__('Put off until later')"
          :loading="busy === 'snooze'"
        />
      </Dropdown>
      <Button
        v-if="!handled"
        :variant="wide ? 'solid' : 'ghost'"
        :label="wide ? __('Mark as handled') : undefined"
        :icon="wide ? undefined : 'lucide-check'"
        :iconLeft="wide ? 'lucide-check' : undefined"
        :tooltip="wide ? undefined : __('Mark as handled')"
        :aria-label="__('Mark as handled')"
        :loading="busy === 'state'"
        @click="decide('Handled')"
      />
      <Button
        v-else
        variant="subtle"
        :label="wide ? __('Put it back') : undefined"
        :icon="wide ? undefined : 'lucide-rotate-ccw'"
        :iconLeft="wide ? 'lucide-rotate-ccw' : undefined"
        :tooltip="wide ? undefined : __('Put it back')"
        :aria-label="__('Put it back')"
        :loading="busy === 'state'"
        @click="decide('Open')"
      />
      <Button
        v-if="details"
        variant="ghost"
        icon="lucide-panel-right-open"
        :tooltip="__('About this person')"
        :aria-label="__('About this person')"
        @click="emit('details')"
      />
    </div>
  </div>
</template>

<script setup>
import PersonAvatar from '@/components/Conversations/PersonAvatar.vue'
import { useConversationState } from '@/composables/conversationState'
import { laterLabel as later } from '@/utils/conversation'
import { Badge, Dropdown, dayjsLocal } from 'frappe-ui'
import { computed, toRef } from 'vue'

const props = defineProps({
  person: { type: Object, default: () => ({}) },
  // on a phone: the way back to the list, which this pane replaced
  back: { type: Boolean, default: false },
  // when the panel about the person is not on screen: the way to it
  details: { type: Boolean, default: false },
  // room for words on the buttons, not only icons
  wide: { type: Boolean, default: true },
})

const emit = defineEmits(['back', 'details', 'changed'])

const { busy, unread, handled, snoozedUntil, setRead, decide, snoozeOptions } =
  useConversationState(toRef(props, 'person'), () => emit('changed'))

const title = computed(
  () =>
    props.person.lead_name ||
    props.person.organization ||
    [props.person.first_name, props.person.last_name]
      .filter(Boolean)
      .join(' ') ||
    props.person.name ||
    '',
)

// the company and the number: what somebody checks before answering
const subtitle = computed(() =>
  [props.person.lead_name && props.person.organization, props.person.mobile_no]
    .filter(Boolean)
    .join(' · '),
)

// the moment it comes back, on the reader's clock
function laterLabel(at) {
  const local = (value) => dayjsLocal(value).format('YYYY-MM-DD HH:mm:ss')
  return later(local(at), local())
}
</script>
