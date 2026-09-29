<!--
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
          :label="signed ? __('Signed') : __('To finish')"
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

  <div class="flex-1 overflow-y-auto">
    <div v-if="!data" class="flex justify-center py-16">
      <LoadingIndicator class="w-5" />
    </div>
    <div v-else class="mx-auto flex max-w-2xl flex-col gap-6 px-5 py-6 max-md:px-4">
      <div class="flex flex-col gap-1">
        <h1 class="text-2xl font-semibold text-ink-gray-9">{{ data.title }}</h1>
        <p class="text-p-base text-ink-gray-6">
          {{ data.lead_name }} · {{ __('version {0}', [data.version]) }}
          <template v-if="signed">
            · {{ __('signed {0}', [formatDate(data.signed_on, 'D MMM YYYY, HH:mm')]) }}
          </template>
        </p>
      </div>

      <div
        v-if="stops.length"
        class="flex flex-col gap-1 rounded-lg bg-surface-red-1 px-4 py-3 text-sm text-ink-red-4"
        role="alert"
      >
        <div class="flex items-center gap-2 font-medium">
          <LucideTriangleAlert class="size-4 shrink-0" />
          {{ __('Warnings for the operator') }}
        </div>
        <span v-for="stop in stops" :key="stop.field">
          {{ labelOf(stop.field) }}: {{ stop.message || __('Stop here and tell the operator') }}
        </span>
      </div>

      <div v-if="!signed" class="flex flex-col gap-1.5">
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
        :readonly="signed"
        :show-missing="tried"
      />

      <div
        v-if="!signed && data.can_sign"
        class="dialog-footer sticky bottom-0 flex items-center justify-between gap-2 border-t border-outline-gray-2 bg-surface-base py-3 max-md:flex-wrap"
      >
        <Button
          variant="ghost"
          theme="red"
          :label="__('Discard')"
          @click="discard"
        />
        <div class="flex gap-2 max-md:w-full max-md:justify-end">
          <Button :label="__('Save for later')" :loading="saving" @click="save" />
          <Button
            variant="solid"
            :label="__('Sign and finish')"
            :loading="signing"
            @click="sign"
          />
        </div>
      </div>

      <!-- signed: what proves it -->
      <section
        v-if="signed"
        class="flex flex-col gap-3 rounded-lg border border-outline-gray-2 px-4 py-4"
      >
        <h2 class="text-base font-semibold text-ink-gray-8">{{ __('Evidence') }}</h2>
        <dl class="grid grid-cols-[10rem_1fr] gap-x-4 gap-y-2 text-sm max-md:grid-cols-1">
          <dt class="text-ink-gray-5">{{ __('What it asked (SHA-256)') }}</dt>
          <dd class="break-all font-mono text-xs text-ink-gray-7">{{ data.schema_hash }}</dd>
          <dt class="text-ink-gray-5">{{ __('The answers (SHA-256)') }}</dt>
          <dd class="break-all font-mono text-xs text-ink-gray-7">{{ data.answers_hash }}</dd>
          <template v-if="data.pdf_hash">
            <dt class="text-ink-gray-5">{{ __('The PDF (SHA-256)') }}</dt>
            <dd class="break-all font-mono text-xs text-ink-gray-7">
              {{ data.pdf_hash }}
              <span class="block font-sans text-ink-gray-5">{{ data.pdf_conformance }}</span>
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
            <span v-if="event.detail" class="text-ink-gray-5">· {{ event.detail }}</span>
          </div>
        </div>
      </section>
    </div>
  </div>
</template>

<script setup>
import LayoutHeader from '@/components/LayoutHeader.vue'
import Link from '@/components/Controls/Link.vue'
import FormRenderer from '@/components/Moduli/FormRenderer.vue'
import { evaluate, fieldsOf } from '@/utils/moduli'
import { formatDate } from '@/utils'
import { globalStore } from '@/stores/global'
import LucideTriangleAlert from '~icons/lucide/triangle-alert'
import {
  Badge,
  Breadcrumbs,
  Button,
  LoadingIndicator,
  call,
  toast,
  usePageMeta,
} from 'frappe-ui'
import { computed, ref } from 'vue'
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

const signed = computed(() => data.value?.docstatus === 1)
const signatureFields = computed(() =>
  fieldsOf(data.value?.schema).filter((field) => field.type === 'signature'),
)

function apply(form) {
  data.value = form
  givenBy.value = form.given_by || null
  const shown = { ...(form.answers || {}) }
  // a signed form shows its strokes where they were drawn
  for (const signature of form.signatures || []) shown[signature.field] = signature.image
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
        route: { name: 'Lead', params: { leadId: data.value.lead }, hash: '#forms' },
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
  return fieldsOf(data.value?.schema).find((field) => field.id === key)?.label || key
}

const EVENTS = {
  created: __('Started'),
  signed: __('Signed'),
  pdf_generated: __('PDF made'),
  pdf_failed: __('PDF not made'),
  consent_recorded: __('Consent recorded'),
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
      .filter(([, value]) => typeof value === 'string' && value.startsWith('data:image/png')),
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
    toast.success(__('Signed'))
  } catch (error) {
    toast.error(error.messages?.join(' ') || error.message)
  } finally {
    signing.value = false
  }
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
          await call('crm.moduli.compilazioni.discard_form', { name: props.formId })
          close()
          router.push({ name: 'Lead', params: { leadId: data.value.lead } })
        },
      },
    ],
  })
}
</script>
