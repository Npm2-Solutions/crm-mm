<!--
  Modifications copyright (c) 2026, NPM2 Solutions Srl

  Settings > Phone > Telephony and the pages it opens: the carrier's - Twilio
  or Telnyx (doc 64) -, the answering service, transcription, the numbers
  shown on calls.
-->
<template>
  <TelephonySettings
    v-if="step === 'telephony-settings'"
    @updateStep="updateStep"
  />
  <TwilioSettings
    v-else-if="step === 'twilio-settings'"
    @updateStep="updateStep"
  />
  <TelnyxSettings
    v-else-if="step === 'telnyx-settings'"
    @updateStep="updateStep"
  />
  <AnsweringServiceSettings
    v-else-if="step === 'answering-settings'"
    @updateStep="updateStep"
  />
  <TranscriptionSettings
    v-else-if="step === 'transcription-settings'"
    @updateStep="updateStep"
  />
  <CallerIdSettings
    v-else-if="step === 'caller-id-settings'"
    @updateStep="updateStep"
  />
</template>
<script setup>
import TelephonySettings from './TelephonySettings.vue'
import TwilioSettings from './TwilioSettings.vue'
import TelnyxSettings from './TelnyxSettings.vue'
import AnsweringServiceSettings from './AnsweringServiceSettings.vue'
import TranscriptionSettings from './TranscriptionSettings.vue'
import CallerIdSettings from './CallerIdSettings.vue'
import { activeTelephonyStep } from '@/composables/settings'
import { ref, watch } from 'vue'

const step = ref(activeTelephonyStep.value || 'telephony-settings')
activeTelephonyStep.value = ''

// a notification about a new number opens the carrier's step, the page open or not
watch(activeTelephonyStep, (passo) => {
  if (!passo) return
  step.value = passo
  activeTelephonyStep.value = ''
})

function updateStep(newStep) {
  step.value = newStep
}
</script>
