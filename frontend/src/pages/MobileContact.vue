<!--
  Modifications copyright (c) 2026, NPM2 Solutions Srl
-->
<template>
  <LayoutHeader v-if="contact.doc">
    <header
      class="relative flex h-10.5 items-center justify-between gap-2 py-2.5 pl-2"
    >
      <Breadcrumbs :items="breadcrumbs">
        <template #prefix="{ item }">
          <Icon v-if="item.icon" :icon="item.icon" class="mr-2 h-4" />
        </template>
      </Breadcrumbs>
    </header>
  </LayoutHeader>
  <div v-if="contact.doc" class="flex flex-col h-full overflow-hidden">
    <FileUploader
      :validateFile="validateIsImageFile"
      @success="changeContactImage"
    >
      <template #default="{ openFileSelector, error }">
        <TestataDellaScheda
          :titolo="nomeDelContatto"
          :nome="contact.doc.full_name"
          :riga="contact.doc.company_name"
          :immagine="contact.doc.image"
          :puoCambiare="canWrite"
          :altro="altro"
          :errore="error ? __(error) : ''"
          @scegli="openFileSelector"
          @togli="changeContactImage('')"
        >
          <Button
            v-if="callEnabled && contact.doc.mobile_no"
            :label="__('Make a Call')"
            :iconLeft="PhoneIcon"
            @click="makeCall(contact.doc.mobile_no)"
          />
        </TestataDellaScheda>
      </template>
    </FileUploader>
    <Tabs
      v-model="tabIndex"
      as="div"
      :tabs="tabs"
      class="flex flex-1 overflow-auto flex-col [&>[role='tablist']]:gap-3 [&>[role='tablist']]:px-4 [&>[role='tabpanel']:not([hidden])]:flex [&>[role='tabpanel']:not([hidden])]:grow"
    >
      <template #tab-item="{ tab, selected }">
        <button
          v-if="tab.name == 'Deals'"
          class="group flex items-center gap-2 border-b border-transparent py-2.5 text-base text-ink-gray-5 duration-300 ease-in-out hover:text-ink-gray-9 !px-4"
          :class="{ 'text-ink-gray-9': selected }"
        >
          <component :is="tab.icon" v-if="tab.icon" class="h-5" />
          {{ __(tab.label) }}
          <Badge
            class="group-hover:bg-surface-gray-10"
            :class="[selected ? 'bg-surface-gray-10' : 'bg-gray-600']"
            variant="solid"
            theme="gray"
            size="sm"
          >
            {{ tab.count }}
          </Badge>
        </button>
      </template>
      <template #tab-panel="{ tab }">
        <div v-if="tab.name == 'Details'">
          <div
            v-if="sections.data"
            class="flex flex-1 flex-col justify-between overflow-hidden"
          >
            <SidePanelLayout
              :sections="sections.data"
              doctype="Contact"
              :docname="contact.doc.name"
              @reload="sections.reload"
            />
          </div>
        </div>
        <DealsListView
          v-else-if="tab.name === 'Deals' && rows.length"
          class="mt-4"
          :rows="rows"
          :columns="columns"
          :options="{ selectable: false, showTooltip: false }"
        />
        <!-- by the tab's name: its label is in the reader's language, and
             the deals never showed in Italian -->
        <EmptyState
          v-if="tab.name === 'Deals' && !rows.length"
          name="Deals"
          title="No deals yet"
          description="The deals this contact takes part in appear here."
        />
      </template>
    </Tabs>
  </div>
  <ErrorPage
    v-else-if="chiusa"
    :errorTitle="chiusa.titolo"
    :errorMessage="chiusa.testo"
  />
</template>

<script setup>
import Icon from '@/components/Icon.vue'
import SidePanelLayout from '@/components/SidePanelLayout.vue'
import LayoutHeader from '@/components/LayoutHeader.vue'
import DetailsIcon from '@/components/Icons/DetailsIcon.vue'
import PhoneIcon from '@/components/Icons/PhoneIcon.vue'
import TestataDellaScheda from '@/components/Mobile/TestataDellaScheda.vue'
import DealsIcon from '@/components/Icons/DealsIcon.vue'
import DealsListView from '@/components/ListViews/DealsListView.vue'
import EmptyState from '@/components/ListViews/EmptyState.vue'
import { validateIsImageFile, copyToClipboard } from '@/utils'
import { useContactFields } from '@/composables/useContactFields'
import { timestampCell } from '@/composables/useTimelinePreferences'
import { getView } from '@/utils/view'
import { schedaChiusa } from '@/utils/schedaChiusa'
import ErrorPage from '@/components/ErrorPage.vue'
import { useDocument } from '@/data/document'
import { getSettings } from '@/stores/settings'
import { getMeta } from '@/stores/meta'
import { globalStore } from '@/stores/global.js'
import { usersStore } from '@/stores/users.js'
import { organizationsStore } from '@/stores/organizations.js'
import { statusesStore } from '@/stores/statuses'
import { callEnabled } from '@/composables/telephony'
import {
  Breadcrumbs,
  FileUploader,
  Tabs,
  call,
  createResource,
  usePageMeta,
  toast,
} from 'frappe-ui'
import { useDoctypeModal } from '@/composables/doctypeModal'
import { useTelemetry } from 'frappe-ui/frappe'
import { ref, computed, h, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'

const { brand } = getSettings()
const { $dialog, makeCall } = globalStore()

const { getUser } = usersStore()
const { getOrganization } = organizationsStore()
const { getDealStatus } = statusesStore()
const { doctypeMeta } = getMeta('Contact')
const { capture } = useTelemetry()

const props = defineProps({
  contactId: { type: String, required: true },
})

const route = useRoute()
const router = useRouter()

const {
  document: contact,
  permissions,
  canWrite,
  triggerOnRender,
  error: nonSiApre,
} = useDocument('Contact', props.contactId)

const canDelete = computed(() => permissions.data?.permissions?.delete || false)

// why the page did not open, in words
const chiusa = computed(() => schedaChiusa(nonSiApre.value, 'Contact'))

const transformField = useContactFields(contact)

onMounted(async () => {
  if (contact.doc) await triggerOnRender()
})

const breadcrumbs = computed(() => {
  let items = [{ label: __('Contacts'), route: { name: 'Contacts' } }]

  if (route.query.view || route.query.viewType) {
    let view = getView(route.query.view, route.query.viewType, 'Contact')
    if (view) {
      items.push({
        label: __(view.label),
        icon: view.icon,
        route: {
          name: 'Contacts',
          params: { viewType: route.query.viewType },
          query: { view: route.query.view },
        },
      })
    }
  }

  items.push({
    label: title.value,
    route: {
      name: 'Contact',
      params: { contactId: props.contactId },
      query: route.query,
    },
  })
  return items
})

const title = computed(() => {
  let t = doctypeMeta.value?.title_field || 'name'
  return contact.doc?.[t] || props.contactId
})

usePageMeta(() => {
  return {
    title: title.value,
    icon: brand.favicon,
  }
})

function changeContactImage(file) {
  contact.doc.image = file?.file_url || ''
  contact.save.submit(null, {
    onSuccess: () => {
      toast.success(__('Contact Image Updated'))
    },
  })
}

// with its salutation, as the computer's page writes it, in the reader's
// language: «Mr» is «Sig.», which carries its own dot
const nomeDelContatto = computed(() => {
  const titolo = contact.doc?.salutation ? __(contact.doc.salutation) : ''
  return [
    titolo && (titolo.endsWith('.') ? titolo : `${titolo}.`),
    contact.doc?.full_name,
  ]
    .filter(Boolean)
    .join(' ')
})

// under «⋯», as on a person's page: the link to send a colleague, deleting last
const altro = computed(() => [
  {
    label: __('Copy the link'),
    icon: 'link',
    onClick: () =>
      copyToClipboard(window.location.origin + window.location.pathname),
  },
  canDelete.value && {
    label: __('Delete'),
    icon: 'trash-2',
    theme: 'red',
    onClick: deleteContact,
  },
])

async function deleteContact() {
  $dialog({
    title: __('Delete Contact'),
    message: __('Are you sure you want to delete this contact?'),
    actions: [
      {
        label: __('Delete'),
        theme: 'red',
        variant: 'solid',
        async onClick(close) {
          await call('frappe.client.delete', {
            doctype: 'Contact',
            name: props.contactId,
          })
          close()
          router.push({ name: 'Contacts' })
        },
      },
    ],
  })
}

const tabIndex = ref(0)
const tabs = [
  {
    name: 'Details',
    label: __('Details'),
    icon: DetailsIcon,
  },
  {
    name: 'Deals',
    label: __('Deals'),
    icon: h(DealsIcon, { class: 'h-4 w-4' }),
    count: computed(() => deals.data?.length),
  },
]

const deals = createResource({
  url: 'crm.api.contact.get_linked_deals',
  cache: ['deals', props.contactId],
  params: { contact: props.contactId },
  auto: true,
})

const rows = computed(() => {
  if (!deals.data || deals.data == []) return []

  return deals.data.map((row) => getDealRowObject(row))
})

const sections = createResource({
  url: 'crm.fcrm.doctype.crm_fields_layout.crm_fields_layout.get_sidepanel_sections',
  cache: ['sidePanelSections', 'Contact'],
  params: { doctype: 'Contact' },
  auto: true,
  transform: (data) => computed(() => getParsedSections(data)),
})

function getParsedSections(_sections) {
  return _sections.map((section) => {
    section.columns = section.columns.map((column) => {
      column.fields = column.fields.map((field) =>
        transformField(field, { showAddressModal }),
      )
      return column
    })
    return section
  })
}

const { getFormattedCurrency } = getMeta('CRM Deal')

const columns = computed(() => dealColumns)

function getDealRowObject(deal) {
  return {
    name: deal.name,
    organization: {
      label: deal.organization,
      logo: getOrganization(deal.organization)?.organization_logo,
    },
    deal_value: getFormattedCurrency('deal_value', deal),
    status: {
      label: deal.status,
      color: getDealStatus(deal.status)?.color,
    },
    email: deal.email,
    mobile_no: deal.mobile_no,
    deal_owner: {
      label: deal.deal_owner && getUser(deal.deal_owner).full_name,
      ...(deal.deal_owner && getUser(deal.deal_owner)),
    },
    modified: timestampCell(deal.modified),
  }
}

const dealColumns = [
  {
    label: __('Organization'),
    key: 'organization',
    width: '11rem',
  },
  {
    label: __('Amount'),
    key: 'deal_value',
    align: 'right',
    width: '9rem',
  },
  {
    label: __('Status'),
    key: 'status',
    // the stage's name in the reader's language, as in the deals' own list
    options: 'CRM Deal Status',
    width: '10rem',
  },
  {
    label: __('Email'),
    key: 'email',
    width: '12rem',
  },
  {
    label: __('Mobile Number'),
    key: 'mobile_no',
    width: '11rem',
  },
  {
    label: __('Deal Owner'),
    key: 'deal_owner',
    width: '10rem',
  },
  {
    label: __('Last Modified'),
    key: 'modified',
    width: '8rem',
  },
]

const { showModal } = useDoctypeModal()

function showAddressModal(_address) {
  showModal({
    name: _address || null,
    doctype: 'Address',
    callbacks: {
      afterInsert: (d) => {
        capture('address_created')
        contact.doc.address = d.name
        contact.save.submit()
      },
    },
  })
}
</script>
