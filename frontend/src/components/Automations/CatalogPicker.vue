<template>
  <Dialog v-model="show" :options="{ title, size: '3xl' }">
    <template #body-content>
      <div class="flex flex-col gap-4">
        <FormControl
          ref="searchInput"
          v-model="query"
          type="text"
          :placeholder="__('Search')"
          autocomplete="off"
        />
        <div
          v-for="category in visibleCategories"
          :key="category.name"
          class="flex flex-col gap-2"
        >
          <div
            class="flex items-center gap-1.5 text-xs font-medium uppercase tracking-wide text-ink-gray-5"
          >
            <FeatherIcon :name="category.icon" class="size-3.5" />
            {{ __(category.label) }}
          </div>
          <div class="grid gap-2 sm:grid-cols-2">
            <button
              v-for="entry in category.entries"
              :key="entry.key"
              class="flex items-start gap-2.5 rounded-lg border border-outline-gray-2 p-2.5 text-left transition-colors hover:border-outline-gray-3 hover:bg-surface-gray-1"
              @click="pick(entry)"
            >
              <div
                class="grid size-8 shrink-0 place-items-center rounded-md"
                :class="ICON_CLASSES[entry.theme] || ICON_CLASSES.gray"
              >
                <FeatherIcon :name="entry.icon" class="size-4" />
              </div>
              <div class="min-w-0">
                <div class="text-base font-medium text-ink-gray-8">
                  {{ __(entry.label) }}
                </div>
                <div class="text-sm text-ink-gray-5">
                  {{ __(entry.description || '') }}
                </div>
              </div>
            </button>
          </div>
        </div>
        <div
          v-if="!visibleCategories.length"
          class="py-6 text-center text-sm text-ink-gray-4"
        >
          {{ __('Nothing matches «{0}»', [query]) }}
        </div>
      </div>
    </template>
  </Dialog>
</template>

<script setup>
import { Dialog, FeatherIcon, FormControl } from 'frappe-ui'
import { computed, ref } from 'vue'
import { ICON_CLASSES } from '@/utils/automation'

const props = defineProps({
  title: { type: String, default: '' },
  categories: { type: Array, required: true },
  entries: { type: Array, required: true },
})

const emit = defineEmits(['select'])

const show = defineModel({ type: Boolean, default: false })
const query = ref('')

const matches = computed(() => {
  const needle = query.value.trim().toLowerCase()
  if (!needle) return props.entries
  return props.entries.filter((entry) =>
    [entry.label, entry.description, entry.key]
      .map((text) => __(text || '').toLowerCase())
      .some((text) => text.includes(needle)),
  )
})

const visibleCategories = computed(() =>
  props.categories
    .map((category) => ({
      ...category,
      entries: matches.value.filter(
        (entry) => entry.category === category.name,
      ),
    }))
    .filter((category) => category.entries.length),
)

function pick(entry) {
  emit('select', entry)
  show.value = false
  query.value = ''
}
</script>
