<template>
  <TelephonySettings
    v-if="step === 'telephony-settings'"
    @updateStep="updateStep"
  />
  <TwilioSettings
    v-else-if="step === 'twilio-settings'"
    @updateStep="updateStep"
  />
  <ExotelSettings
    v-else-if="step === 'exotel-settings'"
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
import ExotelSettings from './ExotelSettings.vue'
import TwilioSettings from './TwilioSettings.vue'
import AnsweringServiceSettings from './AnsweringServiceSettings.vue'
import TranscriptionSettings from './TranscriptionSettings.vue'
import CallerIdSettings from './CallerIdSettings.vue'
import { activeTelephonyStep } from '@/composables/settings'
import { ref, watch } from 'vue'

const step = ref(activeTelephonyStep.value || 'telephony-settings')
activeTelephonyStep.value = ''

// a notification about a new number opens Twilio's step, the page open or not
watch(activeTelephonyStep, (passo) => {
  if (!passo) return
  step.value = passo
  activeTelephonyStep.value = ''
})

function updateStep(newStep) {
  step.value = newStep
}
</script>
