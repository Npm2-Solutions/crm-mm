<!--
  A library the plans are written with, as a settings page: searched, filtered
  by group and source, a row opened to be put right, imports listed with who
  declared which licence. The CRM's exercises use it (a library DottorCloud
  ships: no import, the centre adds its own), and so does a module for its own
  library - the clinic's foods, imported from a table: each says where its rows
  come from and how they read (``library``), and keeps its own dialogs.
-->
<template>
  <SettingsLayoutBase>
    <template #title>
      <h2 class="text-2xl-semibold text-ink-gray-9">{{ library.title }}</h2>
    </template>
    <template #description>
      <p class="text-p-base text-ink-gray-6">{{ library.description }}</p>
    </template>
    <template #header-actions>
      <Button
        v-if="library.newLabel"
        class="shrink-0"
        variant="solid"
        icon-left="plus"
        :label="library.newLabel"
        @click="emit('new')"
      />
      <Button
        v-if="library.importLabel"
        class="shrink-0"
        variant="solid"
        icon-left="upload"
        :label="library.importLabel"
        @click="emit('import')"
      />
    </template>
    <template #header-bottom>
      <div class="flex flex-wrap items-center gap-2">
        <div class="min-w-48 flex-1">
          <FormControl
            v-model="filters.text"
            type="text"
            :placeholder="library.searchPlaceholder"
            :aria-label="__('Search')"
          />
        </div>
        <div class="w-56 max-md:flex-1">
          <FormControl
            v-model="filters.group"
            type="select"
            :options="groupOptions"
            :aria-label="library.groupLabel"
          />
        </div>
        <div class="w-40 max-md:flex-1">
          <FormControl
            v-model="filters.source"
            type="select"
            :options="sourceOptions"
            :aria-label="__('Source')"
          />
        </div>
      </div>
    </template>
    <template #content>
      <div class="flex flex-col gap-4 pb-6">
        <slot name="before" :data="data" :reload="reload" />

        <p
          v-if="data && !data.rows.length"
          class="px-2 py-6 text-center text-p-base text-ink-gray-5"
        >
          {{ anyFilter ? __('Nothing matches.') : library.empty }}
        </p>

        <div v-if="data?.rows.length" class="flex flex-col">
          <button
            v-for="row in rows"
            :key="row.name"
            type="button"
            class="flex items-center gap-3 rounded-md px-2 py-2 text-left hover:bg-surface-gray-2 focus-visible:bg-surface-gray-2 focus-visible:outline-none"
            @click="emit('edit', { ...row })"
          >
            <img
              v-if="library.thumbnail?.(row)"
              :src="library.thumbnail(row)"
              alt=""
              class="size-10 shrink-0 rounded object-cover"
              loading="lazy"
            />
            <span class="flex min-w-0 flex-1 flex-col">
              <span
                class="truncate text-base"
                :class="row.enabled ? 'text-ink-gray-8' : 'text-ink-gray-5'"
              >
                {{ row[library.nameField] }}
              </span>
              <span class="truncate text-p-sm text-ink-gray-5">
                {{ library.describe(row) }}
              </span>
            </span>
            <span class="flex shrink-0 items-center gap-2">
              <Badge
                v-if="!row.enabled"
                variant="subtle"
                theme="gray"
                :label="__('Off')"
              />
              <Badge
                variant="subtle"
                :theme="(row.source || 'Centre') === 'Centre' ? 'blue' : 'gray'"
                :label="sourceLabel(row.source)"
              />
            </span>
          </button>
          <div class="flex items-center justify-between gap-2 px-2 pt-2">
            <span class="text-p-sm text-ink-gray-5">
              {{ __('{0} of {1}', [rows.length, data.total]) }}
            </span>
            <Button
              v-if="rows.length < data.total"
              :label="__('Show more')"
              :loading="loadingMore"
              @click="more"
            />
          </div>
        </div>

        <slot name="after" :data="data" />

        <section
          v-if="data?.imports?.length"
          class="flex flex-col gap-2 border-t border-outline-gray-1 px-2 pt-4"
        >
          <h3 class="text-base-semibold text-ink-gray-8">
            {{ __('Imports') }}
          </h3>
          <div
            v-for="entry in data.imports"
            :key="entry.name"
            class="flex flex-col gap-0.5 text-p-sm"
          >
            <span class="text-ink-gray-8">
              {{ entry.attribution || entry.source }}
              <span class="text-ink-gray-5">
                · {{ formatDate(entry.imported_on, 'D MMM YYYY, HH:mm') }} ·
                {{ entry.imported_by }}
              </span>
            </span>
            <span class="text-ink-gray-5">
              {{
                __('{0} added, {1} updated, {2} rows not read', [
                  entry.created_count,
                  entry.updated_count,
                  entry.skipped_count,
                ])
              }}
              <template v-if="entry.licence">
                · {{ __(entry.licence) }}</template
              >
            </span>
          </div>
        </section>
      </div>
      <slot name="dialogs" :reload="reload" :data="data" />
    </template>
  </SettingsLayoutBase>
</template>

<script setup>
import SettingsLayoutBase from '@/components/Layouts/SettingsLayoutBase.vue'
import { formatDate } from '@/utils'
import { Badge, Button, FormControl, call, debounce, toast } from 'frappe-ui'
import { computed, reactive, ref, watch } from 'vue'

const props = defineProps({
  // title, description, endpoint, nameField, groups, everyGroup, groupLabel,
  // sources (a name, or its value and label), searchPlaceholder, newLabel or
  // importLabel, empty, describe(row), thumbnail(row)
  library: { type: Object, required: true },
})
const emit = defineEmits(['edit', 'new', 'import'])

const filters = reactive({ text: '', group: '', source: '' })
const data = ref(null)
const rows = ref([])
const loadingMore = ref(false)

const anyFilter = computed(() =>
  Boolean(filters.text || filters.group || filters.source),
)

const groupOptions = computed(() => [
  { label: props.library.everyGroup, value: '' },
  ...props.library.groups.map((g) => ({ label: __(g), value: g })),
])

// a source is a table's own name ("CIQUAL"), or a value with the words the
// centre reads ("exercises-dataset" is the library DottorCloud ships)
const sources = computed(() =>
  props.library.sources.map((s) =>
    typeof s === 'string' ? { label: s, value: s } : s,
  ),
)

const sourceOptions = computed(() => [
  { label: __('Every source'), value: '' },
  { label: __('The centre'), value: 'Centre' },
  ...sources.value,
])

function sourceLabel(source) {
  if (!source || source === 'Centre') return __('The centre')
  return sources.value.find((s) => s.value === source)?.label || source
}

async function load(start = 0) {
  const result = await call(props.library.endpoint, {
    text: filters.text || null,
    group: filters.group || null,
    source: filters.source || null,
    start,
  })
  data.value = result
  rows.value = start ? [...rows.value, ...result.rows] : result.rows
}

function reload() {
  return load(0).catch((e) => toast.error(e.messages?.join(' ') || e.message))
}

async function more() {
  loadingMore.value = true
  try {
    await load(rows.value.length)
  } finally {
    loadingMore.value = false
  }
}

const search = debounce(reload, 300)
watch(() => filters.text, search)
watch(() => [filters.group, filters.source], reload)
reload()

defineExpose({ reload, data })
</script>
