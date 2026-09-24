<template>
  <aside
    class="flex h-full w-[22rem] shrink-0 flex-col border-l border-outline-gray-2 bg-surface-base"
    :aria-label="__('Widget library')"
  >
    <div class="flex items-center justify-between gap-2 px-4 pb-2 pt-3">
      <div>
        <h2 class="text-base font-semibold text-ink-gray-9">
          {{ __('Add widgets') }}
        </h2>
        <p class="text-xs text-ink-gray-5">
          {{ __('{0} ready for your site', [readyCount]) }}
        </p>
      </div>
      <Button
        variant="ghost"
        icon="x"
        :aria-label="__('Close')"
        @click="$emit('close')"
      />
    </div>

    <div class="px-4 pb-2">
      <TextInput
        ref="searchInput"
        v-model="query"
        type="search"
        :placeholder="__('Search widgets')"
        :debounce="150"
      >
        <template #prefix>
          <span
            class="lucide-search size-4 text-ink-gray-5"
            aria-hidden="true"
          />
        </template>
      </TextInput>
    </div>

    <div class="flex gap-1 overflow-x-auto px-4 pb-2">
      <button
        v-for="option in categoryOptions"
        :key="option.value"
        class="shrink-0 whitespace-nowrap rounded-full px-2.5 py-1 text-xs font-medium transition-colors"
        :class="
          category === option.value
            ? 'bg-surface-gray-10 text-ink-base'
            : 'bg-surface-gray-2 text-ink-gray-7 hover:bg-surface-gray-3'
        "
        @click="category = option.value"
      >
        {{ option.label }}
      </button>
    </div>

    <div class="min-h-0 flex-1 overflow-y-auto px-4 pb-6">
      <div
        v-if="loading && !catalog.widgets?.length"
        class="flex flex-col gap-2 pt-3"
      >
        <div
          v-for="index in 6"
          :key="index"
          class="h-16 animate-pulse rounded-lg bg-surface-gray-1"
        />
      </div>
      <div
        v-else-if="!groups.length"
        class="py-10 text-center text-sm text-ink-gray-5"
      >
        {{ __('No widget matches “{0}”', [query]) }}
      </div>
      <section v-for="group in groups" :key="group.category" class="pt-3">
        <h3
          class="mb-2 flex items-center gap-1.5 text-xs font-medium uppercase tracking-wide text-ink-gray-5"
        >
          <Icon :icon="categoryMeta(group.category).icon" class="size-3.5" />
          {{ categoryMeta(group.category).label }}
        </h3>
        <ul class="flex flex-col gap-2">
          <li v-for="widget in group.widgets" :key="widget.id">
            <div
              class="w-full rounded-lg border p-3 text-left transition-colors"
              :class="
                widget.unavailable
                  ? 'border-dashed border-outline-gray-2 bg-surface-gray-1'
                  : 'border-outline-gray-2 hover:border-outline-gray-4 hover:bg-surface-gray-1'
              "
            >
              <button
                class="flex w-full items-start gap-2.5 text-left disabled:cursor-not-allowed"
                :disabled="Boolean(widget.unavailable)"
                @click="$emit('add', widget)"
              >
                <span
                  class="mt-0.5 grid size-7 shrink-0 place-items-center rounded-md bg-surface-gray-2"
                >
                  <Icon
                    :icon="
                      widget.unavailable ? 'lock' : kindMeta(widget.kind).icon
                    "
                    class="size-3.5 text-ink-gray-6"
                  />
                </span>
                <span class="min-w-0 flex-1">
                  <span class="flex items-center gap-1.5">
                    <span
                      class="truncate text-sm font-medium"
                      :class="
                        widget.unavailable
                          ? 'text-ink-gray-5'
                          : 'text-ink-gray-8'
                      "
                    >
                      {{ widget.title }}
                    </span>
                    <span
                      v-if="widget.live"
                      class="shrink-0 rounded-full bg-surface-gray-2 px-1.5 text-2xs text-ink-gray-6"
                    >
                      {{ __('Now') }}
                    </span>
                    <span
                      v-if="used[widget.id]"
                      class="shrink-0 rounded-full bg-surface-blue-2 px-1.5 text-2xs text-ink-blue-8"
                      :title="__('Already on this dashboard')"
                    >
                      {{ used[widget.id] > 1 ? `✓ ×${used[widget.id]}` : '✓' }}
                    </span>
                  </span>
                  <span
                    class="mt-0.5 line-clamp-2 block text-xs text-ink-gray-5"
                  >
                    {{
                      widget.unavailable
                        ? widget.unavailable.message
                        : widget.description
                    }}
                  </span>
                </span>
                <span
                  v-if="!widget.unavailable"
                  class="lucide-plus mt-1 size-4 shrink-0 text-ink-gray-5"
                  aria-hidden="true"
                />
              </button>
              <button
                v-if="widget.unavailable?.feature && canSetUp"
                class="mt-2 inline-flex items-center gap-1 text-xs font-medium text-ink-gray-7 hover:text-ink-gray-9"
                @click="$emit('setup', widget.unavailable.feature)"
              >
                {{ __('Set up {0}', [widget.unavailable.feature.label]) }}
                <span class="lucide-arrow-right size-3" aria-hidden="true" />
              </button>
            </div>
          </li>
        </ul>
      </section>
    </div>
  </aside>
</template>

<script setup>
import Icon from '@/components/Icon.vue'
import {
  categoryMeta,
  kindMeta,
  layoutWidgets,
} from '@/components/Dashboard/meta'
import { groupByCategory, searchCatalog, usage } from '@/utils/dashboard'
import { TextInput } from 'frappe-ui'
import { computed, onMounted, ref } from 'vue'

const props = defineProps({
  catalog: { type: Object, default: () => ({ widgets: [], categories: [] }) },
  items: { type: Array, default: () => [] },
  canSetUp: { type: Boolean, default: false },
  loading: { type: Boolean, default: false },
})

defineEmits(['add', 'close', 'setup'])

const query = ref('')
const category = ref('')
const searchInput = ref(null)

const widgets = computed(() => [
  ...(props.catalog.widgets || []),
  ...layoutWidgets(),
])

const order = computed(() => [...(props.catalog.categories || []), 'layout'])

const readyCount = computed(
  () =>
    (props.catalog.widgets || []).filter((widget) => !widget.unavailable)
      .length,
)

const categoryOptions = computed(() => {
  const present = new Set(widgets.value.map((widget) => widget.category))
  return [
    { value: '', label: __('All') },
    ...order.value
      .filter((key) => present.has(key))
      .map((key) => ({ value: key, label: categoryMeta(key).label })),
  ]
})

// what the site can show first, what it could show once set up after
const groups = computed(() => {
  const found = searchCatalog(widgets.value, query.value, category.value)
  const ready = found.filter((widget) => !widget.unavailable)
  const locked = found.filter((widget) => widget.unavailable)
  return groupByCategory([...ready, ...locked], order.value)
})

const used = computed(() => usage(props.items))

onMounted(() => {
  searchInput.value?.el?.focus?.()
})
</script>
