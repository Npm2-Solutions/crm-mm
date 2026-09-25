<!--
  The right column: who you are talking to, and what you decide about it.

  Deliberately short. The record page is one click away and holds everything;
  what belongs here is only what you need *while replying* — who this is, how to
  reach them, and the three decisions that take a conversation off the pile.
-->
<template>
  <div
    class="flex w-72 shrink-0 flex-col gap-4 overflow-y-auto border-l bg-surface-white p-4"
  >
    <div class="flex flex-col items-center gap-2 text-center">
      <Avatar size="2xl" :label="title" :image="person.image" />
      <div class="min-w-0">
        <div class="truncate text-lg font-medium text-ink-gray-9">
          {{ title }}
        </div>
        <div
          v-if="person.organization"
          class="truncate text-p-sm text-ink-gray-5"
        >
          {{ person.organization }}
        </div>
      </div>
      <Button
        :label="__('Open the record')"
        size="sm"
        @click="router.push({ name: 'Lead', params: { leadId: person.name } })"
      />
    </div>

    <div v-if="person.mobile_no" class="flex flex-col gap-1">
      <span class="text-p-xs uppercase text-ink-gray-5">{{ __('Phone') }}</span>
      <a
        class="truncate text-p-sm text-ink-blue-link"
        :href="`tel:${person.mobile_no}`"
      >
        {{ person.mobile_no }}
      </a>
    </div>

    <div class="flex flex-col gap-2">
      <span class="text-p-xs uppercase text-ink-gray-5">
        {{ __('This conversation') }}
      </span>

      <!--
        Handled is the one that was missing. Until now the only way to take a
        row off the list was to reply — and a conversation that ends with their
        «grazie» needs no reply, so it stayed there for good.
      -->
      <!--
        Read, and off the pile. It only ever happens because somebody says so:
        it used to happen by itself the moment a chat was opened, which is how a
        count becomes noise — you glance to see who it was, the number goes, and
        what you had not dealt with looks like what you had.
      -->
      <Button
        v-if="person.conversation_unread"
        :label="__('Mark as read')"
        iconLeft="eye"
        :loading="reading"
        @click="setRead(true)"
      />
      <Button
        v-else
        :label="__('Mark as unread')"
        iconLeft="eye-off"
        :loading="reading"
        @click="setRead(false)"
      />
      <Button
        v-if="person.conversation_status !== 'Handled'"
        :label="__('Mark as handled')"
        iconLeft="check"
        :loading="saving"
        @click="decide('Handled')"
      />
      <Button
        v-else
        :label="__('Put it back')"
        iconLeft="rotate-ccw"
        :loading="saving"
        @click="decide('Open')"
      />

      <Dropdown :options="snoozeOptions" placement="left">
        <template #default>
          <Button class="w-full" :label="snoozeLabel" iconLeft="clock" />
        </template>
      </Dropdown>

      <div class="flex flex-col gap-1">
        <span class="text-p-xs text-ink-gray-5">{{ __('Assigned to') }}</span>
        <Link
          class="w-full"
          doctype="User"
          :value="person.conversation_assigned_to"
          :placeholder="__('Nobody')"
          @change="
            (user) => decide(person.conversation_status, null, user || '')
          "
        />
      </div>
    </div>
  </div>
</template>

<script setup>
import Link from '@/components/Controls/Link.vue'
import { Avatar, Dropdown, createResource, dayjs, toast } from 'frappe-ui'
import { computed, ref } from 'vue'
import { useRouter } from 'vue-router'

const props = defineProps({
  person: { type: Object, default: () => ({}) },
})

const emit = defineEmits(['changed'])

const router = useRouter()
const saving = ref(false)

const title = computed(
  () =>
    props.person.lead_name ||
    props.person.organization ||
    props.person.name ||
    '',
)

// Tomorrow morning, Monday morning, next week: the three moments somebody
// actually means by «later», rather than a date picker for a decision that
// takes a second.
const snoozeOptions = computed(() => [
  {
    label: __('Tomorrow morning'),
    onClick: () => decide('Snoozed', at(1, 9)),
  },
  {
    label: __('In three days'),
    onClick: () => decide('Snoozed', at(3, 9)),
  },
  {
    label: __('Next week'),
    onClick: () => decide('Snoozed', at(7, 9)),
  },
  ...(props.person.conversation_snoozed_until
    ? [{ label: __('Bring it back now'), onClick: () => decide('Open') }]
    : []),
])

const snoozeLabel = computed(() =>
  props.person.conversation_snoozed_until
    ? __('Back {0}', [
        dayjs(props.person.conversation_snoozed_until).format('D MMM, HH:mm'),
      ])
    : __('Put off until later'),
)

function at(days, hour) {
  return dayjs()
    .add(days, 'day')
    .hour(hour)
    .minute(0)
    .second(0)
    .format('YYYY-MM-DD HH:mm:ss')
}

const reading = ref(false)
const read = createResource({ url: 'crm.api.conversations.mark_read' })
const unread = createResource({ url: 'crm.api.conversations.mark_unread' })

function setRead(yes) {
  reading.value = true
  const what = yes ? read : unread
  what
    .submit({
      reference_doctype: 'CRM Lead',
      reference_name: props.person.name,
    })
    .then(() => emit('changed'))
    .catch((error) =>
      toast.error(error.messages?.[0] || __('Could not save that')),
    )
    .finally(() => (reading.value = false))
}

const state = createResource({ url: 'crm.api.conversations.set_state' })

function decide(which, until = null, assignTo = null) {
  saving.value = true
  state
    .submit({
      reference_doctype: 'CRM Lead',
      reference_name: props.person.name,
      state: which || 'Open',
      until,
      assign_to: assignTo,
    })
    .then(() => emit('changed'))
    .catch((error) =>
      toast.error(error.messages?.[0] || __('Could not save that')),
    )
    .finally(() => (saving.value = false))
}
</script>
