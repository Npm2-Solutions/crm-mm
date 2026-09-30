<template>
  <LayoutHeader>
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
  <div
    v-if="doc.name"
    class="flex h-12 items-center justify-between gap-2 border-b px-3 py-2.5"
  >
    <AssignTo v-model="assignees.data" doctype="CRM Lead" :docname="leadId" />
    <div class="flex items-center gap-2">
      <CustomActions
        v-if="document._actions?.length"
        :actions="document._actions"
      />
      <CustomActions
        v-if="document.actions?.length"
        :actions="document.actions"
      />
      <Button
        v-if="canWrite && puo('trattative.scrivi')"
        :label="__('New Deal')"
        variant="solid"
        @click="showConvertToDealModal = true"
      />
    </div>
  </div>
  <div v-if="doc.name" class="flex h-full overflow-hidden">
    <Tabs
      ref="tabsRef"
      v-model="tabIndex"
      as="div"
      :tabs="tabs"
      class="flex flex-1 overflow-auto flex-col [&>[role='tablist']>[role='tab']]:px-0 [&>[role='tablist']>[role='tab']]:shrink-0 [&>[role='tablist']]:px-3 [&>[role='tablist']]:min-h-[45px] [&>[role='tablist']]:gap-7.5 [&>[role='tabpanel']:not([hidden])]:flex [&>[role='tabpanel']:not([hidden])]:grow"
    >
      <template #tab-panel="{ tab }">
        <div v-if="tab.name == 'Details'">
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
              @afterFieldChange="reloadAssignees"
            >
              <template #after>
                <BillingProfileSection partyType="CRM Lead" :party="leadId" />
                <RelatedPeopleSection :lead="leadId" />
                <PatientSection :lead="leadId" />
                <CyclesSection :lead="leadId" />
                <ConsentsSection :lead="leadId" />
              </template>
            </SidePanelLayout>
          </div>
        </div>
        <Activities
          v-else
          v-model:reload="reload"
          v-model:tabIndex="tabIndex"
          doctype="CRM Lead"
          :docname="leadId"
          :tabs="tabs"
          @beforeSave="saveChange"
          @afterSave="reloadAssignees"
        />
      </template>
    </Tabs>
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
  <DeleteLinkedDocModal
    v-if="showDeleteLinkedDocModal"
    v-model="showDeleteLinkedDocModal"
    :doctype="'CRM Lead'"
    :docname="leadId"
    name="Leads"
  />
</template>
<script setup>
import DeleteLinkedDocModal from '@/components/DeleteLinkedDocModal.vue'
import ErrorPage from '@/components/ErrorPage.vue'
import Icon from '@/components/Icon.vue'
import DetailsIcon from '@/components/Icons/DetailsIcon.vue'
import EventIcon from '@/components/Icons/EventIcon.vue'
import ActivityIcon from '@/components/Icons/ActivityIcon.vue'
import PhoneIcon from '@/components/Icons/PhoneIcon.vue'
import TaskIcon from '@/components/Icons/TaskIcon.vue'
import NoteIcon from '@/components/Icons/NoteIcon.vue'
import AttachmentIcon from '@/components/Icons/AttachmentIcon.vue'
import LayoutHeader from '@/components/LayoutHeader.vue'
import Activities from '@/components/Activities/Activities.vue'
import LucideRadar from '~icons/lucide/radar'
import LucideStethoscope from '~icons/lucide/stethoscope'
import LucideFileSignature from '~icons/lucide/file-signature'
import LucideAppWindow from '~icons/lucide/app-window'
import LucideFolderOpen from '~icons/lucide/folder-open'
import LucideReceiptText from '~icons/lucide/receipt-text'
import { usersStore } from '@/stores/users'
import AssignTo from '@/components/AssignTo.vue'
import SidePanelLayout from '@/components/SidePanelLayout.vue'
import BillingProfileSection from '@/components/BillingProfileSection.vue'
import ConsentsSection from '@/components/ConsentsSection.vue'
import CyclesSection from '@/components/CyclesSection.vue'
import PatientSection from '@/components/PatientSection.vue'
import RelatedPeopleSection from '@/components/RelatedPeopleSection.vue'
import SLASection from '@/components/SLASection.vue'
import CustomActions from '@/components/CustomActions.vue'
import { setupCustomizations } from '@/utils'
import { getView } from '@/utils/view'
import { getSettings } from '@/stores/settings'
import { globalStore } from '@/stores/global'
import { getMeta } from '@/stores/meta'
import { useDocument } from '@/data/document'
import { isMobileView } from '@/composables/settings'
import { useActiveTabManager } from '@/composables/useActiveTabManager'
import { useSelectedTabInView } from '@/composables/selectedTabInView'
import {
  createResource,
  Tabs,
  Breadcrumbs,
  call,
  usePageMeta,
  toast,
} from 'frappe-ui'
import { ref, computed, watch, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import ConvertToDealModal from '@/components/Modals/ConvertToDealModal.vue'

const { brand } = getSettings()
const { $dialog, $socket } = globalStore()
const { doctypeMeta } = getMeta('CRM Lead')

const route = useRoute()
const { puo } = usersStore()
const router = useRouter()

const props = defineProps({
  leadId: { type: String, required: true },
})

const errorTitle = ref('')
const errorMessage = ref('')
const showDeleteLinkedDocModal = ref(false)

const { triggerOnRender, assignees, document, scripts, error, canWrite } =
  useDocument('CRM Lead', props.leadId)

const doc = computed(() => document.doc || {})

onMounted(async () => {
  if (document.doc) await triggerOnRender()
})

watch(error, (err) => {
  if (err) {
    errorTitle.value = __(
      err.exc_type == 'DoesNotExistError'
        ? __('Document Not Found')
        : __('Error Occurred'),
    )
    errorMessage.value = __(err.messages?.[0] || 'An Error Occurred')
  } else {
    errorTitle.value = ''
    errorMessage.value = ''
  }
})

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

const reload = ref(false)

const breadcrumbs = computed(() => {
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
  return doc.value?.[t] || props.leadId
})

usePageMeta(() => {
  return {
    title: title.value,
    icon: brand.favicon,
  }
})

const tabs = computed(() => {
  let tabOptions = [
    {
      name: 'Details',
      label: __('Details'),
      icon: DetailsIcon,
      condition: () => isMobileView.value,
    },
    {
      // Email, WhatsApp, SMS and comments used to be four tabs of their own.
      // They are one stream here now, with a channel picker above it: the
      // question anybody asks of a record is what has been said to this person
      // and in what order, and four tabs could only answer it three at a time.
      name: 'Activity',
      label: __('Activity'),
      icon: ActivityIcon,
    },
    {
      name: 'Data',
      label: __('Data'),
      icon: DetailsIcon,
    },
    // a person's appointments and events, as on a desk: the tab was missing on
    // a phone, so nothing booked for them could be seen from one
    {
      name: 'Events',
      label: __('Events'),
      icon: EventIcon,
      condition: () => puo('agenda.vedi'),
    },
    {
      name: 'Calls',
      label: __('Calls'),
      icon: PhoneIcon,
      condition: () => puo('telefono.registro'),
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
    {
      name: 'Tracking',
      label: __('Tracking'),
      icon: LucideRadar,
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
    // the person's own area: who enters it, the board the centre writes on,
    // the plans they follow there
    {
      name: 'Area',
      label: __('Client area'),
      icon: LucideAppWindow,
      condition: () =>
        puo('area.invita') ||
        puo('area.messaggi') ||
        puo('piani.vedi') ||
        puo('piani.scrivi'),
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
  ]
  return tabOptions.filter((tab) => (tab.condition ? tab.condition() : true))
})

const { tabIndex } = useActiveTabManager(tabs, 'lastLeadTab')
const tabsRef = ref(null)
useSelectedTabInView(tabsRef, tabIndex)

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

const showConvertToDealModal = ref(false)

function saveChange(data) {
  document.save.submit(null, {
    onSuccess: () => reloadAssignees(data),
  })
}
function reloadAssignees(data) {
  if (Object.hasOwn(data ?? {}, 'lead_owner')) {
    assignees.reload()
  }
}
</script>
