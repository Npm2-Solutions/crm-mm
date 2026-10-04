<!--
  Modifications copyright (c) 2026, NPM2 Solutions Srl
-->
<template>
  <CreateDocumentModal
    v-if="showCreateDocumentModal"
    v-model="showCreateDocumentModal"
    :doctype="createDocumentDoctype"
    :data="createDocumentData"
    @callback="(data) => createDocumentCallback(data)"
  />
  <QuickEntryModal
    v-if="showQuickEntryModal"
    v-model="showQuickEntryModal"
    v-bind="quickEntryProps"
  />
  <ChangePasswordModal
    v-if="showChangePasswordModal"
    v-model="showChangePasswordModal"
  />
  <AboutModal v-model="showAboutModal" />
  <!-- Mounted here rather than in AppSidebar: a phone has no sidebar, and
       opens the settings from its "More" page. -->
  <Settings />
  <!-- the first steps: opened by their card, in the sidebar on a desktop and
       on the "More" page on a phone -->
  <FirstStepsPanel />
  <FieldLayoutDialogContainer />
  <!-- the invoice, made and read inside DottorCloud: from the invoices, the
       agenda, a cycle, a subscription. Mounted the first time one opens, then
       kept, so that closing it plays -->
  <InvoiceDialog v-if="fatturaAperta" />
</template>
<script setup>
import Settings from '@/components/Settings/Settings.vue'
import FirstStepsPanel from '@/components/FirstSteps/FirstStepsPanel.vue'
import FieldLayoutDialogContainer from '@/components/Modals/FieldLayoutDialogContainer.vue'
import AboutModal from '@/components/Modals/AboutModal.vue'
import { aRichiesta, apertoUnaVolta } from '@/utils/aRichiesta'
import { useFattura } from '@/composables/fattura'
import {
  showCreateDocumentModal,
  createDocumentDoctype,
  createDocumentData,
  createDocumentCallback,
} from '@/composables/document'
import {
  showQuickEntryModal,
  quickEntryProps,
  showAboutModal,
  showChangePasswordModal,
} from '@/composables/modals'
import { useAscoltoNotifiche } from '@/composables/notifiche'

// the dialogs come when they open: imported here, with the fields of every
// kind of record, they were in every page's first download
const CreateDocumentModal = aRichiesta(
  () => import('@/components/Modals/CreateDocumentModal.vue'),
  { attesa: false },
)
const QuickEntryModal = aRichiesta(
  () => import('@/components/Modals/QuickEntryModal.vue'),
  { attesa: false },
)
const ChangePasswordModal = aRichiesta(
  () => import('@/components/Modals/ChangePasswordModal.vue'),
  { attesa: false },
)
const InvoiceDialog = aRichiesta(
  () => import('@/components/Invoices/InvoiceDialog.vue'),
  { attesa: false },
)

const { stato: fattura } = useFattura()
const fatturaAperta = apertoUnaVolta(() => fattura.aperto)

// the notifications as they arrive, on the computer and on the phone alike
useAscoltoNotifiche()
</script>
