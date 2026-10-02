<template>
  <!-- the page fills the pane: what is long scrolls inside it, the buttons stay -->
  <div class="flex min-h-0 flex-1 flex-col p-8 max-md:px-5 max-md:py-5">
    <div v-if="step === 'email-list'" class="flex min-h-0 flex-1 flex-col">
      <EmailAccountList @update:step="updateStep" />
    </div>
    <!-- a new mailbox and one to change: the same form -->
    <div v-else class="flex min-h-0 flex-1 flex-col">
      <EmailEdit :account-data="accountData" @update:step="updateStep" />
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import EmailAccountList from './EmailAccountList.vue'
import EmailEdit from './EmailEdit.vue'

const step = ref('email-list')
const accountData = ref(null)
function updateStep(newStep, data) {
  step.value = newStep
  accountData.value = data || {}
}
</script>
