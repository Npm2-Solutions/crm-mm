<!--
  The centre's libraries: the foods and the exercises its plans are written with.
  A food table comes in from a file (CIQUAL, BDA-IEO with the licence, CREA with
  the permission), exercises-dataset from its file or GitHub; here a name becomes
  the centre's own, a group is put right, an item is switched off. Imported again,
  a table brings its numbers, never over the centre's words.
-->
<template>
  <SettingsLayoutBase>
    <template #title>
      <h2 class="text-2xl-semibold text-ink-gray-9">{{ __('Libraries') }}</h2>
    </template>
    <template #description>
      <p class="text-p-base text-ink-gray-6">
        {{
          __(
            'The foods and exercises plans are written with. The numbers come from the tables; the names and groups are the centre’s.',
          )
        }}
      </p>
    </template>
    <template #header-actions>
      <Button
        class="shrink-0"
        variant="solid"
        icon-left="upload"
        :label="
          kind === 'Foods' ? __('Import a table') : __('Import exercises')
        "
        @click="openImport"
      />
    </template>
    <template #header-bottom>
      <div class="flex flex-col gap-3">
        <TabButtons v-model="kind" :buttons="kinds" class="w-fit" />
        <div class="flex flex-wrap items-center gap-2">
          <div class="min-w-48 flex-1">
            <FormControl
              v-model="filters.text"
              type="text"
              :placeholder="
                kind === 'Foods'
                  ? __('Search a food')
                  : __('Search an exercise')
              "
              :aria-label="__('Search')"
            />
          </div>
          <div class="w-44 max-md:flex-1">
            <FormControl
              v-model="filters.group"
              type="select"
              :options="groupOptions"
              :aria-label="kind === 'Foods' ? __('Group') : __('Body part')"
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
      </div>
    </template>
    <template #content>
      <div class="flex flex-col gap-4 pb-6">
        <div
          v-if="kind === 'Exercises' && data?.can_set_media"
          class="flex flex-col gap-2 rounded-lg border border-outline-gray-2 p-3"
        >
          <div class="flex flex-wrap items-end gap-2">
            <div class="min-w-60 flex-1">
              <FormControl
                v-model="media"
                :label="__('Exercise pictures from')"
                placeholder="https://"
              />
            </div>
            <Button
              class="shrink-0"
              :label="__('Save')"
              :loading="savingMedia"
              :disabled="media === (data.media_url || '')"
              @click="saveMedia"
            />
          </div>
          <span class="text-p-sm text-ink-gray-5">
            {{
              __(
                'Where the agency hosts the images/ and videos/ folders of exercises-dataset: one copy per server or a CDN, not one per site. Empty: no pictures.',
              )
            }}
          </span>
        </div>

        <p
          v-if="data && !data.rows.length"
          class="px-2 py-6 text-center text-p-base text-ink-gray-5"
        >
          {{
            anyFilter
              ? __('Nothing matches.')
              : kind === 'Foods'
                ? __(
                    'No foods yet: import a table, or add them while writing a plan.',
                  )
                : __(
                    'No exercises yet: import exercises-dataset, or add them while writing a plan.',
                  )
          }}
        </p>

        <div v-if="data?.rows.length" class="flex flex-col">
          <button
            v-for="row in rows"
            :key="row.name"
            type="button"
            class="flex items-center gap-3 rounded-md px-2 py-2 text-left hover:bg-surface-gray-2 focus-visible:bg-surface-gray-2 focus-visible:outline-none"
            @click="edit(row)"
          >
            <img
              v-if="kind === 'Exercises' && (row.animation || row.picture)"
              :src="row.picture || row.animation"
              alt=""
              class="size-10 shrink-0 rounded object-cover"
              loading="lazy"
            />
            <span class="flex min-w-0 flex-1 flex-col">
              <span
                class="truncate text-base"
                :class="row.enabled ? 'text-ink-gray-8' : 'text-ink-gray-5'"
              >
                {{ kind === 'Foods' ? row.food_name : row.exercise_name }}
              </span>
              <span class="truncate text-p-sm text-ink-gray-5">
                {{ describe(row) }}
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

        <p
          v-if="kind === 'Exercises' && data?.has_media"
          class="px-2 text-p-xs text-ink-gray-5"
        >
          {{
            __(
              'Animations and pictures of exercises-dataset © Gym visual — https://gymvisual.com/',
            )
          }}
        </p>

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
              <template v-if="entry.licence"> · {{ entry.licence }}</template>
            </span>
          </div>
        </section>
      </div>

      <FoodEditDialog
        v-model="foodDialog.show"
        :food="foodDialog.row"
        @saved="reload"
      />
      <ExerciseEditDialog
        v-model="exerciseDialog.show"
        :exercise="exerciseDialog.row"
        @saved="reload"
      />
      <FoodImportDialog v-model="importing.foods" @imported="reload" />
      <ExerciseImportDialog
        v-model="importing.exercises"
        :has-media="Boolean(data?.has_media)"
        @imported="reload"
      />
    </template>
  </SettingsLayoutBase>
</template>

<script setup>
import SettingsLayoutBase from '@/components/Layouts/SettingsLayoutBase.vue'
import ExerciseEditDialog from '@/components/Settings/Clinic/ExerciseEditDialog.vue'
import ExerciseImportDialog from '@/components/Settings/Clinic/ExerciseImportDialog.vue'
import FoodEditDialog from '@/components/Settings/Clinic/FoodEditDialog.vue'
import FoodImportDialog from '@/components/Settings/Clinic/FoodImportDialog.vue'
import { formatDate } from '@/utils'
import { FONTI } from '@/utils/librerie'
import { GRUPPI, PARTI } from '@/utils/piani'
import {
  Badge,
  Button,
  FormControl,
  TabButtons,
  call,
  debounce,
  toast,
} from 'frappe-ui'
import { computed, reactive, ref, watch } from 'vue'

const kinds = [
  { label: __('Foods'), value: 'Foods' },
  { label: __('Exercises'), value: 'Exercises' },
]
const kind = ref('Foods')
const filters = reactive({ text: '', group: '', source: '' })
const data = ref(null)
const rows = ref([])
const loadingMore = ref(false)

const anyFilter = computed(() =>
  Boolean(filters.text || filters.group || filters.source),
)

const groupOptions = computed(() => [
  {
    label: kind.value === 'Foods' ? __('Every group') : __('Every body part'),
    value: '',
  },
  ...(kind.value === 'Foods' ? GRUPPI : PARTI).map((g) => ({
    label: __(g),
    value: g,
  })),
])

const sourceOptions = computed(() => [
  { label: __('Every source'), value: '' },
  { label: __('The centre'), value: 'Centre' },
  ...(kind.value === 'Foods' ? FONTI : ['exercises-dataset']).map((s) => ({
    label: s,
    value: s,
  })),
])

function sourceLabel(source) {
  return !source || source === 'Centre' ? __('The centre') : source
}

function describe(row) {
  if (kind.value === 'Foods') {
    const parts = [__(row.food_group)]
    if (row.kcal !== null && row.kcal !== undefined)
      parts.push(__('{0} kcal/100 g', [row.kcal]))
    if (row.name_in_source && row.name_in_source !== row.food_name)
      parts.push(row.name_in_source)
    return parts.join(' · ')
  }
  return [row.body_part ? __(row.body_part) : '', row.equipment || '']
    .filter(Boolean)
    .join(' · ')
}

async function load(start = 0) {
  const result = await call('crm.clinica.librerie.get_library', {
    kind: kind.value,
    text: filters.text || null,
    group: filters.group || null,
    source: filters.source || null,
    start,
  })
  data.value = result
  rows.value = start ? [...rows.value, ...result.rows] : result.rows
  if (!start) media.value = result.media_url || ''
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
watch(kind, () => {
  Object.assign(filters, { text: '', group: '', source: '' })
  reload()
})
reload()

// ------------------------------------------------------------ editing

const foodDialog = reactive({ show: false, row: null })
const exerciseDialog = reactive({ show: false, row: null })

function edit(row) {
  const dialog = kind.value === 'Foods' ? foodDialog : exerciseDialog
  Object.assign(dialog, { show: true, row: { ...row } })
}

const importing = reactive({ foods: false, exercises: false })

function openImport() {
  if (kind.value === 'Foods') importing.foods = true
  else importing.exercises = true
}

// ------------------------------------------------------------ the agency's pictures

const media = ref('')
const savingMedia = ref(false)

async function saveMedia() {
  savingMedia.value = true
  try {
    await call('crm.clinica.librerie.save_media_url', {
      url: media.value || null,
    })
    toast.success(__('Saved'))
    await reload()
  } catch (e) {
    toast.error(e.messages?.join(' ') || e.message)
  } finally {
    savingMedia.value = false
  }
}
</script>
