<!--
  Copyright (c) 2026, NPM2 Solutions Srl and contributors
  For license information, please see license.txt

  Who you are talking to, and what you decide about it.

  The middle of the screen had no name on it. The person was in the column on
  the right — as «CRM-LEAD-2026-00128» when the conversation had been opened
  from a link — and the three decisions that take a conversation off the pile
  sat there too, at the far edge from the words they are decisions about. Every
  inbox puts both where the eye already is: the name over the thread, and
  «done» and «later» beside it.

  On a phone, with a chat open, it is the page's header (`inTestata`), beside
  the phone at the top right: the page's own row, «Conversations» and its
  refresh, took 42px over a chat that had none to spare. Its buttons are 40px
  there, side by side, and the person is opened from their name.
-->
<template>
  <!-- icone-a-dito: the icon buttons 40px each on a phone (telefono.css) -->
  <div
    class="icone-a-dito flex shrink-0 items-center"
    :class="
      inTestata
        ? 'h-12 gap-1'
        : 'h-14 gap-2 border-b bg-surface-base px-2 sm:gap-3 sm:px-4'
    "
  >
    <Button
      v-if="back"
      variant="ghost"
      icon="lucide-arrow-left"
      :aria-label="__('Back to the list')"
      @click="emit('back')"
    />
    <button
      class="flex min-w-0 flex-1 items-center rounded-lg py-1 text-left"
      :class="[
        details ? 'hover:opacity-80' : 'cursor-default',
        inTestata ? 'gap-2' : 'gap-3',
      ]"
      :tabindex="details ? 0 : -1"
      @click="details && emit('details')"
    >
      <PersonAvatar :name="title" :image="person.image" size="md" />
      <span class="min-w-0">
        <span class="block truncate text-base font-semibold text-ink-gray-9">
          {{ title }}
        </span>
        <!--
          What was decided, first on the line under the name: beside the name
          it squeezed it — «Gi…» next to «Back tomorrow 09:00» — and the name
          is the one thing in this header that must never be cut.
        -->
        <span
          class="flex min-w-0 items-center gap-1.5 text-p-xs text-ink-gray-5"
        >
          <Tooltip
            v-if="snoozedUntil"
            :text="__('Put off: back in Open then, or sooner if they write')"
          >
            <span
              class="flex shrink-0 items-center gap-1 font-medium text-ink-orange-8"
            >
              <span class="lucide-clock size-3" aria-hidden="true" />
              {{ __('Back {0}', [laterLabel(snoozedUntil)]) }}
            </span>
          </Tooltip>
          <Tooltip
            v-else-if="handled"
            :text="__('Out of Open until they write again')"
          >
            <span
              class="flex shrink-0 items-center gap-1 font-medium text-ink-green-8"
            >
              <span class="lucide-check size-3" aria-hidden="true" />
              {{ __('Handled') }}
            </span>
          </Tooltip>
          <span v-if="subtitle && (snoozedUntil || handled)" aria-hidden="true">
            ·
          </span>
          <span v-if="subtitle" class="truncate">{{ subtitle }}</span>
        </span>
      </span>
    </button>

    <div class="flex shrink-0 items-center" :class="inTestata ? '' : 'gap-1'">
      <!--
        Read is a thing somebody says, not a thing that happens when a chat is
        glanced at — so while there is something new, saying so is the first
        button, with its words and, on hover, what it does beyond the badge.
        Once read, the button becomes the answer to «who read this, and when»,
        with the way back behind it.
      -->
      <!-- in the blue of the dot and the count it clears, so that on a phone,
           where both are an icon, the thing to do and the thing done differ -->
      <Button
        v-if="unread"
        theme="blue"
        variant="subtle"
        :label="wide ? __('Mark as read') : undefined"
        :icon="wide ? undefined : 'lucide-check-check'"
        :iconLeft="wide ? 'lucide-check-check' : undefined"
        :tooltip="readTip"
        :aria-label="__('Mark as read')"
        :loading="busy === 'read'"
        @click="setRead(true)"
      />
      <Dropdown v-else :options="readOptions" align="end">
        <Button
          variant="ghost"
          class="text-ink-gray-6"
          :label="wide ? seenLabel : undefined"
          :icon="wide ? undefined : 'lucide-check-check'"
          :iconLeft="wide ? 'lucide-check-check' : undefined"
          :tooltip="seenLine"
          :aria-label="seenLine"
          :loading="busy === 'read'"
        />
      </Dropdown>
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
        :tooltip="handleTip"
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
        :tooltip="__('Back to Open, with the conversations still going on')"
        :aria-label="__('Put it back')"
        :loading="busy === 'state'"
        @click="decide('Open')"
      />
      <!-- in the page's header on a phone the name opens the person, as in a
           phone's messengers: the button would take the name's room -->
      <Button
        v-if="details && !inTestata"
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
import { usersStore } from '@/stores/users'
import {
  laterLabel as later,
  listTime,
  momentLabel,
} from '@/utils/conversation'
import { Dropdown, Tooltip, dayjsLocal } from 'frappe-ui'
import { computed, toRef } from 'vue'
import { appLocale } from '@/utils/locale'
import { leggibile } from '@/utils/telefono'

const props = defineProps({
  person: { type: Object, default: () => ({}) },
  // on a phone: the way back to the list, which this pane replaced
  back: { type: Boolean, default: false },
  // when the panel about the person is not on screen: the way to it
  details: { type: Boolean, default: false },
  // room for words on the buttons, not only icons
  wide: { type: Boolean, default: true },
  // drawn in the page's header, on a phone with a chat open
  inTestata: { type: Boolean, default: false },
})

const emit = defineEmits(['back', 'details', 'changed'])

const {
  busy,
  receipts,
  unread,
  handled,
  snoozedUntil,
  setRead,
  decide,
  snoozeOptions,
} = useConversationState(toRef(props, 'person'), () => emit('changed'))

const { getUser } = usersStore()

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
  [
    props.person.lead_name && props.person.organization,
    leggibile(props.person.mobile_no),
  ]
    .filter(Boolean)
    .join(' · '),
)

// the server's clock, moved onto the reader's
function local(at) {
  return dayjsLocal(at || undefined).format('YYYY-MM-DD HH:mm:ss')
}

// the moment it comes back, on the reader's clock
function laterLabel(at) {
  return later(local(at), local(), appLocale())
}

// What pressing a button does beyond the badge — which is the part nobody can
// see from here: whether the customer is told.
const readTip = computed(() =>
  receipts.value
    ? __(
        'Clears the badge for the whole team, and WhatsApp shows them the blue ticks',
      )
    : __(
        'Clears the badge for the whole team. They are not sent a read receipt',
      ),
)

const handleTip = computed(() => {
  const moves = __('Moves it to Handled until they write again')
  if (!unread.value) return moves
  return receipts.value
    ? __('{0}. It also marks it read, and they get the blue ticks', [moves])
    : __('{0}. It also marks it read', [moves])
})

// Who read it, the way the header can say it in two words: their first name,
// or «you».
const seenBy = computed(() => {
  const user = props.person.conversation_seen_by
  if (!user) return ''
  if (user === getUser()?.name) return __('you')
  return getUser(user)?.full_name || user
})

const seenLabel = computed(() => {
  if (!seenBy.value) return __('Read', null, 'Message read')
  const first = seenBy.value.split(' ')[0]
  const at = props.person.conversation_seen_until
  return at
    ? __('Read by {0} · {1}', [
        first,
        listTime(local(at), local(), appLocale()),
      ])
    : __('Read by {0}', [first])
})

// the whole of it, for the tooltip and the heading of the menu
const seenLine = computed(() => {
  const at = props.person.conversation_seen_until
  if (!seenBy.value) return __('Nothing new since it was last read')
  if (!at) return __('Read by {0}', [seenBy.value])
  return __('Read by {0} · {1}', [
    seenBy.value,
    momentLabel(local(at), appLocale()),
  ])
})

const readOptions = computed(() => [
  {
    group: seenLine.value,
    options: [
      {
        label: __('Mark as unread'),
        icon: 'lucide-circle-dot',
        description: receipts.value
          ? __('The blue ticks already sent stay')
          : __('Puts the dot back, for the whole team'),
        onClick: () => setRead(false),
      },
    ],
  },
])
</script>
