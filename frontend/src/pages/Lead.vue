<!--
  Modifications copyright (c) 2026, NPM2 Solutions Srl
-->
<template>
  <LayoutHeader>
    <template #left-header>
      <Breadcrumbs :items="breadcrumbs">
        <template #prefix="{ item }">
          <Icon v-if="item.icon" :icon="item.icon" class="mr-2 h-4" />
        </template>
      </Breadcrumbs>
    </template>
    <template v-if="!errorTitle" #right-header>
      <CustomActions
        v-if="document._actions?.length"
        :actions="document._actions"
      />
      <CustomActions
        v-if="document.actions?.length"
        :actions="document.actions"
      />
      <!-- what a website says about the person: only where there is one -->
      <EnrichFromWebsite
        v-if="doc.website"
        doctype="CRM Lead"
        :docname="leadId"
        :website="doc.website"
        @done="onEnriched"
      />
      <AssignTo v-model="assignees.data" doctype="CRM Lead" :docname="leadId" />
      <Dropdown
        v-if="deals.data?.length"
        :options="dealOptions"
        placement="right"
      >
        <template #default="{ open }">
          <Button
            :label="__('Deals') + ' · ' + deals.data.length"
            :iconRight="open ? 'chevron-up' : 'chevron-down'"
          />
        </template>
      </Dropdown>
      <Button
        v-else-if="canOpenDeal"
        :label="__('New Deal')"
        variant="solid"
        @click="showConvertToDealModal = true"
      />
    </template>
  </LayoutHeader>
  <div v-if="doc.name" class="flex h-full overflow-hidden">
    <div class="flex min-w-0 flex-1 flex-col overflow-hidden">
      <Tabs
        v-model="tabIndex"
        :tabs="tabs"
        class="flex flex-1 overflow-hidden flex-col [&>[role='tablist']>[role='tab']]:px-0 [&>[role='tablist']>[role='tab']]:shrink-0 [&>[role='tablist']]:px-5 [&>[role='tablist']::-webkit-scrollbar]:h-0 [&>[role='tablist']]:min-h-[45px] [&>[role='tablist']]:gap-7.5 [&>[role='tabpanel']:not([hidden])]:flex [&>[role='tabpanel']:not([hidden])]:grow"
      >
        <template #tab-panel>
          <Activities
            ref="activities"
            v-model:reload="reload"
            v-model:tabIndex="tabIndex"
            doctype="CRM Lead"
            :docname="leadId"
            :tabs="tabs"
            @beforeSave="saveChange"
            @afterSave="reloadResources"
          />
        </template>
      </Tabs>
    </div>
    <Resizer class="flex flex-col justify-between border-l" side="right">
      <!-- who the person is, how to reach them, what comes next: the head
           the phone draws too (PersonHeader). The record's code, for copying,
           sits in its More menu: on top of the panel it read as its title -->
      <FileUploader
        :validateFile="validateIsImageFile"
        @success="(file) => updateField('image', file.file_url)"
      >
        <template #default="{ openFileSelector }">
          <div class="flex flex-col gap-2 border-b p-5">
            <PersonHeader
              :doc="doc"
              :title="title"
              :more="altro(openFileSelector)"
              @write="scrivi"
            >
              <template #avatar>
                <div class="group relative size-12 shrink-0">
                  <Avatar
                    size="3xl"
                    class="size-12"
                    :label="title"
                    :image="doc.image || doc.organization_logo"
                  />
                  <button
                    v-if="canWrite"
                    type="button"
                    class="absolute inset-0 flex items-end justify-center overflow-hidden rounded-full opacity-0 transition-opacity focus-visible:opacity-100 group-hover:opacity-100"
                    :aria-label="
                      doc.image ? __('Change Image') : __('Upload Image')
                    "
                    @click="openFileSelector"
                  >
                    <span
                      class="flex h-5 w-full items-center justify-center bg-black/40"
                    >
                      <CameraIcon class="size-3.5 text-white" />
                    </span>
                  </button>
                </div>
              </template>
            </PersonHeader>
            <ErrorMessage :message="__(error)" />
          </div>
        </template>
      </FileUploader>
      <SLASection
        v-if="doc.sla_status"
        v-model="doc"
        @updateField="updateField"
      />
      <div
        v-if="sections.data"
        class="flex flex-1 flex-col justify-between overflow-hidden"
      >
        <SidePanelLayout
          :sections="sections.data"
          doctype="CRM Lead"
          :docname="leadId"
          @reload="sections.reload"
          @beforeFieldChange="saveChange"
          @afterFieldChange="reloadResources"
        >
          <template #after>
            <BillingProfileSection partyType="CRM Lead" :party="leadId" />
            <RelatedPeopleSection :lead="leadId" />
            <ConventionCoversSection :lead="leadId" />
            <PatientSection :lead="leadId" />
            <ConsentsSection :lead="leadId" />
          </template>
        </SidePanelLayout>
      </div>
    </Resizer>
  </div>
  <ErrorPage
    v-else-if="errorTitle"
    :errorTitle="errorTitle"
    :errorMessage="errorMessage"
  />
  <ConvertToDealModal
    v-if="showConvertToDealModal"
    v-model="showConvertToDealModal"
    :lead="doc"
  />
  <FilesUploader
    v-model="showFilesUploader"
    doctype="CRM Lead"
    :docname="leadId"
    @after="
      () => {
        activities?.all_activities?.reload()
        changeTabTo('attachments')
      }
    "
  />
  <DeleteLinkedDocModal
    v-if="showDeleteLinkedDocModal"
    v-model="showDeleteLinkedDocModal"
    :doctype="'CRM Lead'"
    :docname="leadId"
    :title="title"
    name="Leads"
  />
</template>
<script setup>
import DeleteLinkedDocModal from '@/components/DeleteLinkedDocModal.vue'
import ErrorPage from '@/components/ErrorPage.vue'
import Icon from '@/components/Icon.vue'
import Resizer from '@/components/Resizer.vue'
import ActivityIcon from '@/components/Icons/ActivityIcon.vue'
import EventIcon from '@/components/Icons/EventIcon.vue'
import TaskIcon from '@/components/Icons/TaskIcon.vue'
import NoteIcon from '@/components/Icons/NoteIcon.vue'
import CameraIcon from '@/components/Icons/CameraIcon.vue'
import AttachmentIcon from '@/components/Icons/AttachmentIcon.vue'
import LayoutHeader from '@/components/LayoutHeader.vue'
import Activities from '@/components/Activities/Activities.vue'
import PersonHeader from '@/components/PersonHeader.vue'
import LucideRadar from '~icons/lucide/radar'
import LucideLayoutList from '~icons/lucide/layout-list'
import LucideTicket from '~icons/lucide/ticket'
import LucideStethoscope from '~icons/lucide/stethoscope'
import LucideFileSignature from '~icons/lucide/file-signature'
import LucideAppWindow from '~icons/lucide/app-window'
import LucideListChecks from '~icons/lucide/list-checks'
import LucideFolderOpen from '~icons/lucide/folder-open'
import LucideReceiptText from '~icons/lucide/receipt-text'
import { usersStore } from '@/stores/users'
import AssignTo from '@/components/AssignTo.vue'
import FilesUploader from '@/components/FilesUploader/FilesUploader.vue'
import SidePanelLayout from '@/components/SidePanelLayout.vue'
import BillingProfileSection from '@/components/BillingProfileSection.vue'
import ConsentsSection from '@/components/ConsentsSection.vue'
import PatientSection from '@/components/PatientSection.vue'
import RelatedPeopleSection from '@/components/RelatedPeopleSection.vue'
import ConventionCoversSection from '@/components/ConventionCoversSection.vue'
import SLASection from '@/components/SLASection.vue'
import CustomActions from '@/components/CustomActions.vue'
import ConvertToDealModal from '@/components/Modals/ConvertToDealModal.vue'
import EnrichFromWebsite from '@/components/EnrichFromWebsite.vue'
import {
  openWebsite,
  setupCustomizations,
  copyToClipboard,
  validateIsImageFile,
} from '@/utils'
import { getView } from '@/utils/view'
import { schedaChiusa, nomeInAttesa } from '@/utils/schedaChiusa'
import { getSettings } from '@/stores/settings'
import { globalStore } from '@/stores/global'
import { getMeta } from '@/stores/meta'
import { useDocument } from '@/data/document'
import {
  createResource,
  FileUploader,
  Dropdown,
  Avatar,
  Tabs,
  Breadcrumbs,
  call,
  usePageMeta,
  toast,
} from 'frappe-ui'
import { ref, computed, watch, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useActiveTabManager } from '@/composables/useActiveTabManager'
import { useUnsavedChangesWarning } from '@/composables/useUnsavedChangesWarning'

const { brand } = getSettings()
const { $dialog, $socket } = globalStore()
const { doctypeMeta } = getMeta('CRM Lead')

const route = useRoute()
const { puo } = usersStore()
const router = useRouter()

const props = defineProps({
  leadId: { type: String, required: true },
})

const reload = ref(false)
const activities = ref(null)
const showDeleteLinkedDocModal = ref(false)
const showConvertToDealModal = ref(false)

// a person has no relationship with us, or one, or several — the deal is the
// relationship, not what the person turns into. Opening another one never takes
// this page away from anybody.
const deals = createResource({
  url: 'crm.api.lead.get_deals',
  params: { lead: props.leadId },
})

const dealOptions = computed(() => [
  ...(deals.data || []).map((deal) => ({
    label: deal.organization || deal.name,
    onClick: () => router.push({ name: 'Deal', params: { dealId: deal.name } }),
  })),
  ...(canOpenDeal.value
    ? [
        {
          label: __('New Deal'),
          icon: 'plus',
          onClick: () => (showConvertToDealModal.value = true),
        },
      ]
    : []),
])
const showFilesUploader = ref(false)

const {
  triggerOnRender,
  assignees,
  permissions,
  document,
  scripts,
  error,
  canWrite,
  pronto,
} = useDocument('CRM Lead', props.leadId)
// once the person came: a person one does not follow asks nothing more, and the
// page says why
pronto.then((venuto) => venuto && deals.fetch().catch(() => {}))

const canDelete = computed(() => permissions.data?.permissions?.delete || false)
// opening a deal writes the person too (doc 30): whoever reads it does not
const canOpenDeal = computed(() => canWrite.value && puo('trattative.scrivi'))

const doc = computed(() => document.doc || {})

useUnsavedChangesWarning(() => document.isDirty)

onMounted(async () => {
  if (document.doc) await triggerOnRender()
})

// why the page did not open, in words (a person one does not follow, one gone)
const chiusa = computed(() => schedaChiusa(error.value, 'CRM Lead'))
const errorTitle = computed(() => chiusa.value?.titolo || '')
const errorMessage = computed(() => chiusa.value?.testo || '')

watch(
  () => document.doc,
  async (_doc) => {
    if (scripts.data?.length) {
      let s = await setupCustomizations(scripts.data, {
        doc: _doc,
        $dialog,
        $socket,
        router,
        toast,
        updateField,
        createToast: toast.create,
        deleteDoc: deleteLead,
        call,
      })
      document._actions = s.actions || []
    }
  },
  { once: true },
)

const breadcrumbs = computed(() => {
  // the list is called People everywhere else — the sidebar, the list itself
  let items = [{ label: __('People'), route: { name: 'Leads' } }]

  if (route.query.view || route.query.viewType) {
    let view = getView(route.query.view, route.query.viewType, 'CRM Lead')
    if (view) {
      items.push({
        label: __(view.label),
        icon: view.icon,
        route: {
          name: 'Leads',
          params: { viewType: route.query.viewType },
          query: { view: route.query.view },
        },
      })
    }
  }

  items.push({
    label: title.value,
    route: {
      name: 'Lead',
      params: { leadId: props.leadId },
      query: route.query,
    },
  })
  return items
})

const title = computed(() => {
  let t = doctypeMeta.value?.title_field || 'name'
  // not loaded, or not one's to open: a word, never the record's code
  if (!doc.value?.name) return nomeInAttesa('CRM Lead')
  return doc.value?.[t] || props.leadId
})

usePageMeta(() => {
  return { title: title.value, icon: brand.favicon }
})

const tabs = computed(() => {
  let tabOptions = [
    // what one needs to know of the person, where their page opens from the
    // People list and the agenda; the conversations open it on the chat
    {
      name: 'Summary',
      label: __('Summary', null, 'Person tab'),
      icon: LucideLayoutList,
    },
    {
      // Email, WhatsApp, SMS and comments used to be four tabs of their own.
      // They are one stream here now, with a channel picker above it: the
      // question anybody asks of a record is what has been said to this person
      // and in what order, and four tabs could only answer it three at a time.
      // The chat, as the conversations call it: the same one, the other door
      name: 'Activity',
      label: __('Chat'),
      icon: ActivityIcon,
    },
    {
      name: 'Events',
      label: __('Events'),
      icon: EventIcon,
      condition: () => puo('agenda.vedi'),
    },
    // what the person has going beyond one appointment: subscriptions, cycles
    // of sessions, what they wait for - once under their data
    {
      name: 'Subscriptions',
      label: __('Subscriptions'),
      icon: LucideTicket,
      condition: () =>
        puo('agenda.vedi') ||
        puo('agenda.cicli') ||
        puo('agenda.abbonamenti') ||
        puo('agenda.attese'),
    },
    {
      name: 'Tasks',
      label: __('Tasks'),
      icon: TaskIcon,
    },
    {
      name: 'Notes',
      label: __('Notes'),
      icon: NoteIcon,
      condition: () => puo('note.vedi'),
    },
    {
      name: 'Attachments',
      label: __('Attachments'),
      icon: AttachmentIcon,
    },
    // the forms the person filled and signed: privacy, consents, questionnaires
    {
      name: 'Forms',
      label: __('Forms'),
      icon: LucideFileSignature,
      condition: () => puo('moduli.vedi'),
    },
    // the person's documents: what they brought or sent, signed forms, contracts;
    // with the clinic the tests and reports too
    {
      name: 'Documents',
      label: __('Documents'),
      icon: LucideFolderOpen,
      condition: () => puo('documenti.vedi') || puo('documenti.aggiungi'),
    },
    // the person's quotes, and how they are going; with the clinic, the care plans
    {
      name: 'Quotes',
      label: __('Quotes'),
      icon: LucideReceiptText,
      condition: () =>
        puo('preventivi.vedi') ||
        puo('preventivi.scrivi') ||
        puo('preventivi.gestisci'),
    },
    // what the person follows between appointments - a training, habits, a
    // diet, exercises at home - written here and followed in their area. A tab
    // of its own: inside the area's, under the board, nobody found them
    {
      name: 'Plans',
      label: __('Plans'),
      icon: LucideListChecks,
      condition: () => puo('piani.vedi') || puo('piani.scrivi'),
    },
    // the person's own area: who enters it, the board the centre writes on
    {
      name: 'Area',
      label: __('Client area'),
      icon: LucideAppWindow,
      condition: () => puo('area.invita') || puo('area.messaggi'),
    },
    // the clinical record, for whoever cares for the person: visits and notes,
    // signed and then only added to. Where the plan has no clinic, no tab
    {
      name: 'Clinic',
      label: __('Clinic'),
      icon: LucideStethoscope,
      condition: () =>
        puo('clinica.vedi') || puo('clinica.scrivi') || puo('clinica.accessi'),
    },
    // where the person came from and what they did before writing: the ad, the
    // visits to the site, the first and last touch. Last of all: it is looked
    // at now and then, never every day
    {
      name: 'Tracking',
      label: __('History'),
      icon: LucideRadar,
    },
  ]
  return tabOptions.filter((tab) => (tab.condition ? tab.condition() : true))
})

const { tabIndex, changeTabTo } = useActiveTabManager(tabs, 'lastLeadTab')

const sections = createResource({
  url: 'crm.fcrm.doctype.crm_fields_layout.crm_fields_layout.get_sidepanel_sections',
  cache: ['sidePanelSections', 'CRM Lead'],
  params: { doctype: 'CRM Lead' },
  auto: true,
})

function updateField(name, value) {
  value = Array.isArray(name) ? '' : value
  let oldValues = Array.isArray(name) ? {} : doc.value[name]

  if (Array.isArray(name)) {
    name.forEach((field) => (doc.value[field] = value))
  } else {
    doc.value[name] = value
  }

  document.save.submit(null, {
    onSuccess: () => (reload.value = true),
    onError: (err) => {
      if (Array.isArray(name)) {
        name.forEach((field) => (doc.value[field] = oldValues[field]))
      } else {
        doc.value[name] = oldValues
      }
      toast.error(err.messages?.[0] || __('Error updating field'))
    },
  })
}

function deleteLead() {
  showDeleteLinkedDocModal.value = true
}

// Writing from the head of the page: the Activity tab, its composer on the
// channel chosen, the cursor in it - from whatever tab is open.
function scrivi(canale) {
  activities.value?.write?.(canale)
}

// the head's More menu: what one does less often with a person
function altro(openFileSelector) {
  return [
    doc.value.website && {
      label: __('Go to Website'),
      icon: 'external-link',
      onClick: () => openWebsite(doc.value.website),
    },
    canWrite.value && {
      label: doc.value.image ? __('Change Image') : __('Upload Image'),
      icon: 'camera',
      onClick: openFileSelector,
    },
    canWrite.value && {
      label: __('Attach a File'),
      icon: 'paperclip',
      onClick: () => (showFilesUploader.value = true),
    },
    {
      // the page's address, to send a colleague: its code said nothing to anybody
      label: __('Copy the link'),
      icon: 'link',
      onClick: () =>
        copyToClipboard(window.location.origin + window.location.pathname),
    },
    canDelete.value && {
      label: __('Delete'),
      icon: 'trash-2',
      theme: 'red',
      onClick: deleteLead,
    },
  ]
}

function saveChange(data) {
  document.save.submit(null, {
    onSuccess: () => reloadResources(data),
  })
}

function onEnriched() {
  document.reload?.()
  sections.reload()
}

function reloadResources(data) {
  if (Object.hasOwn(data ?? {}, 'lead_owner')) {
    assignees.reload()
  }
}
</script>
