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
       agenda, a cycle, a subscription -->
  <InvoiceDialog />
</template>
<script setup>
import Settings from '@/components/Settings/Settings.vue'
import FirstStepsPanel from '@/components/FirstSteps/FirstStepsPanel.vue'
import FieldLayoutDialogContainer from '@/components/Modals/FieldLayoutDialogContainer.vue'
import InvoiceDialog from '@/components/Invoices/InvoiceDialog.vue'
import ChangePasswordModal from '@/components/Modals/ChangePasswordModal.vue'
import CreateDocumentModal from '@/components/Modals/CreateDocumentModal.vue'
import QuickEntryModal from '@/components/Modals/QuickEntryModal.vue'
import AboutModal from '@/components/Modals/AboutModal.vue'
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

// the notifications as they arrive, on the computer and on the phone alike
useAscoltoNotifiche()
</script>
