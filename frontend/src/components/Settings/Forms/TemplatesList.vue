<!--
  Modifications copyright (c) 2026, NPM2 Solutions Srl
-->
<template>
  <div
    class="flex h-full flex-col gap-6 p-6 text-ink-gray-8 max-md:px-3 max-md:py-5"
  >
    <div
      class="flex items-start justify-between gap-4 px-2 pt-2 impostazioni-strette:flex-col impostazioni-strette:gap-3"
    >
      <div class="flex min-w-0 flex-col gap-1">
        <h2
          class="flex gap-2 text-2xl-semibold leading-tight md:h-5 md:leading-none"
        >
          {{ heading.title }}
        </h2>
        <p class="text-p-base text-ink-gray-6">{{ heading.description }}</p>
      </div>
      <div class="flex shrink-0 gap-2">
        <!-- the assistant reads the centre's own paper form -->
        <Button
          v-if="
            puo('moduli.configura') &&
            assistant.data?.functions?.form_from_paper
          "
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

    <!-- one list for every use: the filter shows one at a time -->
    <div v-if="filters.length > 2" class="px-2">
      <TabButtons v-model="filter" :buttons="filters" />
    </div>

    <div class="flex h-full flex-col overflow-y-auto">
      <div
        v-if="templates.loading && !templates.data"
        class="mt-12 flex items-center justify-center"
      >
        <LoadingIndicator class="w-4" />
      </div>
      <EmptyState
        v-else-if="!shown.length"
        :title="__('No forms yet')"
        :description="heading.empty"
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
        <template v-for="(template, i) in shown" :key="template.name">
          <div
            class="flex w-full items-center gap-3 rounded px-2 py-3 hover:bg-surface-gray-2 max-md:flex-wrap"
          >
            <button
              type="button"
              class="w-7/12 min-w-0 text-left max-md:w-full"
              @click="$emit('open', template.name)"
            >
              <!-- the name read whole, its tags under it where they do not
                   fit beside it: at 320 it was «Valutazione fisiot…» -->
              <div class="flex min-w-0 flex-wrap items-center gap-x-2 gap-y-1">
                <span
                  class="max-w-full truncate text-base-medium text-ink-gray-7"
                >
                  {{ template.title }}
                </span>
                <!-- what kind of form it is: the design system's Tag, as on a
                     person's documents, quotes and plans. A sheet is written by
                     the operator at the desk, not filled by the person -->
                <CategoryTag
                  v-if="template.use === 'Sheet'"
                  color="blue"
                  :label="__('Sheet')"
                />
                <!-- filled by anybody on the centre's website -->
                <CategoryTag
                  v-else-if="template.use === 'Website'"
                  color="violet"
                  :label="__('Website')"
                />
                <CategoryTag
                  v-if="template.clinical"
                  color="rose"
                  :label="__('Health data')"
                />
              </div>
              <!-- on a phone the line wraps: cut, it lost the address's end
                   and when the form was published -->
              <div
                class="mt-0.5 truncate text-p-base text-ink-gray-5 max-md:whitespace-normal max-md:[overflow-wrap:anywhere]"
              >
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
                  :aria-label="__('Options')"
                  class="touch-target shrink-0"
                  icon="lucide-more-horizontal"
                  variant="ghost"
                />
              </Dropdown>
            </div>
          </div>
          <hr v-if="shown.length !== i + 1" class="mx-2" />
        </template>
      </div>
    </div>
  </div>

  <Dialog v-model="showCreate" :options="{ title: __('New form'), size: 'xl' }">
    <template #body-content>
      <div class="flex flex-col gap-4">
        <FormControl
          v-if="uses.data?.length > 1"
          v-model="draft.use"
          type="select"
          :label="__('Use')"
          :options="uses.data"
          :description="useOf(draft.use)?.description"
        />
        <FormControl
          v-model="draft.title"
          type="text"
          :label="__('Title')"
          :placeholder="
            draft.use === 'Website'
              ? __('Request information')
              : __('Privacy notice')
          "
        />
        <div class="flex flex-col gap-1.5">
          <span class="text-sm text-ink-gray-5">{{ __('Start from') }}</span>
          <div class="grid grid-cols-2 gap-2 max-md:grid-cols-1">
            <button
              v-for="starter in startersFor(draft.use)"
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
import { copyToClipboard, formatDate } from '@/utils'
import { usersStore } from '@/stores/users'
import EmptyState from '@/components/ListViews/EmptyState.vue'
import PaperFormDialog from '@/components/Settings/Forms/PaperFormDialog.vue'
import CategoryTag from '@/components/Espresso/CategoryTag.vue'
import LucideFileSignature from '~icons/lucide/file-signature'
import {
  Badge,
  Button,
  Dialog,
  Dropdown,
  ErrorMessage,
  FormControl,
  LoadingIndicator,
  TabButtons,
  call,
  createResource,
  toast,
} from 'frappe-ui'
import { computed, h, reactive, ref, watch } from 'vue'

const emit = defineEmits(['open'])

const { puo } = usersStore()

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

// what a new template may be, for this session: the centre's, the website's, both
const uses = createResource({
  url: 'crm.moduli.modelli.get_uses',
  auto: true,
})
const useOf = (value) => (uses.data || []).find((use) => use.value === value)

const heading = computed(() => {
  const centre = puo('moduli.configura')
  if (!centre) {
    return {
      title: __('Forms on the website'),
      description: __(
        "On their own page, in another site or in a page of the centre's: whoever sends one is found by their email or mobile, or made, and their deal opens.",
      ),
      empty: __('Start from a contact request or a newsletter sign-up.'),
    }
  }
  return {
    title: __('Forms'),
    description: puo('moduli_lead.gestisci')
      ? __(
          'What people fill and sign, the sheets the operator writes, the forms on the website. You work on a draft; people fill the published version, which never changes, so what was filled can always be shown word for word.',
        )
      : __(
          'What people fill and sign, and the sheets the operator writes. You work on a draft; people fill the published version, which never changes, so what was filled can always be shown word for word.',
        ),
    empty: __(
      'Start from a privacy notice, a first visit history or an informed consent.',
    ),
  }
})

const USE_FILTERS = {
  Form: () => __('To fill and sign'),
  Sheet: () => __('Sheets'),
  Website: () => __('On the website'),
}
const filter = ref('all')
const filters = computed(() => {
  const present = [...new Set((templates.data || []).map((t) => t.use))]
  return [
    { label: __('All'), value: 'all' },
    ...present.map((use) => ({
      label: USE_FILTERS[use]?.() || useOf(use)?.label || use,
      value: use,
    })),
  ]
})
const shown = computed(() =>
  (templates.data || []).filter(
    (template) => filter.value === 'all' || template.use === filter.value,
  ),
)

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
// a blank one for every use; the others for their own
const startersFor = (use) =>
  starters.filter(
    (starter) => starter.key === 'blank' || (starter.use || 'Form') === use,
  )

function summary(template) {
  const parts = [
    template.questions === 1
      ? __('1 question')
      : __('{0} questions', [template.questions]),
  ]
  if (template.route) parts.push(`/crm-form/${template.route}`)
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
  // a form of the website, published: its page, and its link to give
  const online = template.url && template.current_version && template.enabled
  return [
    {
      label: __('Edit'),
      icon: 'lucide-pencil',
      onClick: () => emit('open', template.name),
    },
    online && {
      label: __('Open the page'),
      icon: 'lucide-external-link',
      onClick: () => window.open(template.url, '_blank'),
    },
    online && {
      label: __('Copy the link'),
      icon: 'lucide-link',
      onClick: () => copyToClipboard(template.url),
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
const draft = reactive({ title: '', use: 'Form', starter: 'blank', error: '' })

function openCreate() {
  // the filter says what is being made, when it names one of the session's uses
  const first = uses.data?.[0]?.value || 'Form'
  const use = useOf(filter.value) ? filter.value : first
  Object.assign(draft, { title: '', use, starter: 'blank', error: '' })
  showCreate.value = true
}

// another use, another set of starters: a form of the desk is not a website's
watch(
  () => draft.use,
  (use) => {
    if (!startersFor(use).some((s) => s.key === draft.starter)) {
      pickStarter(starters[0])
    }
  },
)

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
      use: draft.use,
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
