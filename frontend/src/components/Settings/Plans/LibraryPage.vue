<!--
  Copyright (c) 2026, NPM2 Solutions Srl and contributors
  For license information, please see license.txt

  A library the plans are written with, as a settings page: the one DottorCloud
  ships - the CRM's exercises, the clinic's foods - all there already, and the
  centre's own. Searched, filtered by group and by whose it is; each row switched
  off or on where it is, opened to be read (the library's) or put right (the
  centre's); a new one of the centre's added. Nobody imports, nobody changes the
  library. Each says where its rows come from and how they read (``library``),
  and keeps its own dialogs.
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
        <div class="w-44 max-md:flex-1">
          <FormControl
            v-model="filters.show"
            type="select"
            :options="showOptions"
            :aria-label="__('Show')"
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
          <!-- the whole row opens it; its switch, above the row's link, turns it
               off or on where it is -->
          <div
            v-for="row in rows"
            :key="row.name"
            class="relative flex items-center gap-3 rounded-md px-2 py-2 hover:bg-surface-gray-2"
          >
            <img
              v-if="
                library.thumbnail?.(row) &&
                !nonCaricate.has(library.thumbnail(row))
              "
              :src="library.thumbnail(row)"
              alt=""
              class="size-10 shrink-0 rounded object-cover"
              loading="lazy"
              @error="nonCaricate.add(library.thumbnail(row))"
            />
            <span
              v-else-if="library.thumbnail"
              class="flex size-10 shrink-0 items-center justify-center rounded bg-surface-gray-2 text-ink-gray-5"
              aria-hidden="true"
            >
              <span class="lucide-image-off size-4" />
            </span>
            <button
              type="button"
              class="flex min-w-0 flex-1 flex-col text-left after:absolute after:inset-0 after:rounded-md after:content-[''] focus-visible:outline-none focus-visible:after:ring-2 focus-visible:after:ring-outline-gray-3"
              @click="emit('edit', { ...row })"
            >
              <!-- the name read whole: two exercises cut were the same
                   «Abduzione dell'anca da seduto…» -->
              <span
                class="max-w-full break-words text-base"
                :class="row.enabled ? 'text-ink-gray-8' : 'text-ink-gray-5'"
              >
                {{ row[library.nameField] }}
              </span>
              <span class="max-w-full truncate text-p-sm text-ink-gray-5">
                {{ library.describe(row) }}
              </span>
            </button>
            <!-- what the centre added is the exception worth a mark; a
                 «Library» on every row of the library said nothing -->
            <Badge
              v-if="(row.source || 'Centre') === 'Centre'"
              class="shrink-0"
              variant="subtle"
              theme="blue"
              :label="__('The centre’s own')"
            />
            <Switch
              class="relative z-10 shrink-0"
              :model-value="Boolean(row.enabled)"
              :aria-label="row[library.nameField]"
              @update:model-value="(acceso) => accendi(row, acceso)"
            />
          </div>
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
      </div>
      <slot name="dialogs" :reload="reload" :aggiorna="aggiorna" :data="data" />
    </template>
  </SettingsLayoutBase>
</template>

<script setup>
import SettingsLayoutBase from '@/components/Layouts/SettingsLayoutBase.vue'
import {
  Badge,
  Button,
  FormControl,
  Switch,
  call,
  debounce,
  toast,
} from 'frappe-ui'
import { computed, reactive, ref, watch } from 'vue'

const props = defineProps({
  // title, description, endpoint, switchEndpoint, nameField, groups,
  // groupContext, everyGroup, groupLabel, sources (a name, or its value and
  // label), searchPlaceholder, newLabel, empty, describe(row), thumbnail(row)
  library: { type: Object, required: true },
})
const emit = defineEmits(['edit', 'new'])

// the filter's value for the rows switched off, whoever's they are
const SPENTI = 'switched-off'

const filters = reactive({ text: '', group: '', show: '' })
// a picture that did not load leaves its place to a quiet mark, never a broken one
const nonCaricate = reactive(new Set())
const data = ref(null)
const rows = ref([])
const loadingMore = ref(false)

const anyFilter = computed(() =>
  Boolean(filters.text || filters.group || filters.show),
)

const groupOptions = computed(() => [
  { label: props.library.everyGroup, value: '' },
  // a group's word read in its sense: «Back» is a body part, «Schiena», not «Indietro»
  ...props.library.groups.map((g) => ({
    label: __(g, null, props.library.groupContext),
    value: g,
  })),
])

// a source is a table's own name ("CIQUAL"), or a value with the words the
// centre reads ("exercises-dataset" is the library DottorCloud ships); one the
// site holds nothing from (a table a centre imported before the library came)
// is no choice: it showed «No results»
const sources = computed(() => {
  const presenti = data.value?.sources
  return props.library.sources
    .map((s) => (typeof s === 'string' ? { label: s, value: s } : s))
    .filter((s) => !presenti || presenti[s.value] || filters.show === s.value)
})

// what the list shows: all of it, the library's, the centre's own, or what was
// switched off
const showOptions = computed(() => [
  { label: __('All'), value: '' },
  ...sources.value,
  { label: __('The centre’s own'), value: 'Centre' },
  { label: __('Switched off', null, 'Library filter'), value: SPENTI },
])

async function load(start = 0) {
  const result = await call(props.library.endpoint, {
    text: filters.text || null,
    group: filters.group || null,
    source: filters.show && filters.show !== SPENTI ? filters.show : null,
    enabled: filters.show === SPENTI ? 0 : null,
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

// switched off or on where it is: the row shows it at once, and goes back if the
// server says no
async function accendi(row, acceso) {
  const prima = row.enabled
  row.enabled = acceso ? 1 : 0
  try {
    await call(props.library.switchEndpoint, {
      name: row.name,
      enabled: row.enabled,
    })
  } catch (e) {
    row.enabled = prima
    toast.error(e.messages?.join(' ') || e.message)
  }
}

// a row the dialog changed, in its place: the list keeps where it was
function aggiorna(riga) {
  const i = rows.value.findIndex((r) => r.name === riga.name)
  if (i >= 0) rows.value[i] = { ...rows.value[i], ...riga }
}

const search = debounce(reload, 300)
watch(() => filters.text, search)
watch(() => [filters.group, filters.show], reload)
reload()

defineExpose({ reload, aggiorna, data })
</script>
