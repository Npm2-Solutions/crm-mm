<!--
  The person's forms: what they signed, what is half-filled, and a form to fill
  now. Signed ones open read-only, with their PDF; a draft opens where it was
  left. Like the consents, they follow the person: whoever sees the person sees
  them, except the forms with health data, which are the care team's.
-->
<template>
  <div class="flex flex-col gap-4 px-8 py-6 max-md:px-4 max-md:py-4">
    <div
      class="flex items-start justify-between gap-3 max-md:flex-col max-md:items-stretch"
    >
      <p class="min-w-0 text-p-base text-ink-gray-6">
        {{
          __(
            'Privacy, consents, questionnaires: filled with the person and signed on the screen. A signed form is kept as it was, with its PDF.',
          )
        }}
      </p>
      <Dropdown
        v-if="data?.can_fill && data.templates.length"
        :options="templateOptions"
        placement="right"
      >
        <Button
          class="shrink-0"
          variant="solid"
          icon-left="plus"
          :label="__('Fill a form')"
          :loading="starting"
        />
      </Dropdown>
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
          : __('The forms this person fills and signs are kept here.')
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
            :label="form.docstatus ? __('Signed') : __('To finish')"
            :theme="form.docstatus ? 'green' : 'orange'"
            variant="subtle"
            size="sm"
          />
        </div>
      </button>
    </div>
  </div>
</template>

<script setup>
import EmptyState from '@/components/ListViews/EmptyState.vue'
import { formatDate } from '@/utils'
import LucideFileCheck from '~icons/lucide/file-check'
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

const forms = createResource({
  url: 'crm.moduli.compilazioni.get_person_forms',
  params: { lead: props.lead },
  auto: true,
})
const data = computed(() => forms.data)

const templateOptions = computed(() =>
  (data.value?.templates || []).map((template) => ({
    label: template.title,
    icon: template.clinical ? 'lucide-stethoscope' : 'lucide-file-text',
    onClick: () => start(template.name),
  })),
)

function describe(form) {
  const parts = [__('version {0}', [form.version])]
  if (form.docstatus) {
    parts.push(__('signed {0}', [formatDate(form.signed_on, 'D MMM YYYY, HH:mm')]))
  } else {
    parts.push(__('started {0}', [formatDate(form.modified, 'D MMM YYYY')]))
  }
  if (form.filled_by_name) parts.push(__('with {0}', [form.filled_by_name]))
  return parts.join(' · ')
}

function open(name) {
  router.push({ name: 'FormFill', params: { formId: name } })
}

async function start(template) {
  starting.value = true
  try {
    const form = await call('crm.moduli.compilazioni.start_form', {
      lead: props.lead,
      template,
    })
    open(form.name)
  } catch (error) {
    toast.error(error.messages?.[0] || error.message)
  } finally {
    starting.value = false
  }
}
</script>
