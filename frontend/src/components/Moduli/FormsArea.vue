<!--
  The person's forms: what they signed, what is half-filled, and a form to fill
  now, with them at the desk or on their own (a link by email, the desk's
  tablet). Signed ones open read-only, with their PDF; a draft opens where it
  was left. Like the consents, they follow the person: whoever sees the person
  sees them, except the forms with health data, which are the care team's.
-->
<template>
  <div class="flex flex-col gap-4 px-8 py-6 max-md:px-4 max-md:py-4">
    <div
      class="flex items-start justify-between gap-3 max-md:flex-col max-md:items-stretch"
    >
      <p class="min-w-0 text-p-base text-ink-gray-6">
        {{
          __(
            "Privacy, consents, questionnaires: filled with the person and signed on the screen, or on their own from a link or the desk's tablet. The sheets are written by the operator during the appointment. What is signed is kept as it was, with its PDF.",
          )
        }}
      </p>
      <div
        v-if="data?.can_fill && data.templates.length"
        class="flex shrink-0 gap-2 max-md:flex-wrap"
      >
        <Button
          v-if="personForms.length"
          icon-left="send"
          :label="__('On their own')"
          @click="showSend = true"
        />
        <Dropdown :options="templateOptions" placement="right">
          <Button
            variant="solid"
            icon-left="plus"
            :label="__('Fill a form')"
            :loading="starting"
          />
        </Dropdown>
      </div>
    </div>

    <!-- what the person owes: for their next appointment, or in general -->
    <div v-if="owed.length" class="flex flex-col gap-1">
      <span class="text-sm font-medium text-ink-gray-5">
        {{
          data.due.appointment
            ? __('To sign for the appointment of {0}', [
                formatDate(data.due.appointment.starts_on, 'D MMM, HH:mm'),
              ])
            : __('To sign')
        }}
      </span>
      <div
        v-for="form in owed"
        :key="form.template"
        class="flex min-w-0 items-center gap-3 rounded px-2 py-2.5 hover:bg-surface-gray-2 max-md:flex-wrap"
      >
        <LucideFileClock class="size-4 shrink-0 text-ink-gray-5" />
        <div class="min-w-0 flex-1">
          <div class="truncate text-base text-ink-gray-8">{{ form.title }}</div>
          <div class="text-sm text-ink-gray-5">
            {{ REASONS[form.reason]() }}
          </div>
        </div>
        <div class="flex shrink-0 items-center gap-1.5">
          <Badge
            v-if="form.pending"
            :label="PENDING[form.pending]()"
            theme="blue"
            variant="subtle"
            size="sm"
          />
          <Button
            v-else-if="data.can_fill"
            size="sm"
            class="touch-target"
            :label="__('Fill')"
            @click="start(form.template, form.appointment)"
          />
        </div>
      </div>
    </div>

    <!-- what was sent and has not come back -->
    <div v-if="waiting.length" class="flex flex-col gap-1">
      <span class="text-sm font-medium text-ink-gray-5">{{
        __('Sent to fill')
      }}</span>
      <RequestRow
        v-for="request in waiting"
        :key="request.name"
        :request="request"
        :can-fill="data?.can_fill"
        @withdraw="withdraw"
        @open="open"
      />
    </div>

    <div v-if="forms.loading && !data" class="flex justify-center py-10">
      <LoadingIndicator class="w-4" />
    </div>
    <EmptyState
      v-else-if="!data?.forms.length"
      :title="__('No forms yet')"
      :description="
        data?.can_fill && !data.templates.length
          ? __('Publish a form in Settings > Forms to fill it here.')
          : __(
              'The forms this person fills and signs, and the sheets written for them, are kept here.',
            )
      "
      :icon="h(LucideFileSignature)"
    />
    <div v-else class="flex flex-col">
      <button
        v-for="form in data.forms"
        :key="form.name"
        type="button"
        class="flex w-full min-w-0 items-center gap-3 border-b border-outline-gray-1 px-2 py-3 text-left hover:bg-surface-gray-2 max-md:flex-wrap"
        @click="open(form.name)"
      >
        <component
          :is="form.docstatus ? LucideFileCheck : LucideFilePen"
          class="size-4 shrink-0 text-ink-gray-5"
        />
        <div class="min-w-0 flex-1">
          <div class="truncate text-base font-medium text-ink-gray-8">
            {{ form.title }}
          </div>
          <div class="truncate text-sm text-ink-gray-5">
            {{ describe(form) }}
          </div>
        </div>
        <div class="flex shrink-0 flex-wrap items-center gap-1.5">
          <Badge
            v-if="form.alerts?.length"
            :label="
              form.alerts.length === 1
                ? __('1 warning')
                : __('{0} warnings', [form.alerts.length])
            "
            theme="red"
            variant="subtle"
            size="sm"
          />
          <Badge
            v-if="form.use === 'Sheet'"
            :label="__('Sheet')"
            theme="gray"
            variant="subtle"
            size="sm"
          />
          <Badge
            :label="
              form.docstatus
                ? form.use === 'Sheet'
                  ? __('Completed')
                  : form.channel === 'Website'
                    ? __('Sent')
                    : __('Signed')
                : __('To finish')
            "
            :theme="form.docstatus ? 'green' : 'orange'"
            variant="subtle"
            size="sm"
          />
        </div>
      </button>
    </div>

    <div v-if="earlier.length" class="flex flex-col gap-1">
      <button
        type="button"
        class="touch-target flex w-fit items-center gap-1 text-sm text-ink-gray-5 hover:text-ink-gray-7"
        @click="showEarlier = !showEarlier"
      >
        <LucideChevronRight
          class="size-3.5 transition-transform"
          :class="{ 'rotate-90': showEarlier }"
        />
        {{ __('Sent earlier ({0})', [earlier.length]) }}
      </button>
      <template v-if="showEarlier">
        <RequestRow
          v-for="request in earlier"
          :key="request.name"
          :request="request"
          @open="open"
        />
      </template>
    </div>

    <SendFormsDialog
      v-if="showSend"
      v-model="showSend"
      :lead="lead"
      :preselect="
        owed.filter((form) => !form.pending).map((form) => form.template)
      "
      :appointment="data?.due?.appointment?.name || null"
      @sent="
        () => {
          requests.reload()
          forms.reload()
        }
      "
    />
  </div>
</template>

<script setup>
import EmptyState from '@/components/ListViews/EmptyState.vue'
import RequestRow from '@/components/Moduli/RequestRow.vue'
import SendFormsDialog from '@/components/Moduli/SendFormsDialog.vue'
import { formatDate } from '@/utils'
import LucideChevronRight from '~icons/lucide/chevron-right'
import LucideFileCheck from '~icons/lucide/file-check'
import LucideFileClock from '~icons/lucide/file-clock'
import LucideFilePen from '~icons/lucide/file-pen-line'
import LucideFileSignature from '~icons/lucide/file-signature'
import {
  Badge,
  Button,
  Dropdown,
  LoadingIndicator,
  call,
  createResource,
  toast,
} from 'frappe-ui'
import { computed, h, ref } from 'vue'
import { useRouter } from 'vue-router'

const props = defineProps({ lead: { type: String, required: true } })

const router = useRouter()
const starting = ref(false)
const showSend = ref(false)
const showEarlier = ref(false)

const forms = createResource({
  url: 'crm.moduli.compilazioni.get_person_forms',
  params: { lead: props.lead },
  auto: true,
})
const data = computed(() => forms.data)

const requests = createResource({
  url: 'crm.moduli.richieste.get_requests',
  params: { lead: props.lead },
  auto: true,
})
const STILL_OUT = ['Sent', 'Opened', 'Filled']
const waiting = computed(() =>
  (requests.data || []).filter((request) => STILL_OUT.includes(request.status)),
)
const earlier = computed(() =>
  (requests.data || []).filter(
    (request) => !STILL_OUT.includes(request.status),
  ),
)

const owed = computed(() => data.value?.due?.forms || [])
const REASONS = {
  never_signed: () => __('Never signed'),
  new_version: () => __('A new version: to sign again'),
  expired: () => __('Signed more than a year ago'),
  every_appointment: () => __('Signed for each appointment'),
}
const PENDING = {
  draft: () => __('Started'),
  sent: () => __('Link sent'),
  to_sign_at_desk: () => __('To sign at the desk'),
}

// the person's forms, and the operator's sheets: filled at the desk, never sent
const personForms = computed(() =>
  (data.value?.templates || []).filter((template) => template.use !== 'Sheet'),
)
const sheets = computed(() =>
  (data.value?.templates || []).filter((template) => template.use === 'Sheet'),
)
function asOption(template) {
  return {
    label: template.title,
    icon: template.clinical ? 'lucide-stethoscope' : 'lucide-file-text',
    onClick: () => start(template.name),
  }
}
const templateOptions = computed(() => {
  if (!sheets.value.length) return personForms.value.map(asOption)
  return [
    { group: __('Forms'), items: personForms.value.map(asOption) },
    { group: __('Sheets'), items: sheets.value.map(asOption) },
  ].filter((group) => group.items.length)
})

const WHERE = {
  Link: () => __('from a link'),
  Tablet: () => __('on the tablet'),
  Website: () => __('from the website'),
}

function describe(form) {
  const parts = [__('version {0}', [form.version])]
  if (form.docstatus) {
    const when = formatDate(form.signed_on, 'D MMM YYYY, HH:mm')
    parts.push(
      form.use === 'Sheet'
        ? __('completed {0}', [when])
        : form.channel === 'Website'
          ? __('sent {0}', [when])
          : __('signed {0}', [when]),
    )
  } else {
    parts.push(__('started {0}', [formatDate(form.modified, 'D MMM YYYY')]))
  }
  if (WHERE[form.channel]) parts.push(WHERE[form.channel]())
  if (form.filled_by_name) parts.push(__('with {0}', [form.filled_by_name]))
  return parts.join(' · ')
}

function open(name) {
  router.push({ name: 'FormFill', params: { formId: name } })
}

async function start(template, appointment = null) {
  starting.value = true
  try {
    const form = await call('crm.moduli.compilazioni.start_form', {
      lead: props.lead,
      template,
      appointment,
    })
    open(form.name)
  } catch (error) {
    toast.error(error.messages?.[0] || error.message)
  } finally {
    starting.value = false
  }
}

async function withdraw(request) {
  try {
    await call('crm.moduli.richieste.cancel_request', { name: request.name })
    toast.success(__('Withdrawn: the link no longer opens it'))
    requests.reload()
    forms.reload()
  } catch (error) {
    toast.error(error.messages?.[0] || error.message)
  }
}
</script>
