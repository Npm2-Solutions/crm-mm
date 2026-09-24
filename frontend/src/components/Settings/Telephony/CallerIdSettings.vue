<template>
  <SettingsLayoutBase>
    <template #title>
      <div class="flex items-center gap-1">
        <Button
          variant="ghost"
          icon-left="lucide-chevron-left"
          :label="__('Caller IDs')"
          size="md"
          class="cursor-pointer -ml-4 hover:bg-transparent focus:bg-transparent focus:outline-none focus:ring-0 active:bg-transparent active:text-ink-gray-5 text-2xl-semibold hover:opacity-70 !pr-0 !max-w-96 !justify-start"
          @click="emit('updateStep', 'telephony-settings')"
        />
      </div>
    </template>

    <template #description>
      <p class="text-p-base text-ink-gray-6">
        {{
          __(
            'Every number this account can present, what kind of number it is, and whether a call to it actually reaches the CRM.',
          )
        }}
      </p>
    </template>

    <template #header-actions>
      <div class="flex gap-2">
        <Button :label="__('Verify a number')" @click="openVerify" />
        <Button
          variant="solid"
          :label="__('Refresh')"
          icon-left="lucide-refresh-cw"
          :loading="syncing"
          @click="refresh"
        />
      </div>
    </template>

    <template #content>
      <div v-if="callerIds.loading" class="flex justify-center py-16">
        <LoadingIndicator class="size-5" />
      </div>

      <div
        v-else-if="!callerIds.data?.length"
        class="rounded-lg border border-dashed border-outline-gray-2 px-4 py-12 text-center"
      >
        <p class="text-p-base text-ink-gray-6">
          {{ __('No caller IDs yet.') }}
        </p>
        <Button
          class="mt-3"
          variant="solid"
          :label="__('Read them from Twilio')"
          :loading="syncing"
          @click="refresh"
        />
      </div>

      <template v-else>
        <div
          v-if="unreachable.length"
          class="mb-4 rounded-md bg-surface-gray-2 px-3 py-2"
        >
          <p class="text-p-sm text-ink-gray-7">
            {{
              __(
                '{0} of {1} numbers do not reach the CRM. The answering service can only answer on the ones that do.',
                [unreachable.length, callerIds.data.length],
              )
            }}
          </p>
        </div>

        <div
          class="divide-y divide-outline-gray-1 rounded-lg border border-outline-gray-2"
        >
          <div v-for="row in callerIds.data" :key="row.name" class="px-4 py-3">
            <div class="flex items-start justify-between gap-4">
              <div class="min-w-0">
                <div class="flex items-center gap-2">
                  <span
                    class="text-base-medium text-ink-gray-8"
                    :class="!row.enabled && 'line-through text-ink-gray-5'"
                  >
                    {{ row.phone_number }}
                  </span>
                  <Badge
                    v-if="row.number_type"
                    :label="__(row.number_type)"
                    variant="subtle"
                    :theme="row.number_type === 'Mobile' ? 'orange' : 'gray'"
                  />
                  <Badge
                    v-if="row.source === 'Verified Caller ID'"
                    :label="__('Verified')"
                    variant="subtle"
                    theme="blue"
                  />
                  <Badge
                    v-if="!row.enabled"
                    :label="__('Off')"
                    variant="subtle"
                    theme="gray"
                  />
                </div>
                <FormControl
                  :modelValue="row.label"
                  class="mt-1.5 w-72"
                  size="sm"
                  :placeholder="__('Whose number is this?')"
                  @change="(e) => saveLabel(row, e.target.value)"
                />
              </div>

              <div
                class="flex flex-wrap items-center gap-2 sm:shrink-0 sm:flex-nowrap"
              >
                <Badge
                  :label="
                    row.routes_to_crm
                      ? __('Reaches the CRM')
                      : __('Does not reach the CRM')
                  "
                  variant="subtle"
                  :theme="row.routes_to_crm ? 'green' : 'red'"
                />
                <Button
                  :label="row.enabled ? __('Disable') : __('Enable')"
                  size="sm"
                  @click="toggle(row)"
                />
              </div>
            </div>

            <p v-if="row.routing_note" class="mt-1.5 text-p-sm text-ink-gray-5">
              {{ row.routing_note }}
            </p>
            <p v-if="row.sip_trunk" class="mt-1 text-p-sm text-ink-gray-5">
              {{ __('SIP trunk') }}: {{ row.sip_trunk }}
            </p>
          </div>
        </div>
      </template>

      <ErrorMessage class="mt-4" :message="error" />
    </template>
  </SettingsLayoutBase>

  <!-- verify a number the practice owns elsewhere -->
  <Dialog v-model="showVerify" :options="{ title: __('Verify a caller ID') }">
    <template #body-content>
      <div class="flex flex-col gap-4">
        <p class="text-p-sm text-ink-gray-6">
          {{
            __(
              'Twilio rings the number and gives you a code. Answer it and type the code to prove you control the line — that is what separates a caller ID you may present from spoofing.',
            )
          }}
        </p>
        <FormControl
          v-model="verifyForm.phone_number"
          :label="__('Number')"
          placeholder="+39..."
        />
        <FormControl
          v-model="verifyForm.label"
          :label="__('Label')"
          :placeholder="__('Studio Rossi — reception')"
        />

        <div
          v-if="verification"
          class="rounded-md bg-surface-gray-2 px-3 py-3 text-center"
        >
          <div class="text-p-sm text-ink-gray-6">
            {{ __('Answer the call and type this code:') }}
          </div>
          <div class="mt-1 text-2xl-semibold tracking-widest text-ink-gray-9">
            {{ verification.validation_code }}
          </div>
        </div>

        <ErrorMessage :message="verifyError" />
      </div>
    </template>
    <template #actions>
      <div class="flex justify-end gap-2">
        <Button :label="__('Close')" @click="showVerify = false" />
        <Button
          v-if="!verification"
          variant="solid"
          :label="__('Call me')"
          :loading="verifying"
          @click="startVerification"
        />
      </div>
    </template>
  </Dialog>
</template>

<script setup>
import SettingsLayoutBase from '@/components/Layouts/SettingsLayoutBase.vue'
import {
  Badge,
  Dialog,
  ErrorMessage,
  FormControl,
  LoadingIndicator,
  call,
  createResource,
  toast,
} from 'frappe-ui'
import { computed, reactive, ref } from 'vue'

const emit = defineEmits(['updateStep'])

const syncing = ref(false)
const error = ref('')
const showVerify = ref(false)
const verifying = ref(false)
const verifyError = ref('')
const verification = ref(null)
const verifyForm = reactive({ phone_number: '', label: '' })

const callerIds = createResource({
  url: 'crm.telephony.caller_ids.get_caller_ids',
  params: { only_enabled: false },
  auto: true,
})

const unreachable = computed(() =>
  (callerIds.data || []).filter((row) => !row.routes_to_crm),
)

async function refresh() {
  syncing.value = true
  error.value = ''
  try {
    const result = await call('crm.telephony.caller_ids.sync_caller_ids', {
      provider: 'twilio',
    })
    callerIds.reload()
    toast.success(
      __('{0} numbers read, {1} no longer on the account', [
        result.total,
        result.retired,
      ]),
    )
  } catch (e) {
    error.value = e.messages?.[0] || __('Could not read the numbers')
  } finally {
    syncing.value = false
  }
}

async function saveLabel(row, label) {
  if (label === row.label) return
  try {
    await call('crm.telephony.caller_ids.set_label', { name: row.name, label })
    row.label = label
  } catch (e) {
    toast.error(e.messages?.[0] || __('Could not save the label'))
  }
}

async function toggle(row) {
  try {
    const result = await call('crm.telephony.caller_ids.set_enabled', {
      name: row.name,
      enabled: !row.enabled,
    })
    row.enabled = result.enabled ? 1 : 0
  } catch (e) {
    toast.error(e.messages?.[0] || __('Could not change the number'))
  }
}

function openVerify() {
  verification.value = null
  verifyError.value = ''
  verifyForm.phone_number = ''
  verifyForm.label = ''
  showVerify.value = true
}

async function startVerification() {
  verifying.value = true
  verifyError.value = ''
  try {
    verification.value = await call('crm.telephony.caller_ids.verify_number', {
      phone_number: verifyForm.phone_number,
      label: verifyForm.label || null,
    })
  } catch (e) {
    verifyError.value =
      e.messages?.[0] || __('Could not start the verification')
  } finally {
    verifying.value = false
  }
}
</script>
