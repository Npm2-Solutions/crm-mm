<template>
  <Dialog
    v-model:open="show"
    :title="creating ? __('New dashboard') : __('Dashboard settings')"
    size="xl"
  >
    <template #default>
      <div class="flex flex-col gap-5">
        <FormControl
          v-model="form.title"
          type="text"
          size="md"
          :label="__('Name')"
          :placeholder="creating ? __('e.g. Monday meeting') : placeholderTitle"
        />

        <div v-if="creating">
          <div class="mb-2 text-sm text-ink-gray-5">{{ __('Start from') }}</div>
          <div class="grid grid-cols-1 gap-2 sm:grid-cols-2">
            <button
              v-for="option in starts"
              :key="option.id"
              class="flex items-start gap-3 rounded-lg border p-3 text-left transition-colors"
              :class="[
                form.template === option.id
                  ? 'border-outline-gray-5 bg-surface-gray-1 ring-1 ring-outline-gray-5'
                  : 'border-outline-gray-2 hover:border-outline-gray-3',
                option.available === false ? 'opacity-60' : '',
              ]"
              @click="pick(option)"
            >
              <span
                class="grid size-8 shrink-0 place-items-center rounded-md bg-surface-gray-2"
              >
                <Icon :icon="option.icon" class="size-4 text-ink-gray-7" />
              </span>
              <span class="min-w-0">
                <span class="block text-sm font-medium text-ink-gray-8">{{
                  option.title
                }}</span>
                <span class="line-clamp-2 block text-xs text-ink-gray-5">
                  {{
                    option.available === false
                      ? __('Nothing to show yet on this site')
                      : option.description
                  }}
                </span>
              </span>
            </button>
          </div>
        </div>

        <div v-if="creating && canShare" class="flex flex-col gap-2">
          <div class="text-sm text-ink-gray-5">{{ __('Who sees it') }}</div>
          <div class="flex flex-wrap gap-2">
            <Button
              :variant="form.private ? 'solid' : 'outline'"
              :label="__('Only me')"
              iconLeft="lock"
              @click="form.private = true"
            />
            <Button
              :variant="!form.private ? 'solid' : 'outline'"
              :label="__('The whole team')"
              iconLeft="users"
              @click="form.private = false"
            />
          </div>
        </div>

        <template v-if="!creating">
          <div>
            <div class="mb-1.5 text-sm text-ink-gray-5">{{ __('Icon') }}</div>
            <IconPicker
              v-model="form.icon"
              :max-icons="1000"
              :placeholder="__('Select an icon...')"
            />
          </div>
          <FormControl
            v-model="form.period"
            type="select"
            size="md"
            :label="__('Opens on')"
            :options="periodOptions"
          />
          <div class="flex items-start justify-between gap-6">
            <div>
              <div class="text-sm font-medium text-ink-gray-8">
                {{ __('Only my work') }}
              </div>
              <div class="text-p-sm text-ink-gray-5">
                {{
                  __(
                    'Every widget counts only the work of whoever is looking — a personal dashboard for each person.',
                  )
                }}
              </div>
            </div>
            <Switch v-model="form.only_mine" />
          </div>
        </template>

        <ErrorMessage :message="error" />
      </div>
    </template>
    <template #actions>
      <div class="flex justify-end gap-2">
        <Button :label="__('Cancel')" @click="show = false" />
        <Button
          variant="solid"
          :label="creating ? __('Create') : __('Save')"
          :loading="busy"
          :disabled="creating && !form.title.trim()"
          @click="submit"
        />
      </div>
    </template>
  </Dialog>
</template>

<script setup>
import Icon from '@/components/Icon.vue'
import { PERIODS, periodLabel } from '@/utils/dashboard'
import { IconPicker } from 'frappe-ui/icons'
import { call, Dialog, ErrorMessage, FormControl, Switch } from 'frappe-ui'
import { computed, reactive, ref, watch } from 'vue'

const props = defineProps({
  mode: { type: String, default: 'create' },
  dashboard: { type: Object, default: null },
  templates: { type: Array, default: () => [] },
  canShare: { type: Boolean, default: false },
})

const emit = defineEmits(['saved'])

const show = defineModel({ type: Boolean, default: false })

const creating = computed(() => props.mode === 'create')
const busy = ref(false)
const error = ref('')

const form = reactive({
  title: '',
  template: '',
  private: true,
  icon: '',
  period: '',
  only_mine: false,
})

const placeholderTitle = computed(() => props.dashboard?.title || '')

const starts = computed(() => [
  {
    id: '',
    title: __('Blank'),
    description: __('An empty page to fill with the widgets you choose'),
    icon: 'layout-grid',
  },
  ...props.templates,
])

const periodOptions = computed(() =>
  PERIODS.map((key) => ({ label: periodLabel(key), value: key })),
)

watch(show, (open) => {
  if (!open) return
  error.value = ''
  if (creating.value) {
    Object.assign(form, { title: '', template: '', private: true })
  } else if (props.dashboard) {
    Object.assign(form, {
      title: props.dashboard.title || '',
      icon: props.dashboard.icon || '',
      period: props.dashboard.period || 'last_30_days',
      only_mine: Boolean(props.dashboard.only_mine),
    })
  }
})

function pick(option) {
  form.template = option.id
  // a template's name is a good first name for a dashboard made from it
  if (
    option.id &&
    (!form.title || starts.value.some((start) => start.title === form.title))
  ) {
    form.title = option.title
  }
}

async function submit() {
  busy.value = true
  error.value = ''
  try {
    const saved = creating.value
      ? await call('crm.api.dashboard.create_dashboard', {
          title: form.title.trim(),
          private: form.private ? 1 : 0,
          template: form.template || null,
        })
      : await call('crm.api.dashboard.update_dashboard', {
          name: props.dashboard.name,
          title: form.title.trim(),
          icon: form.icon || '',
          period: form.period,
          only_mine: form.only_mine ? 1 : 0,
        })
    emit('saved', saved)
    show.value = false
  } catch (e) {
    error.value =
      e?.messages?.[0] || e?.message || __('Could not save the dashboard')
  } finally {
    busy.value = false
  }
}
</script>
