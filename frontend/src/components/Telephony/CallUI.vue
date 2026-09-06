<template>
  <TwilioCallUI ref="twilio" />
  <ExotelCallUI ref="exotel" />
  <Dialog
    v-model:open="show"
    :title="__('Make Call')"
    :actions="[
      {
        label: __('Call using {0}', [callMedium]),
        variant: 'solid',
        onClick: makeCallUsing,
      },
    ]"
  >
    <template #default>
      <div class="flex flex-col gap-4">
        <FormControl
          v-model="mobileNumber"
          type="text"
          :label="__('Mobile Number')"
        />
        <FormControl
          v-model="callMedium"
          type="select"
          :label="__('Calling Medium')"
          :options="mediumOptions"
        />
        <div class="flex flex-col gap-1">
          <FormControl
            v-model="isDefaultMedium"
            type="checkbox"
            :label="__('Make {0} as default calling medium', [callMedium])"
          />

          <div v-if="isDefaultMedium" class="text-sm text-ink-gray-4">
            {{
              __('You can change the default calling medium from the settings')
            }}
          </div>
        </div>
      </div>
    </template>
  </Dialog>
</template>
<script setup>
import TwilioCallUI from '@/components/Telephony/TwilioCallUI.vue'
import ExotelCallUI from '@/components/Telephony/ExotelCallUI.vue'
import {
  defaultCallingMedium,
  providers,
  useTelephony,
} from '@/composables/telephony'
import { globalStore } from '@/stores/global'
import { FormControl, call, toast } from 'frappe-ui'
import { computed, nextTick, ref, watch } from 'vue'

const { setMakeCall } = globalStore()
const { isEnabled, isAnyEnabled } = useTelephony()

const twilio = ref(null)
const exotel = ref(null)

const callMedium = ref('')
const isDefaultMedium = ref(false)

const show = ref(false)
const mobileNumber = ref('')

// which carriers exist comes from the backend registry; only the in-browser
// calling component stays mapped by name here, because each SDK is genuinely
// its own thing and there is nothing to share between them
const uiComponents = { twilio, exotel }

const enabledIntegrations = computed(() =>
  providers.value
    .filter((p) => isEnabled(p.name) && uiComponents[p.name])
    .map((p) => ({ key: p.name, label: p.label, ref: uiComponents[p.name] })),
)

const mediumOptions = computed(() =>
  enabledIntegrations.value.map(({ label }) => label),
)

function makeCall(number) {
  if (enabledIntegrations.value.length > 1 && !defaultCallingMedium.value) {
    mobileNumber.value = number
    show.value = true
    return
  }

  callMedium.value = enabledIntegrations.value[0]?.label ?? ''
  if (defaultCallingMedium.value) {
    callMedium.value = defaultCallingMedium.value
  }

  mobileNumber.value = number
  makeCallUsing()
}

function makeCallUsing() {
  if (isDefaultMedium.value && callMedium.value) {
    setDefaultCallingMedium()
  }

  const chosen = enabledIntegrations.value.find(
    ({ label }) => label === callMedium.value,
  )
  chosen?.ref?.value?.makeOutgoingCall(mobileNumber.value)
  show.value = false
}

async function setDefaultCallingMedium() {
  await call('crm.integrations.api.set_default_calling_medium', {
    medium: callMedium.value,
  })

  defaultCallingMedium.value = callMedium.value
  toast.success(
    __('Default calling medium set successfully to {0}', [callMedium.value]),
  )
}

watch(
  isAnyEnabled,
  () =>
    nextTick(() => {
      for (const { ref: integrationRef } of enabledIntegrations.value) {
        integrationRef.value?.setup()
      }

      if (isAnyEnabled.value) {
        callMedium.value =
          defaultCallingMedium.value ||
          enabledIntegrations.value[0]?.label ||
          ''
        setMakeCall(makeCall)
      }
    }),
  { immediate: true },
)
</script>
