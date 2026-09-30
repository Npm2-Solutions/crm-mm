<!--
  Giving a report to the patient: by hand, or online for 45 days.

  Online only with the patient's consent to online reports, and never for a
  document marked "never online". The email carries a link and no content; the
  code that opens it is shown here once, to give the patient another way -
  printed or read out - so a wrong address alone opens nothing.
-->
<template>
  <Dialog
    v-model="show"
    :options="{ title: __('Give it to the patient'), size: 'lg' }"
  >
    <template #body-content>
      <div
        v-if="given"
        class="flex flex-col items-center gap-3 py-2 text-center"
      >
        <span class="text-p-sm text-ink-gray-6">
          {{ __('The code to open it: give it to the patient now') }}
        </span>
        <span
          class="font-mono text-3xl font-semibold tracking-[0.3em] text-ink-gray-9 tabular-nums"
        >
          {{ given.code }}
        </span>
        <span class="text-p-sm text-ink-gray-6">
          {{
            given.email
              ? __('The link went to {0}. Online until {1}.', [
                  given.email,
                  formatDate(given.expires_on, 'D MMM YYYY'),
                ])
              : __('Online until {0}.', [
                  formatDate(given.expires_on, 'D MMM YYYY'),
                ])
          }}
        </span>
        <FormControl
          :model-value="given.link"
          class="w-full"
          readonly
          :label="__('The link')"
        />
        <p class="text-p-xs text-ink-gray-5">
          {{
            __(
              'The code is not in the email and is not shown again: if it is lost, withdraw it and give a new one.',
            )
          }}
        </p>
      </div>
      <div v-else-if="info.data" class="flex flex-col gap-4">
        <TabButtons v-model="how" :buttons="modes" class="w-fit" />

        <template v-if="how === 'hand'">
          <p class="text-p-sm text-ink-gray-6">
            {{ __('Printed and handed over. Who took it?') }}
          </p>
          <FormControl
            v-model="deliveredTo"
            :label="__('Given to')"
            :placeholder="__('The patient, or who took it for them')"
          />
        </template>

        <template v-else>
          <div
            v-if="!info.data.online_consent"
            class="rounded-md bg-surface-gray-2 px-3 py-2 text-p-sm text-ink-gray-7"
          >
            {{
              __(
                'The patient has not asked for their reports online. Record their consent first, or give it by hand.',
              )
            }}
          </div>
          <div
            v-else-if="info.data.never_online"
            class="rounded-md bg-surface-gray-2 px-3 py-2 text-p-sm text-ink-gray-7"
          >
            {{ __('This document never goes online: give it by hand.') }}
          </div>
          <template v-else>
            <p class="text-p-sm text-ink-gray-6">
              {{
                __(
                  'Online for 45 days, opened with a code you give the patient here.',
                )
              }}
            </p>
            <label class="flex items-start gap-2">
              <Checkbox
                v-model="sendEmail"
                class="touch-target mt-0.5 shrink-0"
                :disabled="!info.data.email"
              />
              <span class="text-base text-ink-gray-8">
                {{
                  info.data.email
                    ? __('Email the link to {0}', [info.data.email])
                    : __('No email address: give the link with the code')
                }}
              </span>
            </label>
          </template>
        </template>

        <div v-if="info.data.deliveries.length" class="flex flex-col gap-1">
          <span class="text-sm font-medium text-ink-gray-5">
            {{ __('Already given') }}
          </span>
          <div
            v-for="delivery in info.data.deliveries"
            :key="delivery.name"
            class="flex flex-wrap items-center justify-between gap-2 text-p-sm"
          >
            <span class="min-w-0 text-ink-gray-7">{{
              describe(delivery)
            }}</span>
            <Button
              v-if="
                delivery.channel === 'Online' &&
                ['Available', 'Downloaded'].includes(delivery.status)
              "
              size="sm"
              variant="ghost"
              theme="red"
              class="touch-target shrink-0"
              :label="__('Withdraw')"
              @click="withdraw(delivery)"
            />
          </div>
        </div>
        <ErrorMessage :message="error" />
      </div>
    </template>
    <template #actions>
      <div class="dialog-footer flex justify-end gap-2">
        <Button
          :label="given ? __('Done') : __('Cancel')"
          @click="show = false"
        />
        <Button
          v-if="!given && how === 'hand'"
          variant="solid"
          :label="__('Given by hand')"
          :loading="busy"
          @click="byHand"
        />
        <Button
          v-else-if="!given"
          variant="solid"
          :label="__('Put it online')"
          :disabled="!info.data?.online_consent || info.data?.never_online"
          :loading="busy"
          @click="online"
        />
      </div>
    </template>
  </Dialog>
</template>

<script setup>
import { formatDate } from '@/utils'
import {
  Button,
  Checkbox,
  Dialog,
  ErrorMessage,
  FormControl,
  TabButtons,
  call,
  createResource,
} from 'frappe-ui'
import { ref, watch } from 'vue'

const props = defineProps({ document: { type: Object, default: null } })
const emit = defineEmits(['given'])
const show = defineModel({ type: Boolean })

const modes = [
  { label: __('By hand'), value: 'hand' },
  { label: __('Online'), value: 'online' },
]
const how = ref('hand')
const deliveredTo = ref('')
const sendEmail = ref(true)
const busy = ref(false)
const error = ref('')
const given = ref(null)

const info = createResource({
  url: 'crm.clinica.consegna.get_deliveries',
  makeParams: () => ({ document: props.document?.name }),
})

watch(show, (open) => {
  if (!open) return
  how.value = 'hand'
  deliveredTo.value = ''
  sendEmail.value = true
  error.value = ''
  given.value = null
  info.reload()
})

function describe(delivery) {
  const when = formatDate(delivery.given_on, 'D MMM YYYY')
  if (delivery.channel === 'By hand') {
    return __('By hand to {0}, {1}', [delivery.delivered_to, when])
  }
  const until = formatDate(delivery.expires_on, 'D MMM YYYY')
  const state = {
    Available: __('online until {0}', [until]),
    Downloaded: __('downloaded {0} times, online until {1}', [
      delivery.downloads,
      until,
    ]),
    Withdrawn: __('withdrawn'),
    Expired: __('expired'),
  }[delivery.status]
  return __('Online, {0}: {1}', [when, state || delivery.status])
}

async function run(method, args) {
  busy.value = true
  error.value = ''
  try {
    return await call(`crm.clinica.consegna.${method}`, args)
  } catch (e) {
    error.value = e.messages?.join(' ') || e.message
  } finally {
    busy.value = false
  }
}

async function byHand() {
  const done = await run('deliver_by_hand', {
    document: props.document.name,
    delivered_to: deliveredTo.value,
  })
  if (done) {
    emit('given')
    show.value = false
  }
}

async function online() {
  const done = await run('deliver_online', {
    document: props.document.name,
    send_email: sendEmail.value && info.data?.email ? 1 : 0,
  })
  if (done) {
    given.value = done
    emit('given')
  }
}

async function withdraw(delivery) {
  const done = await run('withdraw', { delivery: delivery.name })
  if (done) info.reload()
}
</script>
