<!--
  Modifications copyright (c) 2026, NPM2 Solutions Srl

  The phone's person: their card with the calls and messages a thumb away, the
  tabs one opens every day in a short bar and the rest behind More. On the
  conversation the card waits folded and the chat has the screen, as in a
  phone's own messengers: the person's name in the header opens it.
-->
<template>
  <LayoutHeader>
    <header
      class="relative flex h-10.5 items-center justify-between gap-2 py-2.5 pl-2"
    >
      <Breadcrumbs :items="breadcrumbs" class="min-w-0">
        <template #prefix="{ item }">
          <Icon v-if="item.icon" :icon="item.icon" class="mr-2 h-4" />
        </template>
        <!-- on the conversation the name opens and folds the card -->
        <template #suffix="{ item }">
          <template v-if="item.scheda">
            <span
              class="ml-1 size-4 shrink-0 text-ink-gray-5"
              :class="raccolta ? 'lucide-chevron-down' : 'lucide-chevron-up'"
              aria-hidden="true"
            />
            <span class="sr-only">
              {{ raccolta ? __('Show the card') : __('Hide the card') }}
            </span>
          </template>
        </template>
      </Breadcrumbs>
      <!-- whom the person is with, beside their name as on the computer -->
      <div v-if="doc.name" class="flex shrink-0 items-center gap-2">
        <CustomActions
          v-if="document._actions?.length"
          :actions="document._actions"
        />
        <CustomActions
          v-if="document.actions?.length"
          :actions="document.actions"
        />
        <AssignTo
          v-model="assignees.data"
          doctype="CRM Lead"
          :docname="leadId"
        />
      </div>
    </header>
  </LayoutHeader>
  <!-- the phone's contact card: who, what comes next, call and write; while
       the tab below is scrolled it folds away, the name staying in the header
       (composables/testataRaccolta.js) -->
  <div
    v-if="doc.name"
    class="grid shrink-0 transition-[grid-template-rows] duration-200 ease-out motion-reduce:transition-none"
    :class="raccolta ? 'grid-rows-[0fr]' : 'grid-rows-[1fr]'"
    :inert="raccolta"
  >
    <div class="min-h-0 overflow-hidden">
      <div ref="testata" class="border-b px-3 pb-3 pt-3">
        <PersonHeader :doc="doc" :title="title" :more="altro" @write="scrivi">
          <template #avatar>
            <Avatar
              size="2xl"
              class="size-11 shrink-0"
              :label="title"
              :image="doc.image || doc.organization_logo"
            />
          </template>
        </PersonHeader>
      </div>
    </div>
  </div>
  <div
    v-if="doc.name"
    ref="schede"
    class="flex h-full flex-col overflow-hidden"
  >
    <!-- the tabs one opens every day, the rest behind More; while somebody
         writes in the chat they step aside (telefono.css, «11») -->
    <SchedeDelTelefono
      v-model="tabIndex"
      data-via-scrivendo
      :tabs="tabs"
      :principali="[
        'Activity',
        'Details',
        'Events',
        'Clinic',
        'Tasks',
        'Notes',
      ]"
    />
    <!-- The tabs' content, under the bar above: Details, mounted the first time
         it opens, and one conversation for every other tab - it draws the tab
         chosen. Both stay once opened. A tab per panel unmounted the one left and
         mounted the next, the conversation and its editor with it: half a second
         a tap on a slow phone, and what one was reading back at its top -->
    <div class="flex min-h-0 flex-1 flex-col overflow-auto">
      <div
        v-if="dettagliMontati"
        v-show="inDettagli"
        role="tabpanel"
        class="flex grow flex-col overflow-auto"
      >
        <div>
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
              <!-- below the fields, a screen and more down: they come once the
                   fields are drawn, not in the first tap on Details (seven
                   calls and their sections, a fifth of its time on a slow
                   phone) -->
              <template #after>
                <DopoIlDisegno>
                  <BillingProfileSection partyType="CRM Lead" :party="leadId" />
                  <RelatedPeopleSection :lead="leadId" />
                  <PatientSection :lead="leadId" />
                  <CyclesSection :lead="leadId" />
                  <SubscriptionsSection :lead="leadId" />
                  <WaitingSection :lead="leadId" />
                  <ConsentsSection :lead="leadId" />
                </DopoIlDisegno>
              </template>
            </SidePanelLayout>
          </div>
        </div>
      </div>
      <div
        v-if="attivitaMontate"
        v-show="!inDettagli"
        role="tabpanel"
        class="flex grow flex-col overflow-auto"
      >
        <Activities
          ref="activities"
          v-model:reload="reload"
          :tabIndex="schedaAttivita"
          doctype="CRM Lead"
          :docname="leadId"
          :tabs="tabs"
          @update:tabIndex="(indice) => (tabIndex = indice)"
          @beforeSave="saveChange"
          @afterSave="reloadAssignees"
        />
      </div>
    </div>
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
    :title="title"
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
import SchedeDelTelefono from '@/components/Mobile/SchedeDelTelefono.vue'
import Activities from '@/components/Activities/Activities.vue'
import PersonHeader from '@/components/PersonHeader.vue'
import LucideRadar from '~icons/lucide/radar'
import LucideStethoscope from '~icons/lucide/stethoscope'
import LucideFileSignature from '~icons/lucide/file-signature'
import LucideAppWindow from '~icons/lucide/app-window'
import LucideListChecks from '~icons/lucide/list-checks'
import LucideFolderOpen from '~icons/lucide/folder-open'
import LucideReceiptText from '~icons/lucide/receipt-text'
import { usersStore } from '@/stores/users'
import AssignTo from '@/components/AssignTo.vue'
import SidePanelLayout from '@/components/SidePanelLayout.vue'
import BillingProfileSection from '@/components/BillingProfileSection.vue'
import ConsentsSection from '@/components/ConsentsSection.vue'
import CyclesSection from '@/components/CyclesSection.vue'
import SubscriptionsSection from '@/components/Subscriptions/SubscriptionsSection.vue'
import WaitingSection from '@/components/Waiting/WaitingSection.vue'
import PatientSection from '@/components/PatientSection.vue'
import RelatedPeopleSection from '@/components/RelatedPeopleSection.vue'
import SLASection from '@/components/SLASection.vue'
import CustomActions from '@/components/CustomActions.vue'
import { setupCustomizations, openWebsite, copyToClipboard } from '@/utils'
import { getView } from '@/utils/view'
import { schedaChiusa, nomeInAttesa } from '@/utils/schedaChiusa'
import { getSettings } from '@/stores/settings'
import { globalStore } from '@/stores/global'
import { getMeta } from '@/stores/meta'
import { useDocument } from '@/data/document'
import { isMobileView } from '@/composables/settings'
import { useActiveTabManager } from '@/composables/useActiveTabManager'
import { useTestataRaccolta } from '@/composables/testataRaccolta'
import { useChatAperta } from '@/composables/chatAperta'
import { apertoUnaVolta } from '@/utils/aRichiesta'
import DopoIlDisegno from '@/components/DopoIlDisegno.vue'
import {
  Avatar,
  createResource,
  Breadcrumbs,
  call,
  usePageMeta,
  toast,
} from 'frappe-ui'
import { ref, computed, watch, onMounted, nextTick } from 'vue'
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

const showDeleteLinkedDocModal = ref(false)

const {
  triggerOnRender,
  assignees,
  permissions,
  document,
  scripts,
  error,
  canWrite,
} = useDocument('CRM Lead', props.leadId)

const canDelete = computed(() => permissions.data?.permissions?.delete || false)
const activities = ref(null)

const doc = computed(() => document.doc || {})

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

  // on the conversation the name is the card's: a tap opens it, another folds
  // it. Elsewhere it is the page's own link, as it was
  items.push(
    inChat.value
      ? { label: title.value, scheda: true, onClick: alternaLaScheda }
      : {
          label: title.value,
          route: {
            name: 'Lead',
            params: { leadId: props.leadId },
            query: route.query,
          },
        },
  )
  return items
})

const title = computed(() => {
  let t = doctypeMeta.value?.title_field || 'name'
  // not loaded, or not one's to open: a word, never the record's code
  if (!doc.value?.name) return nomeInAttesa('CRM Lead')
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
  ]
  return tabOptions.filter((tab) => (tab.condition ? tab.condition() : true))
})

const { tabIndex } = useActiveTabManager(tabs, 'lastLeadTab')

// Details is a tab of its own; every other one is the conversation, which draws
// the tab chosen - and while Details is shown stays on the one it drew, hidden
// as it was. Each is mounted the first time it opens, then kept
const inDettagli = computed(
  () => tabs.value[tabIndex.value]?.name === 'Details',
)
const schedaAttivita = ref(tabIndex.value)
watch(
  tabIndex,
  (indice) => {
    if (!inDettagli.value) schedaAttivita.value = indice
  },
  { immediate: true },
)
const dettagliMontati = apertoUnaVolta(inDettagli)
const attivitaMontate = apertoUnaVolta(() => !inDettagli.value)

// the card folds while a tab is scrolled, and opens at its top
const testata = ref(null)
const schede = ref(null)
const raccoltaScorrendo = useTestataRaccolta(schede, testata, tabIndex)

// The conversation is a chat: the card waits folded, the name in the header
// opens it (`alternaLaScheda`), somebody's scrolling folds it again. Open, the
// card and the bar at the bottom left the chat a quarter of an iPhone.
const inChat = computed(
  () => !inDettagli.value && tabs.value[tabIndex.value]?.name === 'Activity',
)
const schedaAperta = ref(false)
const raccolta = computed(
  () => !schedaAperta.value && (raccoltaScorrendo.value || inChat.value),
)
function alternaLaScheda() {
  schedaAperta.value = raccolta.value
  // scrolled before, the card would fold at the first move: it starts afresh
  raccoltaScorrendo.value = false
}
watch(raccoltaScorrendo, (si) => si && (schedaAperta.value = false))
watch(tabIndex, () => (schedaAperta.value = false))
// for whoever writes in it the bar at the bottom steps aside, and with the
// keyboard up the tabs: the box to write in is the screen's bottom
useChatAperta(() => inChat.value && puo('conversazioni.usa'))

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

// Writing from the card: the Activity tab, its composer on the channel chosen.
// From Details the tab is not drawn yet: it opens first, then the composer.
async function scrivi(canale) {
  const indice = tabs.value.findIndex((tab) => tab.name === 'Activity')
  if (indice >= 0 && tabIndex.value !== indice) {
    tabIndex.value = indice
    await nextTick()
    await nextTick()
  }
  activities.value?.write?.(canale)
}

// the card's More menu: what one does less often with a person
const altro = computed(() => [
  canWrite.value &&
    puo('trattative.scrivi') && {
      label: __('New Deal'),
      icon: 'plus',
      onClick: () => (showConvertToDealModal.value = true),
    },
  doc.value.website && {
    label: __('Go to Website'),
    icon: 'external-link',
    onClick: () => openWebsite(doc.value.website),
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
])

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
