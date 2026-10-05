<!-- eslint-disable vue/no-v-html -->
<!--
  Everything said to this person, in one chat.

  «All» is a chat, not a report: whatever the channel, a message somebody sent
  is a bubble on their side and a message we sent is a bubble on ours. That is
  the one arrangement everybody already knows how to read, and it is the reason
  somebody can work a whole day from this one view without opening the others.

  Each encoding means one thing and never another:

  - **the side and the fill say who** — theirs on the left on the raised
    surface, ours on the right in the house blue. On every channel, so the eye
    learns it once. (The fill had been made to carry the channel instead, with
    ours one shade deeper than theirs: one per cent of lightness apart, and a
    conversation that is mostly WhatsApp became a column of identical green.)
  - **the channel says itself in its mark** — the glyph beside the clock, in
    the channel's colour: green WhatsApp, blue email, violet SMS.
  - **amber is ours and nobody else's** — a note we wrote each other, the one
    thing here the customer will never see.

  What is not one side talking to the other takes no side: a call, a stage that
  moved, an appointment, sit in the middle the way a messenger puts its own
  notices between the messages.

  Each channel on its own then gets the view that suits it: WhatsApp its own
  paper and its own green, comments and calls a thread down the side, email
  full-width cards — an email thread was never a chat.
-->
<template>
  <div
    ref="root"
    class="relative min-h-full"
    :class="
      wallpaper ? 'wa-wallpaper' : 'bg-surface-gray-2 dark:bg-surface-base'
    "
  >
    <!--
      The day you are looking at, while you scroll, and only then.

      It was a marker per day pinned to the top for as long as its day was on
      screen — which at rest meant a date chip sitting on top of the first
      message under it, over its words. Now each day has its marker where the
      day begins, in the flow, covering nothing; and this one floats in while
      you scroll, so a long day does not lose its date, and goes once you stop.
    -->
    <div class="pointer-events-none sticky top-0 z-30 h-0" aria-hidden="true">
      <Transition
        enter-active-class="transition duration-150 ease-out"
        enter-from-class="-translate-y-1 opacity-0"
        leave-active-class="transition duration-500 ease-in"
        leave-to-class="opacity-0"
      >
        <div v-if="floating" class="flex justify-center pt-2">
          <span :class="CHIP">{{ floating }}</span>
        </div>
      </Transition>
    </div>

    <div class="flex w-full flex-col pb-4">
      <section
        v-for="group in days"
        :key="group.key"
        :data-day="group.day"
        class="flex flex-col"
      >
        <div v-if="group.day" class="flex justify-center pb-1 pt-4">
          <span :class="CHIP">{{ group.label }}</span>
        </div>

        <!-- comments on their own: a thread, not a chat, because a note is
           addressed to nobody and a side would invent a recipient -->
        <div
          v-if="channel === 'comment'"
          class="flex flex-col px-3 pt-2 sm:px-4"
        >
          <TimelineEntry
            v-for="row in group.rows"
            :key="row.key"
            class="activity"
            :channel="row.channel"
            :icon="iconFor(row.channel)"
          >
            <CommentArea
              v-if="row.channel === 'comment'"
              bare
              :time="timeOf(row)"
              :activity="row.item"
              @reload="emit('reload')"
            />
            <slot v-else name="other" :item="row.item" :row="row" />
          </TimelineEntry>
        </div>

        <!--
          The call register. A call has no text to read, so a bubble would be a
          speech balloon with no speech in it: what there is to know is who,
          which way, how long, and whether there is a recording — which is a
          row, on a thread.
        -->
        <div
          v-else-if="channel === 'call'"
          class="flex flex-col px-3 pt-2 sm:px-4"
        >
          <TimelineEntry
            v-for="row in group.rows"
            :key="row.key"
            class="activity"
            :channel="row.channel"
            :icon="callIconFor(row.item)"
            :incoming="row.direction === 'in'"
          >
            <CallArea v-if="row.channel === 'call'" :activity="row.item" />
            <slot v-else name="other" :item="row.item" :row="row" />
          </TimelineEntry>
        </div>

        <!-- email on its own: full width, because a thread is not a chat -->
        <div
          v-else-if="channel === 'email'"
          class="flex flex-col gap-2 px-3 pt-2 sm:px-4"
        >
          <template v-for="row in group.rows" :key="row.key">
            <NewMessagesLine
              v-if="lineAt(row, true)"
              class="!px-0"
              v-bind="lineProps"
            />
            <div
              class="activity rounded-lg border bg-surface-elevation-2 p-3 shadow-sm dark:bg-surface-gray-2"
              :class="
                row.direction === 'in'
                  ? 'border-l-2 border-outline-blue-3'
                  : 'border-outline-gray-2'
              "
            >
              <!-- its name as its id: a notification's link lands on it -->
              <EmailArea
                :id="row.item.name"
                :activity="row.item"
                :emailBox="emailBox"
              />
            </div>
            <NewMessagesLine
              v-if="lineAt(row, false)"
              class="!px-0"
              v-bind="lineProps"
            />
          </template>
        </div>

        <template v-else>
          <div
            v-for="row in group.rows"
            :key="row.key"
            class="activity"
            :class="spacingOf(row)"
          >
            <NewMessagesLine v-if="lineAt(row, true)" v-bind="lineProps" />
            <!-- said to somebody: a side, and on the first of a run a tail
               pointing to it -->
            <div
              v-if="row.bubble"
              class="flex px-3 sm:px-4"
              :class="row.direction === 'out' ? 'justify-end' : 'justify-start'"
            >
              <div
                class="min-w-0 max-w-[min(85%,40rem)]"
                :class="row.direction === 'out' ? 'pr-2' : 'pl-2'"
              >
                <!--
                  WhatsApp keeps its own bubble in its own view: the green and
                  the paper are what make that view a WhatsApp conversation
                  rather than a list of messages.
                -->
                <WhatsAppArea
                  v-if="channel === 'whatsapp' && row.channel === 'whatsapp'"
                  v-model="whatsappMessages"
                  v-model:reply="reply"
                  :messages="[row.item]"
                  :tail="row.startsRun"
                />
                <SMSArea
                  v-else-if="channel === 'sms' && row.channel === 'sms'"
                  :messages="[row.item]"
                  :tail="row.startsRun"
                />
                <ChatBubble
                  v-else
                  :channel="row.channel"
                  :icon="channel === 'all' ? iconFor(row.channel) : null"
                  :label="LABELS[row.channel] || ''"
                  :mine="row.direction === 'out'"
                  :tail="row.startsRun"
                  :speaker="speakerFor(row)"
                  :time="timeOf(row)"
                  :moment="momentOf(row)"
                  :phone="Boolean(row.item?.written_on_the_phone)"
                  :status="row.item?.status || ''"
                  :failed="row.channel !== 'email' && hasFailed(row.item)"
                  :failure="row.item?.error_message || ''"
                  :retryable="row.channel === 'whatsapp'"
                  :retrying="retrying === row.item?.name"
                  :reaction="row.item?.reaction || ''"
                  @retry="retry(row.item)"
                >
                  <WhatsAppArea
                    v-if="row.channel === 'whatsapp'"
                    v-model="whatsappMessages"
                    v-model:reply="reply"
                    bare
                    :messages="[row.item]"
                  />
                  <SMSArea
                    v-else-if="row.channel === 'sms'"
                    bare
                    :messages="[row.item]"
                  />
                  <EmailArea
                    v-else
                    :id="row.item.name"
                    bare
                    :activity="row.item"
                    :emailBox="emailBox"
                  />
                  <template
                    v-if="row.channel === 'whatsapp' && !hasFailed(row.item)"
                    #actions
                  >
                    <MessageActions
                      :archivable="canArchive && Boolean(row.item.attach)"
                      @reply="answer(row.item)"
                      @react="(emoji) => react(row.item, emoji)"
                      @archive="archiving = row.item"
                    />
                  </template>
                </ChatBubble>
              </div>
            </div>

            <!--
              A call has no words, so it gets no balloon: every messenger puts
              calls in the middle, as a notice — which way, how long — and so
              does this. A missed one is the one notice in red.
            -->
            <HappenedCard
              v-else-if="row.channel === 'call'"
              :icon="callIconFor(row.item)"
              :alarm="isMissed(row.item)"
              :when="timeOf(row)"
            >
              <CallArea :activity="row.item" bare />
            </HappenedCard>

            <!--
              Addressed to nobody, so it sits in the middle. These are the other
              half of the history: what was actually *done* between one message
              and the next, which is what the New menu at the top creates.
            -->
            <HappenedCard
              v-else-if="row.channel === 'comment'"
              kind="note"
              card
            >
              <CommentArea
                bare
                :time="timeOf(row)"
                :activity="row.item"
                @reload="emit('reload')"
              />
            </HappenedCard>

            <HappenedCard
              v-else-if="row.channel === 'note'"
              kind="note"
              :icon="NoteIcon"
              :title="__('Note')"
              :when="timeOf(row)"
              card
            >
              <div class="font-medium">{{ row.item.data?.title }}</div>
              <div
                v-if="row.item.data?.content"
                class="prose-sm max-w-none text-ink-gray-7"
                v-html="sanitizeHTML(row.item.data.content)"
              />
            </HappenedCard>

            <HappenedCard
              v-else-if="row.channel === 'appointment'"
              :icon="CalendarIcon"
              :title="__('Appointment')"
              :when="momentLabel(localOf(row.item.data?.starts_on))"
              card
              opens
              @open="openOnCalendar('appointment', row.item)"
            >
              <div class="flex flex-wrap items-center gap-2">
                <span class="font-medium">
                  {{ nomeDellAppuntamento(row.item.data) }}
                </span>
                <!-- which session of its cycle, as the agenda says it -->
                <span
                  v-if="laSeduta(row.item.data?.cycle, __)"
                  class="text-ink-gray-6"
                >
                  {{ laSeduta(row.item.data.cycle, __) }}
                </span>
                <Badge
                  v-if="row.item.data?.status"
                  size="sm"
                  :theme="appointmentTheme(row.item.data.status)"
                  :label="__(row.item.data.status)"
                />
              </div>
            </HappenedCard>

            <HappenedCard
              v-else-if="row.channel === 'event'"
              :icon="CalendarIcon"
              :title="__('Event')"
              :when="momentLabel(localOf(row.item.data?.starts_on))"
              card
              opens
              @open="openOnCalendar('event', row.item)"
            >
              <span class="font-medium">{{ row.item.data?.subject }}</span>
            </HappenedCard>

            <HappenedCard
              v-else-if="row.channel === 'task'"
              :icon="TaskIcon"
              :title="__('Task')"
              :when="timeOf(row)"
              card
            >
              <div class="flex flex-wrap items-center gap-2">
                <span
                  class="font-medium"
                  :class="
                    row.item.data?.status === 'Done'
                      ? 'text-ink-gray-5 line-through'
                      : ''
                  "
                >
                  {{ row.item.data?.title }}
                </span>
                <Badge
                  v-if="row.item.data?.status"
                  size="sm"
                  :theme="row.item.data.status === 'Done' ? 'green' : 'gray'"
                  :label="__(row.item.data.status)"
                />
              </div>
            </HappenedCard>

            <!--
              An invoice. The one row here that is money, so it says the amount
              at a size somebody can read from across the desk, and the badge is
              the only colour on it: a refused transmission is the single state
              in this whole stream that is somebody's job to fix today.
            -->
            <HappenedCard
              v-else-if="row.channel === 'invoice'"
              :icon="MoneyIcon"
              :title="invoiceTitle(row.item.data)"
              :when="timeOf(row)"
              card
            >
              <div class="flex flex-wrap items-center gap-2">
                <span class="text-lg font-semibold text-ink-gray-8">
                  {{ amountOf(row.item.data) }}
                </span>
                <Badge
                  v-if="statusOf(row.item.data)"
                  size="sm"
                  :theme="invoiceStatusTheme(statusOf(row.item.data))"
                  :label="statusLabel(statusOf(row.item.data))"
                />
                <Badge
                  v-if="row.item.data?.docstatus === 0"
                  size="sm"
                  theme="gray"
                  :label="__('Draft')"
                />
                <Button
                  class="ml-auto"
                  variant="ghost"
                  size="sm"
                  :label="__('Open', null, 'Action')"
                  @click="apriFattura(row.item.data.name)"
                />
              </div>
            </HappenedCard>

            <!--
              A visit. Health data: whoever may read it reads it in the Clinic
              tab, where every reading is logged. Here there is only that it
              happened and who saw the person, behind a padlock.
            -->
            <HappenedCard
              v-else-if="row.channel === 'clinical'"
              :icon="LockIcon"
              :title="
                row.item.data?.kind === 'Note'
                  ? __('Clinical note')
                  : __('Visit')
              "
              :when="timeOf(row)"
              card
            >
              <div class="flex flex-wrap items-center gap-2">
                <span class="text-p-sm text-ink-gray-7">
                  {{ row.item.data?.practitioner_name }}
                </span>
                <Badge
                  v-if="row.item.data?.draft"
                  size="sm"
                  theme="gray"
                  :label="__('Draft')"
                />
              </div>
              <div class="mt-0.5 text-p-xs text-ink-gray-5">
                {{
                  row.item.data?.locked
                    ? __('Only the care team reads it')
                    : __('Read it in the Clinic tab')
                }}
              </div>
            </HappenedCard>

            <!--
              The stage moved. Every other field that changes is bookkeeping and
              reads as one quiet line; this one is the point of the whole
              record, so it is the line the eye is allowed to stop on.
            -->
            <HappenedCard
              v-else-if="isStageChange(row.item)"
              kind="stage"
              :icon="StageIcon"
              :when="timeOf(row)"
            >
              <slot name="other" :item="row.item" :row="row" />
            </HappenedCard>

            <HappenedCard v-else :when="timeOf(row)">
              <slot name="other" :item="row.item" :row="row" />
            </HappenedCard>
            <NewMessagesLine v-if="lineAt(row, false)" v-bind="lineProps" />
          </div>
        </template>
      </section>

      <!--
        A channel with nothing in it says so. It was a grey pane with nothing on
        it, which reads as «still loading» or «broken» — never as «you have not
        written to this person by SMS yet».
      -->
      <div
        v-if="!days.length"
        class="flex flex-col items-center gap-2 px-6 py-16 text-center"
      >
        <component :is="iconFor(channel)" class="size-6 text-ink-gray-4" />
        <span class="text-p-sm text-ink-gray-6">{{ emptyText }}</span>
      </div>
    </div>
    <!-- a file the person sent, filed among their documents -->
    <DocumentDialog
      v-if="canArchive"
      v-model="archivingOpen"
      :message="archiving?.name"
      :message-file-name="fileNameOf(archiving)"
      :suggested-title="(archiving?.message || '').trim().slice(0, 80)"
      @saved="toast.success(__('Added to the documents'))"
    />
  </div>
</template>

<script setup>
import CallArea from '@/components/Activities/CallArea.vue'
import DocumentDialog from '@/components/Documents/DocumentDialog.vue'
import ChatBubble from '@/components/Activities/ChatBubble.vue'
import CommentArea from '@/components/Activities/CommentArea.vue'
import EmailArea from '@/components/Activities/EmailArea.vue'
import HappenedCard from '@/components/Activities/HappenedCard.vue'
import { nomeDellAppuntamento } from '@/utils/schedaPersona'
import { laSeduta } from '@/utils/cicli'
import MessageActions from '@/components/Activities/MessageActions.vue'
import NewMessagesLine from '@/components/Activities/NewMessagesLine.vue'
import SMSArea from '@/components/Activities/SMSArea.vue'
import TimelineEntry from '@/components/Activities/TimelineEntry.vue'
import WhatsAppArea from '@/components/Activities/WhatsAppArea.vue'
import CalendarIcon from '@/components/Icons/CalendarIcon.vue'
import CommentIcon from '@/components/Icons/CommentIcon.vue'
import DeclinedCallIcon from '@/components/Icons/DeclinedCallIcon.vue'
import DotIcon from '@/components/Icons/DotIcon.vue'
import Email2Icon from '@/components/Icons/Email2Icon.vue'
import InboundCallIcon from '@/components/Icons/InboundCallIcon.vue'
import MissedCallIcon from '@/components/Icons/MissedCallIcon.vue'
import MoneyIcon from '@/components/Icons/MoneyIcon.vue'
import NoteIcon from '@/components/Icons/NoteIcon.vue'
import OutboundCallIcon from '@/components/Icons/OutboundCallIcon.vue'
import PhoneIcon from '@/components/Icons/PhoneIcon.vue'
import SMSIcon from '@/components/Icons/SMSIcon.vue'
import TaskIcon from '@/components/Icons/TaskIcon.vue'
import WhatsAppIcon from '@/components/Icons/WhatsAppIcon.vue'
import { useFattura } from '@/composables/fattura'
import { useWhatsAppActions } from '@/composables/whatsappActions'
import { useTimelinePreferences } from '@/composables/useTimelinePreferences'
import { usersStore } from '@/stores/users'
import { sanitizeHTML } from '@/utils'
import {
  buildStream,
  clockOf,
  colleagueOf,
  dayLabel,
  groupByDay,
  hasFailed,
  isStageChange,
  momentLabel as moment,
  newSince,
  speakerOf,
} from '@/utils/conversation'
import {
  formatEuro,
  invoiceLabel,
  invoiceStatusTheme,
  statusLabel,
  isCreditNote,
  worstStatus,
} from '@/utils/invoicing'
import { Badge, dayjs, dayjsLocal, toast } from 'frappe-ui'
import { computed, h, onBeforeUnmount, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { appLocale } from '@/utils/locale'

const props = defineProps({
  items: { type: Array, default: () => [] },
  channel: { type: String, default: 'all' },
  modalRef: { type: Object, default: null },
  // the composer, which is where «Reply» on an email has to land. It was never
  // passed down: the reply buttons inside the chat wrote into an empty object
  // and nothing opened.
  emailBox: { type: Object, default: null },
  // whose record this is. WhatsApp only supplies a profile name when the person
  // publishes one, and a bare number standing where a name goes is unreadable
  // on a record that knows exactly whose number it is.
  them: { type: String, default: '' },
  // where the new messages begin: `{ since, unread, receipts }`, from the
  // conversations screen, or nothing where there is no such line to draw
  newMessages: { type: Object, default: null },
})

const whatsappMessages = defineModel('whatsappMessages', {
  type: Object,
  default: () => ({}),
})
const reply = defineModel('reply', { type: Object, default: () => ({}) })

const emit = defineEmits(['reload'])

const router = useRouter()

// An appointment or an event in the chat opens on the calendar, on its day:
// that is where it can be moved, changed or cancelled. The cards used to be
// something to look at and nothing to click.
function openOnCalendar(kind, item) {
  const date = item?.data?.starts_on
    ? dayjs(item.data.starts_on).format('YYYY-MM-DD')
    : undefined
  router.push({
    name: 'Calendar',
    query:
      kind === 'appointment'
        ? { appointment: item.name, date }
        : { eventId: item.name, date },
  })
}

const { isNewestFirst } = useTimelinePreferences()
const { getUser, puo } = usersStore()
// an invoice opens here, as it does from the invoices page
const { apriFattura } = useFattura()

// a file received goes among the person's documents
const canArchive = computed(() => puo('documenti.aggiungi'))
const archiving = ref(null)
const archivingOpen = computed({
  get: () => Boolean(archiving.value),
  set: (open) => {
    if (!open) archiving.value = null
  },
})

function fileNameOf(message) {
  return decodeURIComponent((message?.attach || '').split('/').pop() || '')
}
const { retrying, retry, react, answer } = useWhatsAppActions({
  list: whatsappMessages,
  reply,
})

// Dates and clocks in the language the rest of the screen is written in — the
// user's, not the browser's — the way the dashboard writes its dates.
const LOCALE = appLocale()

// The server writes its own clock; the reader lives on theirs. Everything is
// moved onto the reader's before it is filed under a day or given a time, so a
// message written at 23:30 in Rome is tomorrow's for somebody reading in London.
function localOf(at) {
  return at ? dayjsLocal(at).format('YYYY-MM-DD HH:mm:ss') : ''
}

// Each day labelled as it is cut: «today» is read once for the whole list, when
// the list is built, rather than once per marker.
const days = computed(() => {
  const now = dayjsLocal().format('YYYY-MM-DD HH:mm:ss')
  return groupByDay(
    buildStream(props.items, {
      channel: props.channel,
      newestFirst: isNewestFirst.value,
      localize: localOf,
    }),
  ).map((group) => ({
    ...group,
    label: group.day ? dayLabel(group.day, now, LOCALE) : '',
  }))
})

function labelOf(day) {
  return days.value.find((group) => group.day === day)?.label || ''
}

// Where the line goes, measured over what is on screen: a channel picked in
// the selector shows its own new messages and no line for the others'.
const newLine = computed(() => {
  const about = props.newMessages
  if (!about) return null
  return newSince(
    days.value.flatMap((group) => group.rows),
    about.since ? localOf(about.since) : null,
    { newestFirst: isNewestFirst.value },
  )
})

function lineAt(row, above) {
  return newLine.value?.key === row.key && newLine.value.above === above
}

const lineProps = computed(() => ({
  count: newLine.value?.count || 0,
  unread: Boolean(props.newMessages?.unread),
  whatsapp: Boolean(newLine.value?.channels.includes('whatsapp')),
  receipts: Boolean(props.newMessages?.receipts),
}))

function timeOf(row) {
  return row.at ? clockOf(row.at, LOCALE) : ''
}

// the whole moment, for the tooltip on a clock
function momentOf(row) {
  const day = labelOf(String(row.at || '').slice(0, 10))
  return day ? `${day}, ${timeOf(row)}` : timeOf(row)
}

function momentLabel(at) {
  return moment(at, LOCALE)
}

// A run is one voice: its messages sit close, and the gap opens where the
// speaker, the channel or the kind of thing changes.
function spacingOf(row) {
  if (row.bubble && !row.startsRun) return 'mt-0.5'
  return row.bubble ? 'mt-3' : 'mt-3.5'
}

const CHIP =
  'rounded-lg bg-surface-elevation-2 px-2.5 py-1 text-p-xs font-medium text-ink-gray-6 shadow-sm dark:bg-surface-gray-2'

const LABELS = { whatsapp: 'WhatsApp', email: 'Email', sms: 'SMS' }

// The reader, for telling their own messages from a colleague's.
const me = computed(() => getUser()?.name || '')

/**
 * A name above a bubble only where the side does not already say it.
 *
 * Theirs: this is a conversation with one person, and their name is in the
 * header — except for an email, which somebody else at their end can write.
 * Ours: a colleague who answered, never the reader, never the machine.
 */
function speakerFor(row) {
  if (!row.startsRun) return ''
  if (row.direction === 'out') {
    const colleague = colleagueOf(row.item, me.value)
    return colleague ? getUser(colleague)?.full_name || colleague : ''
  }
  if (row.channel !== 'email') return ''
  const name = speakerOf(row.item, '', props.them)
  return name && name !== props.them ? name : ''
}

const APPOINTMENT_THEMES = {
  Scheduled: 'blue',
  Confirmed: 'green',
  Completed: 'gray',
  Cancelled: 'red',
  'No Show': 'orange',
}

function appointmentTheme(status) {
  return APPOINTMENT_THEMES[status] || 'gray'
}

// «Fattura n. 12» rather than «CRM Invoice / INV-2026-00012»: the number is what
// somebody quotes on the phone, and a credit note has to say it is one, because
// the amount alone reads as money coming in either way.
function invoiceTitle(invoice) {
  const kind = isCreditNote(invoice?.document_type)
    ? __('Credit note')
    : __('Invoice')
  const number = invoiceLabel(invoice)
  return number ? `${kind} ${number}` : kind
}

function amountOf(invoice) {
  const total = invoice?.grand_total ?? invoice?.net_payable
  const signed = isCreditNote(invoice?.document_type) ? -Math.abs(total) : total
  return formatEuro(signed)
}

function statusOf(invoice) {
  return worstStatus(invoice || {})
}

const EMPTY = {
  whatsapp: 'No WhatsApp messages with this person yet',
  email: 'No emails with this person yet',
  sms: 'No text messages with this person yet',
  call: 'No calls with this person yet',
  comment: 'No notes about this person yet',
}

const emptyText = computed(() => __(EMPTY[props.channel] || 'Nothing here yet'))

// The WhatsApp view, and only that one, gets WhatsApp's own backdrop: it is what
// makes the difference between a list of messages and a conversation.
const wallpaper = computed(() => props.channel === 'whatsapp')

const ICONS = {
  whatsapp: WhatsAppIcon,
  sms: SMSIcon,
  email: Email2Icon,
  comment: CommentIcon,
  call: PhoneIcon,
}

function iconFor(channel) {
  return ICONS[channel] || DotIcon
}

// the mark of the one field change that is worth a line of its own; the size
// comes from where it is used, as with every other icon here
const StageIcon = () => h('span', { class: 'lucide-milestone' })
const LockIcon = () => h('span', { class: 'lucide-lock' })

function isMissed(item) {
  return item?.status === 'No Answer' && item?.type === 'Incoming'
}

// On the register the icon carries the outcome, not merely «a call»: missed and
// answered are the two things somebody scanning a register is looking for, and
// one phone glyph for both makes them look through every row to find out.
function callIconFor(item) {
  if (item?.status === 'No Answer') return MissedCallIcon
  if (item?.status === 'Busy') return DeclinedCallIcon
  return item?.type === 'Incoming' ? InboundCallIcon : OutboundCallIcon
}

// -- the floating day ---------------------------------------------------------

const root = ref(null)
const floating = ref('')
let scroller = null
let settle = null
let frame = 0

function scrollParentOf(element) {
  let node = element?.parentElement
  while (node) {
    if (/(auto|scroll)/.test(getComputedStyle(node).overflowY)) return node
    node = node.parentElement
  }
  return null
}

// Which day is at the top of the pane, and whether its own marker is still in
// sight — if it is, a second copy floating above it would be the same words
// twice.
function dayAtTheTop() {
  const top = scroller.getBoundingClientRect().top
  let current = null
  for (const section of root.value?.querySelectorAll('section[data-day]') ||
    []) {
    if (section.getBoundingClientRect().top - top > 8) break
    current = section
  }
  if (!current?.dataset.day) return ''
  const markerGone = current.getBoundingClientRect().top - top < -28
  return markerGone ? labelOf(current.dataset.day) : ''
}

// Only while somebody is scrolling: the conversation placing itself when it
// opens is a scroll too, and it flashed the date over the first messages.
let lastTouched = 0
function touched() {
  lastTouched = Date.now()
}

function onScroll() {
  if (Date.now() - lastTouched > 1000) return
  if (frame) return
  frame = requestAnimationFrame(() => {
    frame = 0
    if (!scroller || !root.value) return
    floating.value = dayAtTheTop()
    clearTimeout(settle)
    settle = setTimeout(() => (floating.value = ''), 1200)
  })
}

const TOUCHES = ['wheel', 'touchmove', 'keydown', 'mousedown']

onMounted(() => {
  scroller = scrollParentOf(root.value)
  scroller?.addEventListener('scroll', onScroll, { passive: true })
  for (const type of TOUCHES)
    scroller?.addEventListener(type, touched, { passive: true })
})

onBeforeUnmount(() => {
  scroller?.removeEventListener('scroll', onScroll)
  for (const type of TOUCHES) scroller?.removeEventListener(type, touched)
  clearTimeout(settle)
  if (frame) cancelAnimationFrame(frame)
})
</script>

<style scoped>
/*
  WhatsApp's paper: the shade, and a doodle over it.

  Drawn here rather than shipped as an asset — the real one is somebody else's
  artwork, and a tiled PNG is weight on every page load. Two colours and eighteen
  little line drawings, faint enough that the bubbles stay the thing you read:
  what the paper does is tell the eye it is looking at a chat rather than a list,
  and a plain beige rectangle does not do that.

  It fills the pane, not the messages: `min-h-full` on the root takes the box to
  the bottom of the scroller even when there are three messages in it.

  Dark by the app's theme. It followed `prefers-color-scheme`, so a CRM set to
  dark on a laptop left in light mode showed a cream wallpaper in a black app.
  Written without `:global()`: Vue compiled `:global([data-theme='dark'])
  .wa-wallpaper` to `[data-theme=dark]` alone, and the dark paper went on the
  page's <html> instead.
*/
.wa-wallpaper {
  background-color: #efeae2;
  background-image: url("data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' width='300' height='300' viewBox='0 0 300 300'><g fill='none' stroke='%23000000' stroke-opacity='0.06' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'><g transform='translate(12 18) rotate(-4) scale(0.8)'><path d='M0 4a4 4 0 0 1 4-4h26a4 4 0 0 1 4 4v14a4 4 0 0 1-4 4H12l-7 7v-7H4a4 4 0 0 1-4-4z'/></g><g transform='translate(118 44) rotate(-14) scale(0.75)'><path d='M11 0l3.4 7.2 7.6 1-5.5 5.6L18 21l-7-3.9L4 21l1.5-7.2L0 8.2l7.6-1z'/></g><g transform='translate(214 10) rotate(9) scale(0.8)'><path d='M0 9L22 0l-8 21-3.5-8z'/><path d='M10.5 13L22 0'/></g><g transform='translate(62 92) rotate(0) scale(0.8)'><circle cx='11' cy='11' r='11'/><path d='M7 7.5v1.5M15 7.5v1.5'/><path d='M5.5 13.5a6.5 6.5 0 0 0 11 0'/></g><g transform='translate(166 116) rotate(11) scale(0.8)'><path d='M12 20S0 13 0 6.5A6.5 6.5 0 0 1 12 3a6.5 6.5 0 0 1 12 3.5C24 13 12 20 12 20z'/></g><g transform='translate(252 78) rotate(-7) scale(0.75)'><rect x='0' y='4' width='26' height='18' rx='3'/><path d='M8 4l2-3h6l2 3'/><circle cx='13' cy='13' r='5'/></g><g transform='translate(8 150) rotate(5) scale(0.8)'><path d='M0 2h18v10a7 7 0 0 1-7 7H7a7 7 0 0 1-7-7z'/><path d='M18 5h3a3.5 3.5 0 0 1 0 7h-3'/></g><g transform='translate(108 168) rotate(-9) scale(0.8)'><path d='M14 1v14'/><path d='M14 1c0 4 3 3.5 5 5'/><circle cx='10' cy='15.5' r='4'/></g><g transform='translate(206 196) rotate(3) scale(0.75)'><circle cx='11' cy='11' r='11'/><path d='M11 5v6l4 3'/></g><g transform='translate(268 152) rotate(7) scale(0.7)'><path d='M0 4a4 4 0 0 1 4-4h26a4 4 0 0 1 4 4v14a4 4 0 0 1-4 4H12l-7 7v-7H4a4 4 0 0 1-4-4z'/></g><g transform='translate(40 236) rotate(13) scale(0.8)'><path d='M11 0l3.4 7.2 7.6 1-5.5 5.6L18 21l-7-3.9L4 21l1.5-7.2L0 8.2l7.6-1z'/></g><g transform='translate(140 262) rotate(-11) scale(0.75)'><path d='M0 9L22 0l-8 21-3.5-8z'/><path d='M10.5 13L22 0'/></g><g transform='translate(232 268) rotate(4) scale(0.75)'><circle cx='11' cy='11' r='11'/><path d='M7 7.5v1.5M15 7.5v1.5'/><path d='M5.5 13.5a6.5 6.5 0 0 0 11 0'/></g><g transform='translate(70 62) rotate(-8) scale(0.6)'><path d='M12 20S0 13 0 6.5A6.5 6.5 0 0 1 12 3a6.5 6.5 0 0 1 12 3.5C24 13 12 20 12 20z'/></g><g transform='translate(152 20) rotate(6) scale(0.6)'><circle cx='11' cy='11' r='11'/><path d='M11 5v6l4 3'/></g><g transform='translate(176 224) rotate(-5) scale(0.62)'><path d='M0 2h18v10a7 7 0 0 1-7 7H7a7 7 0 0 1-7-7z'/><path d='M18 5h3a3.5 3.5 0 0 1 0 7h-3'/></g><g transform='translate(274 232) rotate(8) scale(0.62)'><path d='M14 1v14'/><path d='M14 1c0 4 3 3.5 5 5'/><circle cx='10' cy='15.5' r='4'/></g><g transform='translate(96 126) rotate(5) scale(0.6)'><rect x='0' y='4' width='26' height='18' rx='3'/><path d='M8 4l2-3h6l2 3'/><circle cx='13' cy='13' r='5'/></g></g></svg>");
  background-size: 300px 300px;
  background-repeat: repeat;
}

[data-theme='dark'] .wa-wallpaper {
  /* WhatsApp's own dark paper, which is not grey but very nearly black */
  background-color: #0b141a;
  background-image: url("data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' width='300' height='300' viewBox='0 0 300 300'><g fill='none' stroke='%23ffffff' stroke-opacity='0.05' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'><g transform='translate(12 18) rotate(-4) scale(0.8)'><path d='M0 4a4 4 0 0 1 4-4h26a4 4 0 0 1 4 4v14a4 4 0 0 1-4 4H12l-7 7v-7H4a4 4 0 0 1-4-4z'/></g><g transform='translate(118 44) rotate(-14) scale(0.75)'><path d='M11 0l3.4 7.2 7.6 1-5.5 5.6L18 21l-7-3.9L4 21l1.5-7.2L0 8.2l7.6-1z'/></g><g transform='translate(214 10) rotate(9) scale(0.8)'><path d='M0 9L22 0l-8 21-3.5-8z'/><path d='M10.5 13L22 0'/></g><g transform='translate(62 92) rotate(0) scale(0.8)'><circle cx='11' cy='11' r='11'/><path d='M7 7.5v1.5M15 7.5v1.5'/><path d='M5.5 13.5a6.5 6.5 0 0 0 11 0'/></g><g transform='translate(166 116) rotate(11) scale(0.8)'><path d='M12 20S0 13 0 6.5A6.5 6.5 0 0 1 12 3a6.5 6.5 0 0 1 12 3.5C24 13 12 20 12 20z'/></g><g transform='translate(252 78) rotate(-7) scale(0.75)'><rect x='0' y='4' width='26' height='18' rx='3'/><path d='M8 4l2-3h6l2 3'/><circle cx='13' cy='13' r='5'/></g><g transform='translate(8 150) rotate(5) scale(0.8)'><path d='M0 2h18v10a7 7 0 0 1-7 7H7a7 7 0 0 1-7-7z'/><path d='M18 5h3a3.5 3.5 0 0 1 0 7h-3'/></g><g transform='translate(108 168) rotate(-9) scale(0.8)'><path d='M14 1v14'/><path d='M14 1c0 4 3 3.5 5 5'/><circle cx='10' cy='15.5' r='4'/></g><g transform='translate(206 196) rotate(3) scale(0.75)'><circle cx='11' cy='11' r='11'/><path d='M11 5v6l4 3'/></g><g transform='translate(268 152) rotate(7) scale(0.7)'><path d='M0 4a4 4 0 0 1 4-4h26a4 4 0 0 1 4 4v14a4 4 0 0 1-4 4H12l-7 7v-7H4a4 4 0 0 1-4-4z'/></g><g transform='translate(40 236) rotate(13) scale(0.8)'><path d='M11 0l3.4 7.2 7.6 1-5.5 5.6L18 21l-7-3.9L4 21l1.5-7.2L0 8.2l7.6-1z'/></g><g transform='translate(140 262) rotate(-11) scale(0.75)'><path d='M0 9L22 0l-8 21-3.5-8z'/><path d='M10.5 13L22 0'/></g><g transform='translate(232 268) rotate(4) scale(0.75)'><circle cx='11' cy='11' r='11'/><path d='M7 7.5v1.5M15 7.5v1.5'/><path d='M5.5 13.5a6.5 6.5 0 0 0 11 0'/></g><g transform='translate(70 62) rotate(-8) scale(0.6)'><path d='M12 20S0 13 0 6.5A6.5 6.5 0 0 1 12 3a6.5 6.5 0 0 1 12 3.5C24 13 12 20 12 20z'/></g><g transform='translate(152 20) rotate(6) scale(0.6)'><circle cx='11' cy='11' r='11'/><path d='M11 5v6l4 3'/></g><g transform='translate(176 224) rotate(-5) scale(0.62)'><path d='M0 2h18v10a7 7 0 0 1-7 7H7a7 7 0 0 1-7-7z'/><path d='M18 5h3a3.5 3.5 0 0 1 0 7h-3'/></g><g transform='translate(274 232) rotate(8) scale(0.62)'><path d='M14 1v14'/><path d='M14 1c0 4 3 3.5 5 5'/><circle cx='10' cy='15.5' r='4'/></g><g transform='translate(96 126) rotate(5) scale(0.6)'><rect x='0' y='4' width='26' height='18' rx='3'/><path d='M8 4l2-3h6l2 3'/><circle cx='13' cy='13' r='5'/></g></g></svg>");
}
</style>
