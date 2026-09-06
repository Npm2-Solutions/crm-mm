<template>
  <LayoutHeader>
    <template #left-header>
      <Breadcrumbs :items="[{ label: __('Automations') }]" />
    </template>
    <template #right-header>
      <div class="flex items-center gap-2">
        <Button :label="__('Start from a recipe')" @click="showRecipes = true">
          <template #prefix>
            <FeatherIcon name="book-open" class="size-4" />
          </template>
        </Button>
        <Button
          variant="solid"
          iconLeft="plus"
          :label="__('Create')"
          @click="create()"
        />
      </div>
    </template>
  </LayoutHeader>

  <div class="flex-1 overflow-y-auto">
    <div class="mx-auto flex w-full max-w-4xl flex-col gap-3 px-3 py-4 sm:px-5">
      <div class="flex flex-wrap items-center gap-2">
        <FormControl
          v-model="query"
          class="w-64"
          type="text"
          :placeholder="__('Search automations')"
        />
        <Button
          v-for="entry in FILTERS"
          :key="entry.name"
          size="sm"
          :variant="filter === entry.name ? 'subtle' : 'ghost'"
          :label="__(entry.label)"
          @click="filter = entry.name"
        />
        <div class="flex-1" />
        <span class="text-sm text-ink-gray-5">
          {{
            __('{0} of {1}', [visible.length, automations.data?.length || 0])
          }}
        </span>
      </div>

      <div
        v-if="visible.length"
        class="divide-y divide-outline-gray-1 rounded-lg border border-outline-gray-2"
      >
        <div
          v-for="row in visible"
          :key="row.name"
          class="flex cursor-pointer items-center gap-3 px-3 py-3 hover:bg-surface-gray-1"
          @click="open(row.name)"
        >
          <div
            class="grid size-9 shrink-0 place-items-center rounded-md"
            :class="
              row.enabled
                ? 'bg-surface-green-1 text-ink-green-3'
                : 'bg-surface-gray-2 text-ink-gray-6'
            "
          >
            <FeatherIcon
              :name="triggerDefinition(row.trigger_event).icon"
              class="size-4"
            />
          </div>
          <div class="min-w-0 flex-1">
            <div class="flex items-center gap-2">
              <span class="truncate text-base font-medium text-ink-gray-9">
                {{ row.title }}
              </span>
              <Badge
                size="sm"
                :label="row.enabled ? __('Active') : __('Draft')"
                :theme="row.enabled ? 'green' : 'gray'"
              />
            </div>
            <div class="mt-0.5 truncate text-sm text-ink-gray-5">
              {{ __(row.trigger_event)
              }}<span v-if="row.description"> · {{ row.description }}</span>
            </div>
          </div>
          <div class="hidden shrink-0 text-sm text-ink-gray-5 sm:block">
            {{ row.active_count }} {{ __('running') }} ·
            {{ row.enrolled_count }}
            {{ __('total') }}
          </div>
          <Dropdown :options="rowOptions(row)" placement="right" @click.stop>
            <Button variant="ghost" icon="lucide-more-horizontal" @click.stop />
          </Dropdown>
        </div>
      </div>

      <div
        v-else-if="!automations.loading"
        class="flex flex-col items-center gap-2 py-16 text-ink-gray-4"
      >
        <FeatherIcon name="zap" class="size-8" />
        <span class="text-lg font-medium">
          {{
            automations.data?.length
              ? __('Nothing matches this filter')
              : __('No automations yet')
          }}
        </span>
        <span class="max-w-sm text-center text-sm">
          {{
            __(
              'An automation watches for an event — a new lead, a stage change, a reply — and then works on its own: messages, waits, branches, tasks.',
            )
          }}
        </span>
        <div class="mt-2 flex gap-2">
          <Button
            :label="__('Start from a recipe')"
            @click="showRecipes = true"
          />
          <Button
            variant="solid"
            iconLeft="plus"
            :label="__('Create one')"
            @click="create()"
          />
        </div>
      </div>
    </div>
  </div>

  <Dialog
    v-model="showRecipes"
    :options="{ title: __('Start from a recipe'), size: '2xl' }"
  >
    <template #body-content>
      <div class="grid gap-2 sm:grid-cols-2">
        <button
          v-for="recipe in RECIPES"
          :key="recipe.key"
          class="flex items-start gap-2.5 rounded-lg border border-outline-gray-2 p-3 text-left hover:border-outline-gray-3 hover:bg-surface-gray-1"
          @click="useRecipe(recipe)"
        >
          <div
            class="grid size-8 shrink-0 place-items-center rounded-md bg-surface-gray-2 text-ink-gray-7"
          >
            <FeatherIcon :name="recipe.icon" class="size-4" />
          </div>
          <div class="min-w-0">
            <div class="text-base font-medium text-ink-gray-8">
              {{ __(recipe.title) }}
            </div>
            <div class="text-sm text-ink-gray-5">
              {{ __(recipe.description) }}
            </div>
            <div class="mt-1 text-xs text-ink-gray-4">
              {{ __(recipe.trigger_event) }}
            </div>
          </div>
        </button>
      </div>
    </template>
  </Dialog>
</template>

<script setup>
import LayoutHeader from '@/components/LayoutHeader.vue'
import {
  Badge,
  Breadcrumbs,
  Button,
  Dialog,
  Dropdown,
  FeatherIcon,
  FormControl,
  call,
  createResource,
  toast,
} from 'frappe-ui'
import { computed, ref } from 'vue'
import { useRouter } from 'vue-router'
import { RECIPES, triggerDefinition } from '@/utils/automation'

const router = useRouter()

const FILTERS = [
  { name: 'all', label: 'All' },
  { name: 'active', label: 'Active' },
  { name: 'draft', label: 'Draft' },
]

const query = ref('')
const filter = ref('all')
const showRecipes = ref(false)

const automations = createResource({
  url: 'crm.api.automation.list_automations',
  cache: 'crm-automations',
  auto: true,
})

const visible = computed(() => {
  const needle = query.value.trim().toLowerCase()
  return (automations.data || []).filter((row) => {
    if (filter.value === 'active' && !row.enabled) return false
    if (filter.value === 'draft' && row.enabled) return false
    if (!needle) return true
    return [row.title, row.description, row.trigger_event]
      .map((text) => (text || '').toLowerCase())
      .some((text) => text.includes(needle))
  })
})

function open(name) {
  router.push({ name: 'Automation', params: { automationId: name } })
}

function create(recipe = null) {
  router.push({
    name: 'Automation',
    params: { automationId: 'new' },
    state: recipe ? { recipe } : {},
  })
}

function useRecipe(recipe) {
  showRecipes.value = false
  create({
    title: __(recipe.title),
    description: __(recipe.description),
    trigger_event: recipe.trigger_event,
    steps: recipe.build(),
  })
}

function rowOptions(row) {
  return [
    { label: __('Edit'), icon: 'edit-3', onClick: () => open(row.name) },
    {
      label: row.enabled ? __('Pause') : __('Activate'),
      icon: row.enabled ? 'pause' : 'play',
      onClick: () => toggle(row),
    },
    { label: __('Duplicate'), icon: 'copy', onClick: () => duplicate(row) },
    { label: __('Delete'), icon: 'trash-2', onClick: () => remove(row) },
  ]
}

async function toggle(row) {
  try {
    await call('crm.api.automation.toggle_automation', {
      name: row.name,
      enabled: !row.enabled,
    })
    automations.reload()
  } catch (error) {
    toast.error(error.messages?.[0] || __('Could not change the state'))
  }
}

async function duplicate(row) {
  try {
    const data = await call('crm.api.automation.duplicate_automation', {
      name: row.name,
    })
    automations.reload()
    open(data.name)
  } catch (error) {
    toast.error(error.messages?.[0] || __('Could not duplicate'))
  }
}

async function remove(row) {
  if (!window.confirm(__('Delete «{0}»?', [row.title]))) return
  try {
    await call('crm.api.automation.delete_automation', { name: row.name })
    automations.reload()
  } catch (error) {
    toast.error(error.messages?.[0] || __('Could not delete'))
  }
}
</script>
