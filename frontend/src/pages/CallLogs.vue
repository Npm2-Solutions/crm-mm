<!--
  Modifications copyright (c) 2026, NPM2 Solutions Srl

  On a phone the register is a list of its own, found by a name or a number
  (components/Mobile/ElencoChiamate.vue).
-->
<template>
  <LayoutHeader>
    <template #left-header>
      <ViewBreadcrumbs v-model="viewControls" routeName="Call Logs" />
    </template>
    <template #right-header>
      <CustomActions
        v-if="callLogsListView?.customListActions"
        :actions="callLogsListView.customListActions"
      />
      <!-- the round of calls starts from the register too, not only from
           the phone at the top -->
      <Button
        v-if="callEnabled && puo('telefono.chiama') && isMobileView"
        icon="lucide-list-ordered"
        :tooltip="__('Call round')"
        :aria-label="__('Call round')"
        :route="{ name: 'Dialer' }"
      />
      <Button
        v-else-if="callEnabled && puo('telefono.chiama')"
        :label="__('Call round')"
        iconLeft="lucide-list-ordered"
        :route="{ name: 'Dialer' }"
      />
      <!-- logging a call is for who calls, as on the person's page -->
      <Button
        v-if="!isMobileView && puo('telefono.chiama')"
        variant="solid"
        :label="__('Create')"
        iconLeft="plus"
        @click="createCallLog"
      />
    </template>
  </LayoutHeader>
  <!-- on a phone: typed to find, one line each, the + where the thumb is -->
  <template v-if="isMobileView">
    <ElencoChiamate ref="elencoChiamate" @apri="showCallLog" />
    <PulsanteAggiungi
      v-if="puo('telefono.chiama')"
      :label="__('Log a call')"
      @click="createCallLog"
    />
  </template>
  <ViewControls
    v-if="!isMobileView"
    ref="viewControls"
    v-model="callLogs"
    v-model:loadMore="loadMore"
    v-model:resizeColumn="triggerResize"
    v-model:updatedPageCount="updatedPageCount"
    doctype="CRM Call Log"
  />
  <CallLogsListView
    v-if="!isMobileView && callLogs.data && rows.length"
    ref="callLogsListView"
    v-model="callLogs.data.page_length_count"
    v-model:list="callLogs"
    :rows="rows"
    :columns="columns"
    :options="{
      showTooltip: false,
      resizeColumn: true,
      rowCount: callLogs.data.row_count,
      totalCount: callLogs.data.total_count,
    }"
    @showCallLog="showCallLog"
    @loadMore="() => loadMore++"
    @columnWidthUpdated="() => triggerResize++"
    @updatePageCount="(count) => (updatedPageCount = count)"
    @applyFilter="(data) => viewControls.applyFilter(data)"
    @applyLikeFilter="(data) => viewControls.applyLikeFilter(data)"
    @likeDoc="(data) => viewControls.likeDoc(data)"
    @selectionsChanged="
      (selections) => viewControls.updateSelections(selections)
    "
  />
  <EmptyState
    v-else-if="!isMobileView && callLogs.data && !rows.length"
    name="Call Logs"
    :icon="PhoneIcon"
  />
  <CallLogDetailModal
    v-model="showCallLogDetailModal"
    v-model:callLog="callLog"
  />
</template>

<script setup>
import ViewBreadcrumbs from '@/components/ViewBreadcrumbs.vue'
import CustomActions from '@/components/CustomActions.vue'
import PhoneIcon from '@/components/Icons/PhoneIcon.vue'
import LayoutHeader from '@/components/LayoutHeader.vue'
import ViewControls from '@/components/ViewControls.vue'
import CallLogsListView from '@/components/ListViews/CallLogsListView.vue'
import EmptyState from '@/components/ListViews/EmptyState.vue'
import CallLogDetailModal from '@/components/Modals/CallLogDetailModal.vue'
import ElencoChiamate from '@/components/Mobile/ElencoChiamate.vue'
import PulsanteAggiungi from '@/components/Mobile/PulsanteAggiungi.vue'
import { isMobileView } from '@/composables/breakpoints'
import { useDoctypeModal } from '@/composables/doctypeModal'
import { callEnabled } from '@/composables/telephony'
import { usersStore } from '@/stores/users'
import { getCallLogDetail } from '@/utils/callLog'
import { useTelemetry } from 'frappe-ui/frappe'
import { createResource } from 'frappe-ui'
import { computed, ref, onMounted } from 'vue'
import { useRoute } from 'vue-router'

const callLogsListView = ref(null)
const elencoChiamate = ref(null)
const { puo } = usersStore()

// callLogs data is loaded in the ViewControls component
const callLogs = ref({})
const loadMore = ref(1)
const triggerResize = ref(1)
const updatedPageCount = ref(20)
const viewControls = ref(null)

const rows = computed(() => {
  if (
    !callLogs.value?.data?.data ||
    !['list', 'group_by'].includes(callLogs.value.data.view_type)
  )
    return []
  return callLogs.value?.data.data.map((callLog) => {
    let _rows = {}
    callLogs.value?.data.rows.forEach((row) => {
      _rows[row] = getCallLogDetail(row, callLog, callLogs.value?.data.columns)
    })
    return _rows
  })
})

const columns = computed(() => {
  let _columns = callLogs.value?.data?.columns || []

  // Set align right for last column
  if (_columns.length) {
    _columns = _columns.map((col, index) => {
      if (index === _columns.length - 1) {
        return { ...col, align: 'right' }
      }
      return col
    })
  }

  return _columns
})

const showCallLogDetailModal = ref(false)
const callLog = ref({})

function showCallLog(name) {
  showCallLogDetailModal.value = true
  callLog.value = createResource({
    url: 'crm.fcrm.doctype.crm_call_log.crm_call_log.get_call_log',
    params: { name },
    cache: ['call_log', name],
    auto: true,
  })
}

const { showModal } = useDoctypeModal()
const { capture } = useTelemetry()

function createCallLog() {
  showModal({
    doctype: 'CRM Call Log',
    title: 'Call Log',
    callbacks: {
      afterInsert: () => {
        capture('call_log_created')
        if (isMobileView.value) elencoChiamate.value?.ricarica()
        else callLogs.value.reload()
      },
    },
  })
}

// `?open=<call>`: the call a notification names (a message left by a number
// nobody knows), open over the register. The address goes on without it, past
// the router: App.vue keys this page on its query, and would draw it again
// without the call
const route = useRoute()
const openCallLogFromURL = () => {
  const open = route.query.open
  if (!open) return
  showCallLog(open)
  const indirizzo = new URL(window.location.href)
  indirizzo.searchParams.delete('open')
  window.history.replaceState(
    window.history.state,
    '',
    indirizzo.pathname + indirizzo.search + indirizzo.hash,
  )
}

onMounted(() => {
  openCallLogFromURL()
})
</script>
