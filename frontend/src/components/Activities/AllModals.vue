<!--
  Modifications copyright (c) 2026, NPM2 Solutions Srl
-->
<template>
  <EventModal
    v-if="showEventModal"
    v-model="showEventModal"
    :event="activeEvent"
    :doctype="doctype"
    :docname="doc?.name"
  />
</template>
<script setup>
import EventModal from '@/components/Modals/EventModal.vue'
import { showEventModal, activeEvent } from '@/composables/event'
import { useDoctypeModal } from '@/composables/doctypeModal'
import { useTelemetry } from 'frappe-ui/frappe'
import { call, dayjs } from 'frappe-ui'
import { callParties, numberOf } from '@/utils/callLog'
import { usersStore } from '@/stores/users'
import { useRoute, useRouter } from 'vue-router'

const props = defineProps({
  doctype: { type: String, default: '' },
  doc: { type: Object, default: () => ({}) },
})

const activities = defineModel({ type: Object })
// which channel of the history to read after a save (Activities.vue)
const emit = defineEmits(['mostra'])

const { showModal } = useDoctypeModal()
const { getUser } = usersStore()
const { capture } = useTelemetry()

// Event
function showEvent(e) {
  showEventModal.value = true
  activeEvent.value = e
}

// Tasks
function showTask(task) {
  showModal({
    name: task?.name,
    doctype: 'CRM Task',
    title: 'Task',
    defaults: {
      reference_doctype: props.doctype,
      reference_docname: props.doc?.name,
      // what the Tasks page and the call panel start a task with: from here
      // the two selects opened empty
      ...(task?.name ? {} : { status: 'Backlog', priority: 'Low' }),
    },
    callbacks: {
      afterInsert: (d) => afterDoctype(d, true),
      afterUpdate: afterDoctype,
      // the sheet's «Delete», as the list's menu
      afterDelete: () => activities.value.reload(),
    },
  })
}

async function deleteTask(name) {
  await call('frappe.client.delete', {
    doctype: 'CRM Task',
    name,
  })
  activities.value.reload()
}

function updateTaskStatus(status, task) {
  call('frappe.client.set_value', {
    doctype: 'CRM Task',
    name: task.name,
    fieldname: 'status',
    value: status,
  }).then(() => {
    activities.value.reload()
  })
}

// Notes
function showNote(note) {
  showModal({
    name: note?.name,
    doctype: 'FCRM Note',
    title: 'Note',
    defaults: {
      reference_doctype: props.doctype,
      reference_docname: props.doc?.name,
    },
    callbacks: {
      afterInsert: (d) => afterDoctype(d, true),
      afterUpdate: afterDoctype,
      afterDelete: () => activities.value.reload(),
    },
  })
}

function afterDoctype(d, isInsert = false) {
  activities.value.reload()

  let name =
    d.doctype == 'FCRM Note'
      ? 'note'
      : d.doctype == 'CRM Task'
        ? 'task'
        : 'call_log'

  let redirectHash = name + 's'
  if (d.doctype == 'CRM Call Log') {
    // the calls are the history's own view, not a tab of their own: there,
    // with the new one in its place among them
    redirectHash = 'activity'
    emit('mostra', 'call')
  }

  if (isInsert) {
    capture(name + '_created')
  } else {
    capture(name + '_updated')
  }

  redirect(redirectHash)
}

// Call Logs
function createCallLog() {
  // The record already says who the call was with, and the session says who is
  // logging it. Asking for both on every call is asking a question the screen
  // can answer — and getting it wrong often enough, because which end is which
  // depends on the direction and a form is filled the way it is laid out.
  const theirNumber = numberOf(props.doc)
  const me = getUser().name

  showModal({
    doctype: 'CRM Call Log',
    title: 'Call Log',
    defaults: {
      reference_doctype: props.doctype,
      reference_docname: props.doc?.name,
      reference_doc: { ...props.doc },
      type: 'Outgoing',
      telephony_medium: 'Manual',
      status: 'Completed',
      start_time: dayjs().format('YYYY-MM-DD HH:mm:ss'),
      ...callParties({ direction: 'Outgoing', theirNumber, myNumber: '', me }),
    },
    callbacks: {
      afterInsert: (d) => afterDoctype(d, true),
      afterUpdate: afterDoctype,
    },
  })
}

// common
const route = useRoute()
const router = useRouter()

function redirect(tabName) {
  if (route.name == 'Lead' || route.name == 'Deal') {
    let hash = '#' + tabName
    if (route.hash != hash) {
      router.push({ ...route, hash })
    }
  }
}

defineExpose({
  showEvent,
  showTask,
  deleteTask,
  updateTaskStatus,
  showNote,
  createCallLog,
})
</script>
