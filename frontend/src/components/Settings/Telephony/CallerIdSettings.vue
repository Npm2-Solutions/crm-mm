<!--
  Copyright (c) 2026, NPM2 Solutions Srl and contributors
  For license information, please see license.txt

  Every number the account can present, what kind it is, whether a call to it
  reaches DottorCloud; a number of the space released from here, one of another
  operator's verified to be shown on calls, or removed from Twilio (doc 52).
-->
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
            'Every number this account can present, what kind of number it is, and whether a call to it actually reaches {brand}.',
          )
        }}
      </p>
    </template>

    <template #header-actions>
      <div class="flex gap-2">
        <Button
          :label="__('Refresh')"
          icon-left="lucide-refresh-cw"
          :loading="syncing"
          @click="refresh"
        />
        <Button
          variant="solid"
          :label="__('Verify a number')"
          @click="openVerify()"
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
                '{0} of {1} numbers do not reach {brand}. The answering service can only answer on the ones that do.',
                [unreachable.length, delConto.length],
              )
            }}
          </p>
        </div>

        <div
          class="divide-y divide-outline-elevation-2 rounded-lg border border-outline-gray-2"
        >
          <div v-for="row in callerIds.data" :key="row.name" class="px-4 py-3">
            <div
              class="flex items-start justify-between gap-4 max-md:flex-col max-md:gap-2"
            >
              <div class="min-w-0 max-md:w-full">
                <div class="flex flex-wrap items-center gap-2">
                  <span
                    class="text-base-medium text-ink-gray-8"
                    :class="
                      !row.enabled &&
                      !daVerificare(row) &&
                      'line-through text-ink-gray-5'
                    "
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
                    v-if="verifica(row)"
                    :label="__(verifica(row).label, null, 'Caller ID')"
                    variant="subtle"
                    :theme="verifica(row).theme"
                  />
                  <Badge
                    v-if="!row.enabled && !verifica(row)"
                    :label="__('Off')"
                    variant="subtle"
                    theme="gray"
                  />
                </div>
                <FormControl
                  :modelValue="row.label"
                  class="mt-1.5 w-72 max-md:w-full"
                  size="sm"
                  :placeholder="__('Whose number is this?')"
                  @change="(e) => saveLabel(row, e.target.value)"
                />
              </div>

              <div class="flex shrink-0 flex-wrap items-center gap-2">
                <Badge
                  v-if="row.source === VERIFICATO"
                  :label="__('Calls out only')"
                  variant="subtle"
                  theme="gray"
                />
                <Badge
                  v-else
                  :label="
                    row.routes_to_crm
                      ? __('Reaches {brand}')
                      : __('Does not reach {brand}')
                  "
                  variant="subtle"
                  :theme="row.routes_to_crm ? 'green' : 'red'"
                />
                <Button
                  v-if="daVerificare(row)"
                  :label="__('Verify again')"
                  size="sm"
                  @click="openVerify(row)"
                />
                <Button
                  v-else
                  :label="row.enabled ? __('Disable') : __('Enable')"
                  size="sm"
                  @click="toggle(row)"
                />
                <Button
                  v-if="
                    row.enabled &&
                    row.provider === 'twilio' &&
                    row.source === 'Account Number'
                  "
                  :label="__('Release')"
                  size="sm"
                  theme="red"
                  variant="subtle"
                  @click="chiediDiRilasciare(row)"
                />
                <Button
                  v-if="
                    row.provider === 'twilio' &&
                    row.source === 'Verified Caller ID' &&
                    row.verification_status === 'Verified'
                  "
                  :label="__('Remove')"
                  size="sm"
                  theme="red"
                  variant="subtle"
                  @click="chiediDiTogliere(row)"
                />
              </div>
            </div>

            <p v-if="row.routing_note" class="mt-1.5 text-p-sm text-ink-gray-5">
              {{ row.routing_note }}
            </p>
            <p
              v-if="incertoInItalia(row)"
              class="mt-1 text-p-sm text-ink-amber-8"
            >
              {{
                __(
                  'In Italy it is shown as far as the operators let it (AGCOM, August 2025): to be sure, move the number to Twilio.',
                )
              }}
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

  <!-- a number of another operator's, verified to be shown on calls -->
  <VerifyNumberDialog
    v-model="showVerify"
    :numero-iniziale="daRiverificare.phone_number"
    :nome-iniziale="daRiverificare.label"
    @changed="callerIds.reload()"
  />
</template>

<script setup>
import SettingsLayoutBase from '@/components/Layouts/SettingsLayoutBase.vue'
import VerifyNumberDialog from '@/components/Settings/Telephony/VerifyNumberDialog.vue'
import { globalStore } from '@/stores/global'
import {
  NON_VERIFICATO,
  IN_ATTESA,
  numeroItaliano,
  statoDellaVerifica,
} from '@/utils/verificati'
import {
  Badge,
  ErrorMessage,
  FormControl,
  LoadingIndicator,
  call,
  createResource,
  toast,
} from 'frappe-ui'
import { computed, reactive, ref } from 'vue'

const emit = defineEmits(['updateStep'])
const { $dialog } = globalStore()

const syncing = ref(false)
const error = ref('')
const showVerify = ref(false)
const daRiverificare = reactive({ phone_number: '', label: '' })

const VERIFICATO = 'Verified Caller ID'

// a verified number's state; one of before the states, verified and on
function verifica(row) {
  if (row.source !== VERIFICATO) return null
  return statoDellaVerifica(
    row.verification_status || (row.enabled ? 'Verified' : ''),
  )
}

function daVerificare(row) {
  return (
    row.source === VERIFICATO &&
    [IN_ATTESA, NON_VERIFICATO].includes(row.verification_status)
  )
}

function incertoInItalia(row) {
  return (
    row.source === VERIFICATO &&
    row.enabled &&
    numeroItaliano(row.phone_number) === 'fisso'
  )
}

const callerIds = createResource({
  url: 'crm.telephony.caller_ids.get_caller_ids',
  params: { only_enabled: false },
  auto: true,
})

// a verified number is shown on calls, and its calls ring elsewhere: by design
const delConto = computed(() =>
  (callerIds.data || []).filter((row) => row.source !== VERIFICATO),
)
const unreachable = computed(() =>
  delConto.value.filter((row) => !row.routes_to_crm),
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

// a number of the space, given back to Twilio: it stops costing, for good
function chiediDiRilasciare(row) {
  $dialog({
    title: __('Release {0}?', [row.phone_number]),
    message: __(
      'The number goes back to Twilio: it stops costing, and whoever calls it hears it does not exist. It cannot be undone: Twilio may give it to somebody else.',
    ),
    actions: [
      {
        label: __('Release'),
        variant: 'solid',
        theme: 'red',
        onClick: (chiudi) => {
          chiudi()
          rilascia(row)
        },
      },
    ],
  })
}

async function rilascia(row) {
  try {
    await call('crm.telephony.numeri.release_number', {
      phone_number: row.phone_number,
    })
    toast.success(__('{0} is released', [row.phone_number]))
    callerIds.reload()
  } catch (e) {
    toast.error(e.messages?.[0] || __('Could not release the number'))
  }
}

function openVerify(row = null) {
  daRiverificare.phone_number = row?.phone_number || ''
  daRiverificare.label = row?.label || ''
  showVerify.value = true
}

// a verified number out of Twilio: not shown on calls any more
function chiediDiTogliere(row) {
  $dialog({
    title: __('Remove {0} from Twilio?', [row.phone_number]),
    message: __(
      'It is not shown on calls any more. Calls to it keep ringing where they ring now; to show it again, verify it again.',
    ),
    actions: [
      {
        label: __('Remove'),
        variant: 'solid',
        theme: 'red',
        onClick: (chiudi) => {
          chiudi()
          togli(row)
        },
      },
    ],
  })
}

async function togli(row) {
  try {
    const esito = await call('crm.telephony.verificati.remove_verified', {
      phone_number: row.phone_number,
    })
    toast.success(__('{0} is removed from Twilio', [row.phone_number]))
    if (esito.lines) {
      toast.warning(
        __(
          '{0} people had it as their own line: give them another in the phone’s settings.',
          [esito.lines],
        ),
      )
    }
    callerIds.reload()
  } catch (e) {
    toast.error(e.messages?.[0] || __('Could not remove the number'))
  }
}
</script>
