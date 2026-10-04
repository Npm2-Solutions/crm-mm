<!--
  Copyright (c) 2026, NPM2 Solutions Srl and contributors
  For license information, please see license.txt

  A form filled with a person, and signed on the screen.

  While it is a draft the answers can be saved and finished later; signing sends
  everything at once, and the server checks it with the same rules this page
  shows (`crm/moduli/schema.py`). Signed, the page is the record: the answers as
  they were, the signatures, the warnings for the operator, the PDF and its
  evidence.
-->
<template>
  <LayoutHeader>
    <template #left-header>
      <Breadcrumbs :items="crumbs" />
    </template>
    <template #right-header>
      <div class="flex items-center gap-2">
        <Badge
          v-if="data"
          :label="
            signed
              ? isSheet
                ? __('Completed')
                : fromTheSite
                  ? __('Sent')
                  : __('Signed')
              : __('To finish')
          "
          :theme="signed ? 'green' : 'orange'"
          variant="subtle"
        />
        <Button
          v-if="data?.pdf_file"
          icon-left="lucide-file-text"
          :label="__('PDF')"
          :link="data.pdf_file"
        />
      </div>
    </template>
  </LayoutHeader>

  <!-- what comes into view - a field touched with the keyboard up, the first
       one missing - stays above the bar of actions at the bottom: on a phone
       its three rows covered the signature -->
  <div class="flex-1 overflow-y-auto scroll-pb-24 max-md:scroll-pb-44">
    <div v-if="!data" class="flex justify-center py-16">
      <LoadingIndicator class="w-5" />
    </div>
    <div
      v-else
      class="mx-auto flex max-w-2xl flex-col gap-6 px-5 py-6 max-md:px-4"
    >
      <div class="flex flex-col gap-1">
        <h1 class="text-2xl font-semibold text-ink-gray-9">{{ data.title }}</h1>
        <p class="text-p-base text-ink-gray-6">
          {{ data.lead_name }} · {{ __('version {0}', [data.version]) }}
          <template v-if="data.channel === 'Link'">
            · {{ __('from a link') }}</template
          >
          <template v-else-if="data.channel === 'Tablet'">
            · {{ __('on the tablet') }}</template
          >
          <template v-else-if="fromTheSite">
            · {{ __('from the website') }}</template
          >
          <template v-if="signed">
            ·
            {{
              __(fromTheSite ? 'sent {0}' : 'signed {0}', [
                formatDate(data.signed_on, 'D MMM YYYY, HH:mm'),
              ])
            }}
          </template>
        </p>
      </div>

      <div
        v-if="stops.length"
        class="flex flex-col gap-1 rounded-lg bg-surface-red-1 px-4 py-3 text-sm text-ink-red-7"
        role="alert"
      >
        <div class="flex items-center gap-2 font-medium">
          <LucideTriangleAlert class="size-4 shrink-0" />
          {{ __('Warnings for the operator') }}
        </div>
        <span v-for="stop in stops" :key="stop.field">
          {{ labelOf(stop.field) }}:
          {{ stop.message || __('Stop here and tell the operator') }}
        </span>
      </div>

      <div
        v-if="atProvider"
        class="flex flex-col gap-2 rounded-lg bg-surface-blue-1 px-4 py-3 text-sm"
        role="status"
      >
        <span class="font-medium text-ink-blue-7">
          {{ __('With {0} for the signatures', [data.provider_name]) }}
        </span>
        <span class="text-ink-gray-7">
          {{
            __(
              'The answers do not change while it is there. Signed, it closes here by itself.',
            )
          }}
        </span>
        <div class="flex flex-wrap gap-2">
          <Button
            v-for="link in providerLinks"
            :key="link.field"
            size="sm"
            icon-left="external-link"
            :label="
              __('Signing page: {0}', [link.label || labelOf(link.field)])
            "
            :link="link.url"
          />
          <Button
            size="sm"
            variant="ghost"
            :label="__('Take it back')"
            @click="takeBack"
          />
        </div>
      </div>
      <div
        v-else-if="
          !signed && ['Declined', 'Expired'].includes(data.provider_status)
        "
        class="rounded-lg bg-surface-red-1 px-4 py-3 text-sm text-ink-red-7"
        role="alert"
      >
        {{
          data.provider_status === 'Declined'
            ? __('Declined at {0}: send it again, or sign it on paper', [
                data.provider_name,
              ])
            : __('Expired at {0}: send it again, or sign it on paper', [
                data.provider_name,
              ])
        }}
      </div>

      <div
        v-if="!signed && !atProvider && !isSheet"
        class="flex flex-col gap-1.5"
      >
        <span class="text-sm text-ink-gray-5">
          {{ __('Answered by a parent or guardian') }}
        </span>
        <div class="flex max-w-md items-center gap-2">
          <Link
            class="min-w-0 flex-1"
            doctype="CRM Lead"
            :value="givenBy"
            :placeholder="__('The person themselves')"
            @change="(value) => (givenBy = value || null)"
          />
          <Button
            v-if="givenBy"
            class="touch-target shrink-0"
            variant="ghost"
            icon="x"
            :label="__('The person themselves')"
            @click="givenBy = null"
          />
        </div>
      </div>

      <FormRenderer
        v-model="values"
        :schema="data.schema"
        :readonly="signed || atProvider"
        :show-missing="tried"
      />

      <div
        v-if="!signed && data.can_sign && !atProvider"
        class="dialog-footer sticky bottom-0 flex items-center justify-between gap-2 border-t border-outline-gray-2 bg-surface-base py-3 max-md:flex-wrap"
      >
        <Button
          v-if="!isMobileView"
          variant="ghost"
          theme="red"
          :label="__('Discard')"
          @click="discard"
        />
        <div class="flex gap-2 max-md:w-full max-md:justify-end">
          <!-- on a phone the rest is under one button: three rows of actions
               took a third of the screen, the form squeezed between -->
          <Dropdown v-if="isMobileView" :options="sulTelefono" placement="left">
            <Button
              class="shrink-0"
              icon="more-horizontal"
              :aria-label="__('More')"
            />
          </Dropdown>
          <Button
            :label="__('Save for later')"
            :loading="saving"
            @click="save"
          />
          <Dropdown
            v-if="otherWays.length && !isMobileView"
            :options="otherWays"
            placement="right"
          >
            <Button
              :label="__('Other ways to sign')"
              icon-right="chevron-down"
            />
          </Dropdown>
          <Button
            v-if="primary === 'drawn'"
            variant="solid"
            :label="
              isSheet && !signatureFields.length
                ? __('Finish the sheet')
                : __('Sign and finish')
            "
            :loading="signing"
            @click="sign"
          />
          <Button
            v-else-if="primary === 'provider'"
            variant="solid"
            :label="__('Sign with {0}', [data.provider.name])"
            :loading="signing"
            @click="sendToProvider"
          />
          <Button
            v-else
            variant="solid"
            :label="__('Sign on paper')"
            @click="showPaper = true"
          />
        </div>
      </div>

      <!-- signed: what proves it -->
      <section
        v-if="signed"
        class="flex flex-col gap-3 rounded-lg border border-outline-gray-2 px-4 py-4"
      >
        <h2 class="text-base font-semibold text-ink-gray-8">
          {{ __('Evidence') }}
        </h2>
        <dl
          class="grid grid-cols-[10rem_1fr] gap-x-4 gap-y-2 text-sm max-md:grid-cols-1"
        >
          <dt class="text-ink-gray-5">
            {{
              fromTheSite
                ? __('Who sent it, known by')
                : __('Who signed, known by')
            }}
          </dt>
          <dd class="text-ink-gray-7">{{ data.recognised }}</dd>
          <dt class="text-ink-gray-5">{{ __('What it asked (SHA-256)') }}</dt>
          <dd class="break-all font-mono text-xs text-ink-gray-7">
            {{ data.schema_hash }}
          </dd>
          <dt class="text-ink-gray-5">{{ __('The answers (SHA-256)') }}</dt>
          <dd class="break-all font-mono text-xs text-ink-gray-7">
            {{ data.answers_hash }}
          </dd>
          <template v-if="data.paper">
            <dt class="text-ink-gray-5">{{ __('Attested by') }}</dt>
            <dd class="text-ink-gray-7">
              {{ data.paper.attested_by }} ·
              {{ formatDate(data.paper.attested_on, 'D MMM YYYY, HH:mm') }}
            </dd>
            <dt class="text-ink-gray-5">{{ __('The scan (SHA-256)') }}</dt>
            <dd class="break-all font-mono text-xs text-ink-gray-7">
              {{ data.paper.sha256 }}
              <a
                class="block font-sans text-ink-gray-5 underline"
                :href="data.paper.file"
                target="_blank"
                >{{ __('Open the scan') }}</a
              >
            </dd>
          </template>
          <template v-if="data.pdf_hash">
            <dt class="text-ink-gray-5">{{ __('The PDF (SHA-256)') }}</dt>
            <dd class="break-all font-mono text-xs text-ink-gray-7">
              {{ data.pdf_hash }}
              <span class="block font-sans text-ink-gray-5">{{
                data.pdf_conformance
              }}</span>
            </dd>
          </template>
        </dl>
        <div class="flex flex-col gap-1.5">
          <span class="text-sm text-ink-gray-5">{{ __('What happened') }}</span>
          <div
            v-for="event in data.events"
            :key="event.name"
            class="flex flex-wrap gap-x-2 text-sm text-ink-gray-7"
          >
            <span class="text-ink-gray-5">
              {{ formatDate(event.occurred_on, 'D MMM YYYY, HH:mm:ss') }}
            </span>
            <span>{{ eventLabel(event.event) }}</span>
            <span v-if="event.detail" class="text-ink-gray-5"
              >· {{ event.detail }}</span
            >
          </div>
        </div>
      </section>
    </div>
  </div>

  <PaperSignDialog
    v-if="showPaper"
    v-model="showPaper"
    :form-id="formId"
    :answers="answersOnly()"
    :given-by="givenBy"
    @signed="signedOnPaper"
  />
</template>

<script setup>
import LayoutHeader from '@/components/LayoutHeader.vue'
import Link from '@/components/Controls/Link.vue'
import FormRenderer from '@/components/Moduli/FormRenderer.vue'
import PaperSignDialog from '@/components/Moduli/PaperSignDialog.vue'
import { evaluate, fieldsOf } from '@/utils/moduli'
import { formatDate } from '@/utils'
import { globalStore } from '@/stores/global'
import { isMobileView } from '@/composables/breakpoints'
import LucideTriangleAlert from '~icons/lucide/triangle-alert'
import {
  Badge,
  Breadcrumbs,
  Button,
  Dropdown,
  LoadingIndicator,
  call,
  toast,
  usePageMeta,
} from 'frappe-ui'
import { computed, ref, watch } from 'vue'
import { useRouter } from 'vue-router'

const props = defineProps({ formId: { type: String, required: true } })

const router = useRouter()
const { $dialog } = globalStore()

const data = ref(null)
const values = ref({})
const givenBy = ref(null)
const tried = ref(false)
const saving = ref(false)
const signing = ref(false)
const showPaper = ref(false)
const providerLinks = ref([])

const signed = computed(() => data.value?.docstatus === 1)
// the operator's sheet, written at the desk: completed, not signed by the person
const isSheet = computed(() => data.value?.use === 'Sheet')
// sent by anybody from the centre's website: nobody signed it
const fromTheSite = computed(() => data.value?.channel === 'Website')
const signatureFields = computed(() =>
  fieldsOf(data.value?.schema).filter((field) => field.type === 'signature'),
)

function apply(form) {
  data.value = form
  givenBy.value = form.given_by || null
  const shown = { ...(form.answers || {}) }
  // a signed form shows its strokes where they were drawn
  // on paper or at a provider there is no stroke: the page says how instead
  for (const signature of form.signatures || [])
    shown[signature.field] = signature.image || { method: signature.method }
  values.value = shown
}

async function load() {
  apply(await call('crm.moduli.compilazioni.get_form', { name: props.formId }))
}
load()

usePageMeta(() => ({ title: data.value?.title || __('Form') }))

const crumbs = computed(() => [
  data.value?.lead
    ? {
        label: data.value.lead_name || data.value.lead,
        route: {
          name: 'Lead',
          params: { leadId: data.value.lead },
          hash: '#forms',
        },
      }
    : { label: __('People'), route: { name: 'Leads' } },
  { label: data.value?.title || props.formId },
])

// signed, the warnings are the ones kept; a draft shows them as they come
const stops = computed(() =>
  signed.value
    ? data.value.alerts || []
    : evaluate(data.value?.schema, values.value).stops,
)

function labelOf(key) {
  return (
    fieldsOf(data.value?.schema).find((field) => field.id === key)?.label || key
  )
}

const atProvider = computed(() => data.value?.provider_status === 'Sent')

// a signature a finger cannot give (advanced, qualified) goes to the provider,
// or on paper when the centre has none
const needsProvider = computed(() => {
  if (!data.value) return false
  const state = evaluate(data.value.schema, values.value)
  return signatureFields.value.some(
    (field) =>
      state.visible[field.id] && (field.level || 'simple') !== 'simple',
  )
})
const primary = computed(() =>
  needsProvider.value ? (data.value?.provider ? 'provider' : 'paper') : 'drawn',
)
const otherWays = computed(() =>
  [
    primary.value !== 'paper' && {
      label: __('On paper'),
      icon: 'lucide-printer',
      onClick: () => (showPaper.value = true),
    },
    data.value?.provider &&
      primary.value !== 'provider' && {
        label: __('With {0}', [data.value.provider.name]),
        icon: 'lucide-shield-check',
        onClick: sendToProvider,
      },
  ].filter(Boolean),
)

// the phone's «⋯»: the other ways to sign, then throwing the form away
const sulTelefono = computed(() => [
  ...(otherWays.value.length
    ? [{ group: __('Other ways to sign'), items: otherWays.value }]
    : []),
  {
    group: '',
    hideLabel: true,
    items: [
      {
        label: __('Discard'),
        icon: 'lucide-trash-2',
        theme: 'red',
        onClick: discard,
      },
    ],
  },
])

watch(atProvider, async (waiting) => {
  providerLinks.value = waiting
    ? await call('crm.moduli.compilazioni.provider_links', {
        name: props.formId,
      })
    : []
})

const EVENTS = {
  printed: __('Printed to sign on paper'),
  attested: __('Scan attested as a true copy'),
  provider_sent: __('Sent to the signature provider'),
  provider_withdrawn: __('Taken back from the signature provider'),
  provider_declined: __('Declined at the signature provider'),
  provider_expired: __('Expired at the signature provider'),
  pdf_received: __('Signed PDF received'),
  sent: __('Link sent'),
  opened: __('Link opened'),
  code_sent: __('Code sent'),
  code_verified: __('Code checked'),
  created: __('Started', null, 'Form filled half-way'),
  answers_saved: __('Answers saved'),
  filled: __('Filled by the person'),
  signed: __('Signed'),
  sent_from_website: __('Sent from the website'),
  pdf_generated: __('PDF made'),
  pdf_failed: __('PDF not made'),
  sealed: __('Sealed by the centre'),
  seal_failed: __('Not sealed'),
  consent_recorded: __('Consent recorded'),
  copy_downloaded: __('Copy downloaded'),
  cancelled: __('Cancelled'),
}
const eventLabel = (event) => EVENTS[event] || event

function answersOnly() {
  const signatures = new Set(signatureFields.value.map((field) => field.id))
  return Object.fromEntries(
    Object.entries(values.value).filter(([key]) => !signatures.has(key)),
  )
}

async function save() {
  saving.value = true
  try {
    await call('crm.moduli.compilazioni.save_answers', {
      name: props.formId,
      answers: JSON.stringify(answersOnly()),
    })
    toast.success(__('Saved: it can be finished later'))
  } catch (error) {
    toast.error(error.messages?.[0] || error.message)
  } finally {
    saving.value = false
  }
}

async function sign() {
  tried.value = true
  const state = evaluate(data.value.schema, values.value)
  if (state.missing.length) {
    toast.error(
      __('Still to answer: {0}', [state.missing.map(labelOf).join(', ')]),
    )
    document
      .querySelector(`[data-field="${state.missing[0]}"]`)
      ?.scrollIntoView({ behavior: 'smooth', block: 'center' })
    return
  }
  const strokes = Object.fromEntries(
    signatureFields.value
      .map((field) => [field.id, values.value[field.id]])
      .filter(
        ([, value]) =>
          typeof value === 'string' && value.startsWith('data:image/png'),
      ),
  )
  signing.value = true
  try {
    const form = await call('crm.moduli.compilazioni.sign_form', {
      name: props.formId,
      answers: JSON.stringify(answersOnly()),
      signatures: JSON.stringify(strokes),
      given_by: givenBy.value || '',
    })
    apply(form)
    tried.value = false
    toast.success(isSheet.value ? __('Completed') : __('Signed'))
  } catch (error) {
    toast.error(error.messages?.join(' ') || error.message)
  } finally {
    signing.value = false
  }
}

function missingBesidesSignatures() {
  const signatures = new Set(signatureFields.value.map((field) => field.id))
  return evaluate(data.value.schema, values.value).missing.filter(
    (key) => !signatures.has(key),
  )
}

async function sendToProvider() {
  tried.value = true
  const missing = missingBesidesSignatures()
  if (missing.length) {
    toast.error(__('Still to answer: {0}', [missing.map(labelOf).join(', ')]))
    return
  }
  signing.value = true
  try {
    const form = await call('crm.moduli.compilazioni.send_to_provider', {
      name: props.formId,
      answers: JSON.stringify(answersOnly()),
      given_by: givenBy.value || '',
    })
    apply(form)
    tried.value = false
    toast.success(__('Sent to {0}', [form.provider_name]))
  } catch (error) {
    toast.error(error.messages?.join(' ') || error.message)
  } finally {
    signing.value = false
  }
}

async function takeBack() {
  try {
    apply(
      await call('crm.moduli.compilazioni.take_back_from_provider', {
        name: props.formId,
      }),
    )
  } catch (error) {
    toast.error(error.messages?.[0] || error.message)
  }
}

function signedOnPaper(form) {
  apply(form)
  tried.value = false
  toast.success(__('Signed on paper'))
}

function discard() {
  $dialog({
    title: __('Discard this form?'),
    message: __('Its answers go. Nothing was signed on it.'),
    variant: 'danger',
    actions: [
      {
        label: __('Discard'),
        variant: 'solid',
        theme: 'red',
        onClick: async (close) => {
          await call('crm.moduli.compilazioni.discard_form', {
            name: props.formId,
          })
          close()
          router.push({ name: 'Lead', params: { leadId: data.value.lead } })
        },
      },
    ],
  })
}
</script>
