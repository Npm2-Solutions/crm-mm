import { createResource, dayjs, toast } from 'frappe-ui'
import { computed, ref } from 'vue'

/**
 * What we decide about a conversation: read, dealt with, put off, whose it is.
 *
 * One place for the four, because the header and the panel both ask them and
 * two copies of «what does snoozing mean» drift. They also have to agree with
 * each other in a way that was easy to miss: assigning somebody went through
 * the same endpoint as «open» and «handled», saying «open» — which unparked a
 * conversation somebody had put off until Monday, the moment it was given to a
 * colleague.
 *
 * @param {import('vue').Ref<object>} person  the row: name and conversation_*
 * @param {() => void} changed                 called after any change lands
 */
export function useConversationState(person, changed) {
  // which of the buttons is waiting for the server
  const busy = ref('')

  const markRead = createResource({ url: 'crm.api.conversations.mark_read' })
  const markUnread = createResource({
    url: 'crm.api.conversations.mark_unread',
  })
  const setState = createResource({ url: 'crm.api.conversations.set_state' })

  function run(key, resource, params = {}) {
    busy.value = key
    return resource
      .submit({
        reference_doctype: 'CRM Lead',
        reference_name: person.value.name,
        ...params,
      })
      .then(() => changed?.())
      .catch((error) =>
        toast.error(error.messages?.[0] || __('Could not save that')),
      )
      .finally(() => (busy.value = ''))
  }

  const unread = computed(() => Boolean(person.value?.conversation_unread))
  const handled = computed(
    () => person.value?.conversation_status === 'Handled',
  )
  const snoozedUntil = computed(
    () => person.value?.conversation_snoozed_until || '',
  )

  // Read, and off the pile. It only ever happens because somebody says so:
  // looking at a chat is not dealing with it.
  function setRead(yes) {
    return run('read', yes ? markRead : markUnread)
  }

  function decide(state, until = null) {
    return run(state === 'Snoozed' ? 'snooze' : 'state', setState, {
      state,
      until,
      assign_to: null,
    })
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

  // Tomorrow morning, in three days, next week: the moments somebody actually
  // means by «later», rather than a date picker for a decision that takes a
  // second.
  const snoozeOptions = computed(() => [
    {
      label: __('Tomorrow morning'),
      icon: 'lucide-sunrise',
      onClick: () => decide('Snoozed', at(1, 9)),
    },
    {
      label: __('In three days'),
      icon: 'lucide-calendar-days',
      onClick: () => decide('Snoozed', at(3, 9)),
    },
    {
      label: __('Next week'),
      icon: 'lucide-calendar-range',
      onClick: () => decide('Snoozed', at(7, 9)),
    },
    ...(snoozedUntil.value
      ? [
          {
            label: __('Bring it back now'),
            icon: 'lucide-rotate-ccw',
            onClick: () => decide('Open'),
          },
        ]
      : []),
  ])

  return {
    busy,
    unread,
    handled,
    snoozedUntil,
    setRead,
    decide,
    assign,
    snoozeOptions,
  }
}
