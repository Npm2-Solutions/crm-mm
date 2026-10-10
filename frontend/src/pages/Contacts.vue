<!--
  Modifications copyright (c) 2026, NPM2 Solutions Srl

  On a phone the contacts are a list of their own, found by typing
  (components/Mobile/ElencoContatti.vue).
-->
<template>
  <LayoutHeader>
    <template #left-header>
      <ViewBreadcrumbs v-model="viewControls" routeName="Contacts" />
    </template>
    <template #right-header>
      <CustomActions
        v-if="contactsListView?.customListActions"
        :actions="contactsListView.customListActions"
      />
      <Button
        v-if="!isMobileView"
        variant="solid"
        :label="__('New contact')"
        iconLeft="plus"
        @click="showContactModal = true"
      />
    </template>
  </LayoutHeader>
  <!-- on a phone: typed to find, one line each, the + where the thumb is -->
  <template v-if="isMobileView">
    <ElencoContatti />
    <PulsanteAggiungi
      v-if="puo('persone.scrivi')"
      :label="__('New contact')"
      @click="showContactModal = true"
    />
  </template>
  <ViewControls
    v-if="!isMobileView"
    ref="viewControls"
    v-model="contacts"
    v-model:loadMore="loadMore"
    v-model:resizeColumn="triggerResize"
    v-model:updatedPageCount="updatedPageCount"
    doctype="Contact"
  />
  <ContactsListView
    v-if="!isMobileView && contacts.data && rows.length"
    ref="contactsListView"
    v-model="contacts.data.page_length_count"
    v-model:list="contacts"
    :rows="rows"
    :columns="columns"
    :options="{
      showTooltip: false,
      resizeColumn: true,
      rowCount: contacts.data.row_count,
      totalCount: contacts.data.total_count,
    }"
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
    v-else-if="!isMobileView && contacts.data && !rows.length"
    name="Contacts"
    :icon="ContactsIcon"
  />
  <ContactModal
    v-if="showContactModal"
    v-model="showContactModal"
    :contact="{}"
  />
</template>

<script setup>
import ViewBreadcrumbs from '@/components/ViewBreadcrumbs.vue'
import CustomActions from '@/components/CustomActions.vue'
import ContactsIcon from '@/components/Icons/ContactsIcon.vue'
import LayoutHeader from '@/components/LayoutHeader.vue'
import ContactModal from '@/components/Modals/ContactModal.vue'
import ContactsListView from '@/components/ListViews/ContactsListView.vue'
import EmptyState from '@/components/ListViews/EmptyState.vue'
import ViewControls from '@/components/ViewControls.vue'
import ElencoContatti from '@/components/Mobile/ElencoContatti.vue'
import PulsanteAggiungi from '@/components/Mobile/PulsanteAggiungi.vue'
import { isMobileView } from '@/composables/breakpoints'
import { usersStore } from '@/stores/users'
import { getMeta } from '@/stores/meta'
import { organizationsStore } from '@/stores/organizations.js'
import { formatDate } from '@/utils'
import { timestampCell } from '@/composables/useTimelinePreferences'
import { ref, computed } from 'vue'

const { getFormattedPercent, getFormattedFloat, getFormattedCurrency } =
  getMeta('Contact')
const { getOrganization } = organizationsStore()
const { puo } = usersStore()

const showContactModal = ref(false)

const contactsListView = ref(null)

// contacts data is loaded in the ViewControls component
const contacts = ref({})
const loadMore = ref(1)
const triggerResize = ref(1)
const updatedPageCount = ref(20)
const viewControls = ref(null)

const rows = computed(() => {
  if (
    !contacts.value?.data?.data ||
    !['list', 'group_by'].includes(contacts.value.data.view_type)
  )
    return []
  return contacts.value?.data.data.map((contact) => {
    let _rows = {}
    contacts.value?.data.rows.forEach((row) => {
      _rows[row] = contact[row]

      let fieldType = contacts.value?.data.columns?.find(
        (col) => (col.key || col.value) == row,
      )?.type

      if (
        fieldType &&
        ['Date', 'Datetime'].includes(fieldType) &&
        !['modified', 'creation'].includes(row)
      ) {
        _rows[row] = formatDate(contact[row], '', true, fieldType == 'Datetime')
      }

      if (fieldType && fieldType == 'Currency') {
        _rows[row] = getFormattedCurrency(row, contact)
      }

      if (fieldType && fieldType == 'Float') {
        _rows[row] = getFormattedFloat(row, contact)
      }

      if (fieldType && fieldType == 'Percent') {
        _rows[row] = getFormattedPercent(row, contact)
      }

      if (row == 'full_name') {
        _rows[row] = {
          label: contact.full_name,
          image_label: contact.full_name,
          image: contact.image,
        }
      } else if (row == 'company_name') {
        _rows[row] = {
          label: contact.company_name,
          logo: getOrganization(contact.company_name)?.organization_logo,
        }
      } else if (['modified', 'creation'].includes(row)) {
        _rows[row] = timestampCell(contact[row])
      }
    })
    return _rows
  })
})

const columns = computed(() => {
  let _columns = contacts.value?.data?.columns || []

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
</script>
