import { getSettings } from '@/stores/settings'
import { laterLabel, momentLabel } from '@/utils/conversation'
import { appLocale } from '@/utils/locale'
import { call, createResource, dayjs, toast } from 'frappe-ui'
import { computed, ref } from 'vue'

// The records a conversation can be kept on.
const RECORDS = ['CRM Lead', 'CRM Deal']

// What an «Undo» puts back: the decision and whether it was read, as they were
// a moment before — and when anything was last said, which is how the server
// knows not to bury a message that arrived in between.
const UNDOABLE = [
  'conversation_status',
  'conversation_snoozed_until',
  'conversation_unread',
  'conversation_seen_until',
  'conversation_seen_by',
  'last_conversation_on',
]

/** Whether this site sends WhatsApp read receipts — the blue ticks. */
export function readReceipts() {
  const { _settings } = getSettings()
  return computed(() => Boolean(_settings.doc?.whatsapp_read_receipts))
}

/**
 * A reply went from here: whoever wrote it had read what they were answering.
 *
 * Called by every composer — WhatsApp, a template, a reaction, SMS, email — and
 * by nothing that sends on its own: a message an automation sends says nothing
 * about anybody having read anything. Quiet, because it is bookkeeping about a
 * message that has already gone; the conversation screen hears about it and
 * redraws the row.
 */
export function markAnswered(doctype, name) {
  if (!RECORDS.includes(doctype) || !name) return
  call('crm.api.conversations.mark_read', {
    reference_doctype: doctype,
    reference_name: name,
  })
    .then((answer) =>
      window.dispatchEvent(
        new CustomEvent('crm:conversation-read', {
          detail: { doctype, name, ...answer },
        }),
      ),
    )
    .catch(() => {})
}

/**
 * What we decide about a conversation: read, handled, put off, whose it is.
 *
 * One place for the four, because the header and the panel both ask them and
 * two copies of «what does snoozing mean» drift. They also have to agree with
 * each other in a way that was easy to miss: assigning somebody went through
 * the same endpoint as «open» and «handled», saying «open» — which unparked a
 * conversation somebody had put off until Monday, the moment it was given to a
 * colleague.
 *
 * The two decisions that take a conversation out of the list say where it
 * went, and offer the way back: a row that leaves with no word is a person the
 * list has lost.
 *
 * @param {import('vue').Ref<object>} person  the row: name and conversation_*
 * @param {() => void} changed                 called after any change lands
 */
export function useConversationState(person, changed) {
  // which of the buttons is waiting for the server
  const busy = ref('')
  const receipts = readReceipts()

  const markRead = createResource({ url: 'crm.api.conversations.mark_read' })
  const markUnread = createResource({
    url: 'crm.api.conversations.mark_unread',
  })
  const setState = createResource({ url: 'crm.api.conversations.set_state' })
  const restore = createResource({ url: 'crm.api.conversations.restore' })

  function run(key, resource, params = {}) {
    busy.value = key
    return resource
      .submit({
        reference_doctype: 'CRM Lead',
        reference_name: person.value.name,
        ...params,
      })
      .then((answer) => {
        changed?.()
        return answer
      })
      .catch((error) => {
        toast.error(error.messages?.[0] || __('Could not save that'))
        return null
      })
      .finally(() => (busy.value = ''))
  }

  const unread = computed(() => Boolean(person.value?.conversation_unread))
  const handled = computed(
    () => person.value?.conversation_status === 'Handled',
  )
  const snoozedUntil = computed(
    () => person.value?.conversation_snoozed_until || '',
  )

  // Read, and off the pile. It only ever happens because somebody says so —
  // or answers: looking at a chat is not dealing with it.
  async function setRead(yes) {
    const answer = await run('read', yes ? markRead : markUnread)
    if (yes && answer?.receipts) {
      toast.success(__('Marked as read'), {
        description: __('Blue ticks sent on WhatsApp.'),
      })
    }
  }

  // The row as it is now, for the way back. Nothing to go back to before the
  // conversation has been read from the server at least once.
  function snapshot() {
    if (!person.value || !('conversation_status' in person.value)) return null
    return Object.fromEntries(
      UNDOABLE.map((key) => [key, person.value[key] ?? null]),
    )
  }

  function undo(name, was) {
    busy.value = 'state'
    restore
      .submit({
        reference_doctype: 'CRM Lead',
        reference_name: name,
        was,
      })
      .then(() => changed?.())
      .catch((error) =>
        toast.error(error.messages?.[0] || __('Could not undo that')),
      )
      .finally(() => (busy.value = ''))
  }

  async function decide(state, until = null) {
    const name = person.value.name
    const was = snapshot()
    const answer = await run(
      state === 'Snoozed' ? 'snooze' : 'state',
      setState,
      { state, until, assign_to: null },
    )
    if (!answer) return

    const back = was
      ? { action: { label: __('Undo'), onClick: () => undo(name, was) } }
      : {}
    const ticks = answer.receipts ? ' ' + __('Blue ticks sent.') : ''
    if (state === 'Handled') {
      toast.success(__('Marked as handled'), {
        description: __('Back in Open when they write.') + ticks,
        ...back,
      })
    } else if (state === 'Snoozed') {
      toast.success(__('Put off until {0}', [whenBack(until)]), {
        description: __('Back in Open then, or sooner if they write.'),
        ...back,
      })
    }
  }

  // Whose it is, without touching what was decided about it: a parked
  // conversation stays parked, a handled one stays handled.
  function assign(user) {
    const state = snoozedUntil.value
      ? 'Snoozed'
      : person.value?.conversation_status || 'Open'
    return run('assign', setState, {
      state,
      until: snoozedUntil.value || null,
      assign_to: user || '',
    })
  }

  function at(days, hour) {
    return dayjs()
      .add(days, 'day')
      .hour(hour)
      .minute(0)
      .second(0)
      .format('YYYY-MM-DD HH:mm:ss')
  }

  function whenBack(until) {
    return laterLabel(until, dayjs().format('YYYY-MM-DD HH:mm:ss'), appLocale())
  }

  // Tomorrow morning, in three days, next week: the moments somebody actually
  // means by «later», rather than a date picker for a decision that takes a
  // second. Each says the moment it means, and the heading says what «later»
  // does to the conversation meanwhile.
  const snoozeOptions = computed(() => {
    const choices = [
      [__('Tomorrow morning'), 'lucide-sunrise', at(1, 9)],
      [__('In three days'), 'lucide-calendar-days', at(3, 9)],
      [__('Next week'), 'lucide-calendar-range', at(7, 9)],
    ]
    return [
      {
        group: __('Back in Open then, or when they write'),
        options: [
          ...choices.map(([label, icon, moment]) => ({
            label,
            icon,
            description: momentLabel(moment, appLocale()),
            onClick: () => decide('Snoozed', moment),
          })),
          ...(snoozedUntil.value
            ? [
                {
                  label: __('Bring it back now'),
                  icon: 'lucide-rotate-ccw',
                  onClick: () => decide('Open'),
                },
              ]
            : []),
        ],
      },
    ]
  })

  return {
    busy,
    receipts,
    unread,
    handled,
    snoozedUntil,
    setRead,
    decide,
    assign,
    snoozeOptions,
  }
}
