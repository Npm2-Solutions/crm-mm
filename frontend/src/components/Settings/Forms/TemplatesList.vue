<template>
  <div
    class="flex h-full flex-col gap-6 p-6 text-ink-gray-8 max-md:px-3 max-md:py-5"
  >
    <div
      class="flex items-start justify-between gap-4 px-2 pt-2 max-md:flex-col max-md:gap-3"
    >
      <div class="flex min-w-0 flex-col gap-1">
        <h2
          class="flex gap-2 text-2xl-semibold leading-tight md:h-5 md:leading-none"
        >
          {{ __('Forms to sign') }}
        </h2>
        <p class="text-p-base text-ink-gray-6">
          {{
            __(
              'Privacy notices, consents, questionnaires: what people fill and sign. You work on a draft; people fill the published version, which never changes, so what someone signed can always be shown word for word.',
            )
          }}
        </p>
      </div>
      <div class="flex shrink-0 gap-2">
        <!-- the assistant reads the centre's own paper form -->
        <Button
          v-if="assistant.data?.functions?.form_from_paper"
          :label="__('From a paper form')"
          icon-left="lucide-sparkles"
          @click="paper = true"
        />
        <Button
          :label="__('New')"
          icon-left="lucide-plus"
          variant="solid"
          @click="openCreate"
        />
      </div>
    </div>
    <PaperFormDialog v-model="paper" @created="(name) => $emit('open', name)" />

    <div class="flex h-full flex-col overflow-y-auto">
      <div
        v-if="templates.loading && !templates.data"
        class="mt-12 flex items-center justify-center"
      >
        <LoadingIndicator class="w-4" />
      </div>
      <EmptyState
        v-else-if="!templates.data?.length"
        :title="__('No forms to sign yet')"
        :description="
          __(
            'Start from a privacy notice, a first visit history or an informed consent.',
          )
        "
        :icon="h(LucideFileSignature)"
      />
      <div v-else class="w-full">
        <div
          class="flex items-center p-2 text-sm text-ink-gray-5 max-md:hidden"
        >
          <div class="w-7/12">{{ __('Form') }}</div>
          <div class="w-5/12">{{ __('Status') }}</div>
        </div>
        <div class="mx-2 h-px border-t border-outline-elevation-2" />
        <template v-for="(template, i) in templates.data" :key="template.name">
          <div
            class="flex w-full items-center gap-3 rounded px-2 py-3 hover:bg-surface-gray-2 max-md:flex-wrap"
          >
            <button
              type="button"
              class="w-7/12 min-w-0 text-left max-md:w-full"
              @click="$emit('open', template.name)"
            >
              <div class="flex min-w-0 items-center gap-2">
                <span class="truncate text-base-medium text-ink-gray-7">
                  {{ template.title }}
                </span>
                <!-- written by the operator at the desk, not filled by the person -->
                <Badge
                  v-if="template.use === 'Sheet'"
                  :label="__('Sheet')"
                  theme="gray"
                  variant="subtle"
                  size="sm"
                />
                <Badge
                  v-if="template.clinical"
                  :label="__('Health data')"
                  theme="blue"
                  variant="subtle"
                  size="sm"
                />
              </div>
              <div class="mt-0.5 truncate text-p-base text-ink-gray-5">
                {{ summary(template) }}
              </div>
            </button>
            <div
              class="flex w-5/12 min-w-0 items-center justify-between gap-2 max-md:w-full"
            >
              <div class="flex min-w-0 flex-wrap items-center gap-1.5">
                <Badge
                  v-for="badge in badges(template)"
                  :key="badge.label"
                  :label="badge.label"
                  :theme="badge.theme"
                  variant="outline"
                  size="md"
                />
              </div>
              <Dropdown placement="right" :options="rowOptions(template)">
                <Button
                  class="touch-target shrink-0"
                  icon="lucide-more-horizontal"
                  variant="ghost"
                />
              </Dropdown>
            </div>
          </div>
          <hr v-if="templates.data.length !== i + 1" class="mx-2" />
        </template>
      </div>
    </div>
  </div>

  <Dialog
    v-model="showCreate"
    :options="{ title: __('New form to sign'), size: 'xl' }"
  >
    <template #body-content>
      <div class="flex flex-col gap-4">
        <FormControl
          v-model="draft.title"
          type="text"
          :label="__('Title')"
          :placeholder="__('Privacy notice')"
        />
        <div class="flex flex-col gap-1.5">
          <span class="text-sm text-ink-gray-5">{{ __('Start from') }}</span>
          <div class="grid grid-cols-2 gap-2 max-md:grid-cols-1">
            <button
              v-for="starter in starters"
              :key="starter.key"
              type="button"
              class="flex min-w-0 flex-col gap-0.5 rounded-lg border px-3 py-2.5 text-left"
              :class="
                draft.starter === starter.key
                  ? 'border-outline-gray-5 bg-surface-gray-2'
                  : 'border-outline-gray-2'
              "
              @click="pickStarter(starter)"
            >
              <span class="text-base font-medium text-ink-gray-8">
                {{ starter.title }}
              </span>
              <span class="text-sm text-ink-gray-5">{{
                starter.description
              }}</span>
            </button>
          </div>
        </div>
        <ErrorMessage :message="draft.error" />
      </div>
    </template>
    <template #actions>
      <div class="dialog-footer flex justify-end gap-2">
        <Button :label="__('Cancel')" @click="showCreate = false" />
        <Button
          variant="solid"
          :label="__('Create')"
          :loading="creating"
          :disabled="!draft.title?.trim()"
          @click="create"
        />
      </div>
    </template>
  </Dialog>
</template>

<script setup>
import { STARTERS } from '@/utils/moduliStarters'
import { formatDate } from '@/utils'
import EmptyState from '@/components/ListViews/EmptyState.vue'
import PaperFormDialog from '@/components/Settings/Forms/PaperFormDialog.vue'
import LucideFileSignature from '~icons/lucide/file-signature'
import {
  Badge,
  Button,
  Dialog,
  Dropdown,
  ErrorMessage,
  FormControl,
  LoadingIndicator,
  call,
  createResource,
  toast,
} from 'frappe-ui'
import { h, reactive, ref } from 'vue'

const emit = defineEmits(['open'])

const paper = ref(false)
const assistant = createResource({
  url: 'crm.assistente.modello.get_status',
  auto: true,
})

const templates = createResource({
  url: 'crm.moduli.modelli.get_templates',
  auto: true,
})

defineExpose({ reload: () => templates.reload() })

const starters = [
  {
    key: 'blank',
    title: __('Blank'),
    description: __('Sections and questions of your own'),
    schema: () => ({ sections: [{ id: 'section', title: '', fields: [] }] }),
  },
  ...STARTERS.map((starter) => ({
    ...starter,
    title: __(starter.title),
    description: __(starter.description),
  })),
]

function summary(template) {
  const parts = [
    template.questions === 1
      ? __('1 question')
      : __('{0} questions', [template.questions]),
  ]
  if (template.specialty) parts.push(template.specialty)
  if (template.published_on) {
    parts.push(
      __('published {0}', [formatDate(template.published_on, 'D MMM YYYY')]),
    )
  }
  return parts.join(' · ')
}

function badges(template) {
  const found = []
  if (!template.enabled) found.push({ label: __('Off'), theme: 'gray' })
  if (template.current_version_number) {
    found.push({
      label: __('Version {0}', [template.current_version_number]),
      theme: 'green',
    })
    if (template.unpublished_changes) {
      found.push({ label: __('Changes not published'), theme: 'orange' })
    }
  } else {
    found.push({ label: __('Draft'), theme: 'gray' })
  }
  return found
}

function rowOptions(template) {
  return [
    {
      label: __('Edit'),
      icon: 'lucide-pencil',
      onClick: () => emit('open', template.name),
    },
    {
      label: __('Duplicate'),
      icon: 'lucide-copy',
      onClick: () =>
        run('crm.moduli.modelli.duplicate_template', template, __('Copied')),
    },
    {
      label: template.enabled ? __('Switch off') : __('Switch on'),
      icon: template.enabled ? 'lucide-eye-off' : 'lucide-eye',
      onClick: () =>
        run(
          'crm.moduli.modelli.save_template',
          { ...template, enabled: template.enabled ? 0 : 1 },
          template.enabled ? __('Switched off') : __('Switched on'),
        ),
    },
    // a published one stays: what was signed on it points at it
    !template.current_version && {
      label: __('Delete'),
      icon: 'lucide-trash-2',
      theme: 'red',
      onClick: () =>
        run('crm.moduli.modelli.delete_template', template, __('Deleted')),
    },
  ].filter(Boolean)
}

async function run(method, template, done) {
  try {
    const args = { name: template.name }
    if (method.endsWith('save_template')) args.enabled = template.enabled
    await call(method, args)
    toast.success(done)
    templates.reload()
  } catch (error) {
    toast.error(error.messages?.[0] || error.message)
  }
}

const showCreate = ref(false)
const creating = ref(false)
const draft = reactive({ title: '', starter: 'blank', error: '' })

function openCreate() {
  Object.assign(draft, { title: '', starter: 'blank', error: '' })
  showCreate.value = true
}

function pickStarter(starter) {
  const previous = starters.find((s) => s.key === draft.starter)
  // the title follows the starter until somebody writes their own
  if (!draft.title || draft.title === previous?.title) {
    draft.title = starter.key === 'blank' ? '' : starter.title
  }
  draft.starter = starter.key
}

async function create() {
  creating.value = true
  draft.error = ''
  try {
    const starter = starters.find((s) => s.key === draft.starter) || starters[0]
    const saved = await call('crm.moduli.modelli.save_template', {
      title: draft.title.trim(),
      schema: JSON.stringify(starter.schema()),
    })
    showCreate.value = false
    emit('open', saved.name)
  } catch (error) {
    draft.error = error.messages?.[0] || error.message
  } finally {
    creating.value = false
  }
}
</script>
