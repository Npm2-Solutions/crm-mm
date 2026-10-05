<!--
  Copyright (c) 2026, NPM2 Solutions Srl and contributors
  For license information, please see license.txt
-->
<template>
  <!-- What this person agreed to, on which words, when and how: the consent
       register, one line per kind. A consent is withdrawn here as easily as it
       was recorded (art. 7(3) GDPR). -->
  <div v-if="consents.data?.types?.length" class="flex flex-col">
    <div class="h-px w-full border-t" />
    <div class="p-1 sm:p-3">
      <CollapsibleSection
        labelClass="px-2 font-semibold"
        headerClass="h-8"
        :label="__('Consents')"
      >
        <div class="flex flex-col gap-1.5 pb-1">
          <div
            v-for="type in consents.data.types"
            :key="type.key"
            class="flex items-start gap-2 px-3 leading-5 first:mt-3"
          >
            <div
              class="line-clamp-2 w-[35%] min-w-20 shrink-0 break-words pt-1 text-sm text-ink-gray-5"
            >
              {{ __(type.label) }}
            </div>
            <!-- the state and its button on one line, when and how under both:
                 beside the button the date wrapped on three lines. The button
                 goes under the state where both do not fit: beside it «Nessuna
                 risposta» was «Nessuna ris…», in the panel's 352px -->
            <div class="flex min-w-0 flex-1 flex-col">
              <div
                class="flex min-h-7 flex-wrap items-center justify-between gap-x-2"
              >
                <div
                  class="flex min-w-0 items-center gap-1 px-2 text-base text-ink-gray-8"
                >
                  <IndicatorIcon class="-ml-1 shrink-0" :class="dot(type)" />
                  <span class="truncate">{{ stateLabel(type) }}</span>
                </div>
                <Button
                  v-if="action(type)"
                  size="sm"
                  variant="ghost"
                  class="touch-target ml-auto shrink-0"
                  :label="action(type).label"
                  @click="action(type).run()"
                />
              </div>
              <div
                v-if="type.current"
                class="px-2 text-p-xs text-ink-gray-5 [overflow-wrap:anywhere]"
              >
                {{ stateDetail(type.current) }}
              </div>
            </div>
          </div>
        </div>
      </CollapsibleSection>
    </div>
  </div>

  <Dialog v-model="dialog.show" :options="{ title: dialog.title, size: 'md' }">
    <template #body-content>
      <div v-if="dialog.type" class="flex flex-col gap-4">
        <!-- the words they agree to, exactly: the answer keeps its own copy -->
        <div
          v-if="dialog.mode === 'record'"
          class="max-h-48 overflow-y-auto whitespace-pre-line rounded-md bg-surface-gray-2 p-3 text-p-sm text-ink-gray-8"
        >
          {{ dialog.type.text }}
        </div>
        <FormControl
          v-model="dialog.channel"
          type="select"
          :label="
            dialog.mode === 'record'
              ? __('How did they answer?')
              : __('How did they withdraw it?')
          "
          :options="channelOptions"
        />
        <!-- a parent answers for a minor child: somebody linked to them, and
             the register says who -->
        <FormControl
          v-if="dialog.mode === 'record' && answeredByOptions.length > 1"
          v-model="dialog.givenBy"
          type="select"
          :label="__('Who answered?')"
          :options="answeredByOptions"
        />
        <FormControl
          v-model="dialog.note"
          type="textarea"
          :label="__('Note')"
          :placeholder="
            dialog.mode === 'record'
              ? __('Where the signed paper is, who took the call…')
              : __('What they said, and to whom')
          "
        />
        <ErrorMessage :message="dialog.error" />
      </div>
    </template>
    <template #actions>
      <div
        v-if="dialog.type"
        class="flex flex-wrap items-center justify-end gap-2"
      >
        <template v-if="dialog.mode === 'record'">
          <Button
            v-if="dialog.type.kind === 'Consent'"
            :label="__('They said no')"
            :loading="dialog.saving === 'Refused'"
            @click="record('Refused')"
          />
          <Button
            variant="solid"
            :label="
              dialog.type.kind === 'Consent'
                ? __('They agree')
                : __('They have read it')
            "
            :loading="dialog.saving === 'Given'"
            @click="record('Given')"
          />
        </template>
        <Button
          v-else
          variant="solid"
          theme="red"
          :label="__('Withdraw consent')"
          :loading="dialog.saving === 'Withdrawn'"
          @click="withdraw"
        />
      </div>
    </template>
  </Dialog>
</template>

<script setup>
import CollapsibleSection from '@/components/CollapsibleSection.vue'
import IndicatorIcon from '@/components/Icons/IndicatorIcon.vue'
import { usersStore } from '@/stores/users'
import { formatDate, parseColor } from '@/utils'
import {
  Dialog,
  ErrorMessage,
  FormControl,
  createResource,
  call,
  toast,
} from 'frappe-ui'
import { computed, reactive, watch } from 'vue'

const props = defineProps({
  lead: { type: String, required: true },
})

const { puo } = usersStore()

const consents = createResource({
  url: 'crm.moduli.consensi.get_consents',
  makeParams: () => ({ lead: props.lead }),
  onError: () => consents.setData(null),
})

watch(
  () => props.lead,
  (lead) => lead && puo('consensi.vedi') && consents.reload(),
  { immediate: true },
)

const CHANNEL_LABELS = {
  'Online booking': __('Online booking'),
  'Web form': __('Web form'),
  'At the desk': __('At the desk'),
  'On paper': __('On paper'),
  'By phone': __('By phone'),
  'By email': __('By email'),
  Imported: __('Imported'),
}

const answeredByOptions = computed(() => [
  { label: __('The person themselves'), value: '' },
  ...(consents.data?.answered_by || []).map((person) => ({
    label: person.represents
      ? __('{0}, who acts for them', [person.label])
      : person.label,
    value: person.name,
  })),
])

const channelOptions = computed(() =>
  (consents.data?.channels || []).map((value) => ({
    label: CHANNEL_LABELS[value] || value,
    value,
  })),
)

function stateLabel(type) {
  const status = type.current?.status
  if (!status) return __('No answer')
  if (status === 'Given') {
    return type.kind === 'Consent'
      ? __('Given')
      : __('Read', null, 'Notice acknowledged')
  }
  return status === 'Refused' ? __('Refused') : __('Withdrawn')
}

function stateDetail(current) {
  const channel = (c) => CHANNEL_LABELS[c] || c
  if (current.status === 'Withdrawn' && current.withdrawn_on) {
    return __('on {0}, {1}', [
      formatDate(current.withdrawn_on, 'D MMM YYYY'),
      channel(current.withdrawal_channel).toLowerCase(),
    ])
  }
  const when = __('on {0}, {1}', [
    formatDate(current.answered_on, 'D MMM YYYY'),
    channel(current.channel).toLowerCase(),
  ])
  return current.given_by_name
    ? __('{0}, by {1}', [when, current.given_by_name])
    : when
}

function dot(type) {
  const status = type.current?.status
  if (status === 'Given') return parseColor('green')
  if (status === 'Withdrawn') return parseColor('red')
  if (status === 'Refused') return parseColor('orange')
  return 'text-ink-gray-5'
}

function action(type) {
  if (!consents.data?.can_record) return null
  if (type.can_withdraw) {
    return {
      label: __('Withdraw', null, 'Consent'),
      run: () => open(type, 'withdraw'),
    }
  }
  // read once is read: a privacy notice is not answered twice
  if (type.kind !== 'Consent' && type.current?.status === 'Given') return null
  return {
    label: __('Record', null, 'Consent'),
    run: () => open(type, 'record'),
  }
}

const dialog = reactive({
  show: false,
  mode: 'record',
  type: null,
  title: '',
  channel: 'At the desk',
  givenBy: '',
  note: '',
  error: '',
  saving: '',
})

function open(type, mode) {
  Object.assign(dialog, {
    show: true,
    mode,
    type,
    title:
      mode === 'record'
        ? __('Record an answer: {0}', [__(type.label)])
        : __('Withdraw: {0}', [__(type.label)]),
    channel: 'At the desk',
    givenBy: '',
    note: '',
    error: '',
    saving: '',
  })
}

async function send(method, extra, saving) {
  dialog.saving = saving
  dialog.error = ''
  try {
    const data = await call(`crm.moduli.consensi.${method}`, {
      lead: props.lead,
      consent_type: dialog.type.key,
      channel: dialog.channel,
      note: dialog.note || null,
      ...extra,
    })
    consents.setData(data)
    dialog.show = false
    toast.success(__('Recorded in the consent register'))
  } catch (err) {
    dialog.error = err.messages?.[0] || err.message
  } finally {
    dialog.saving = ''
  }
}

function record(status) {
  send('record_consent', { status, given_by: dialog.givenBy || null }, status)
}

function withdraw() {
  send('withdraw_consent', {}, 'Withdrawn')
}
</script>
