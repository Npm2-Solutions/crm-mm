<!--
  Copyright (c) 2026, NPM2 Solutions Srl and contributors
  For license information, please see license.txt

  The library a plan is written with, to browse: the exercises with their
  pictures, or the foods with their values, searched by name and filtered - a
  body part and an equipment, a food group - each choice saying how many it
  holds. A page at a time, «Show more» for the next. Several are chosen at once
  and go in the moment together; one is chosen when an item changes its own. An
  exercise opens to be read whole - its animation, its muscles, how it is done -
  before it is chosen. What the library has not got is added from here.
-->
<template>
  <Dialog v-model="show" :options="{ size: '5xl' }">
    <template #body-title>
      <div class="flex min-w-0 flex-col gap-0.5">
        <h3 class="text-2xl font-semibold text-ink-gray-9">
          {{
            kind === 'food'
              ? __('Choose the foods')
              : __('Choose the exercises')
          }}
        </h3>
        <p v-if="moment" class="text-p-sm text-ink-gray-6">
          {{ __('For «{0}»', [moment]) }}
        </p>
      </div>
    </template>
    <template #body-content>
      <!-- one exercise, read whole -->
      <div v-if="detail" class="flex flex-col gap-4">
        <Button
          class="w-fit"
          variant="ghost"
          icon-left="chevron-left"
          :label="__('Back to the list')"
          @click="detail = null"
        />
        <div
          class="grid grid-cols-[minmax(0,16rem)_minmax(0,1fr)] gap-5 max-md:grid-cols-1"
        >
          <div
            class="flex aspect-square w-full items-center justify-center overflow-hidden rounded-lg bg-white ring-1 ring-outline-gray-1"
          >
            <img
              v-if="figura(detail)"
              :src="figura(detail)"
              alt=""
              class="size-full object-contain"
              @error="rotte.add(figura(detail))"
            />
            <span
              v-else
              class="lucide-dumbbell size-10 text-ink-gray-4"
              aria-hidden="true"
            />
          </div>
          <div class="flex min-w-0 flex-col gap-3">
            <div class="flex flex-col gap-1">
              <h4 class="text-xl font-semibold text-ink-gray-9">
                {{ detail.exercise_name }}
              </h4>
              <p class="text-p-sm text-ink-gray-6">{{ describe(detail) }}</p>
            </div>
            <dl
              v-if="detail.primary_muscles || detail.secondary_muscles"
              class="grid grid-cols-[auto_minmax(0,1fr)] gap-x-3 gap-y-1 text-p-sm"
            >
              <template v-if="detail.primary_muscles">
                <dt class="text-ink-gray-5">{{ __('Muscles') }}</dt>
                <dd class="text-ink-gray-8">{{ detail.primary_muscles }}</dd>
              </template>
              <template v-if="detail.secondary_muscles">
                <dt class="text-ink-gray-5">{{ __('Also') }}</dt>
                <dd class="text-ink-gray-8">{{ detail.secondary_muscles }}</dd>
              </template>
            </dl>
            <p
              v-if="detail.instructions"
              class="whitespace-pre-line text-p-base text-ink-gray-8"
            >
              {{ detail.instructions }}
            </p>
            <a
              v-if="detail.video_url"
              :href="detail.video_url"
              target="_blank"
              rel="noopener"
              class="w-fit text-p-sm text-ink-gray-7 underline"
            >
              {{ __('The video') }}
            </a>
            <p
              v-if="detail.media_attribution && figura(detail)"
              class="text-p-xs text-ink-gray-5"
            >
              {{ detail.media_attribution }}
            </p>
          </div>
        </div>
      </div>

      <!-- the library -->
      <div v-else class="flex flex-col gap-3">
        <FormControl
          v-model="text"
          type="text"
          v-bind="tastiera('cerca')"
          :placeholder="
            kind === 'food'
              ? __('Search a food: pasta, apple, yogurt…')
              : __('Search an exercise: squat, plank, stretching…')
          "
          :aria-label="__('Search')"
        />

        <!-- the first filter as choices in a row, scrolling sideways on a phone -->
        <div
          v-if="facets[mainFacet]?.length"
          class="-mx-1 flex gap-1.5 overflow-x-auto px-1 pb-1"
          role="group"
          :aria-label="kind === 'food' ? __('Group') : __('Body part')"
        >
          <button
            v-for="choice in [{ value: '', count: null }, ...facets[mainFacet]]"
            :key="choice.value || 'all'"
            type="button"
            class="touch-target shrink-0 rounded-full border px-3 py-1 text-sm"
            :class="
              filters[mainFacet] === choice.value
                ? 'border-transparent bg-surface-gray-10 text-ink-white hover:bg-surface-gray-9'
                : 'border-outline-gray-2 text-ink-gray-7 hover:bg-surface-gray-2'
            "
            :aria-pressed="filters[mainFacet] === choice.value"
            @click="filters[mainFacet] = choice.value"
          >
            {{ choice.value ? facetLabel(mainFacet, choice.value) : __('All') }}
            <span v-if="choice.count" class="opacity-70">
              {{ choice.count }}
            </span>
          </button>
        </div>
        <div
          v-if="kind === 'exercise' && facets.equipment?.length"
          class="w-64 max-md:w-full"
        >
          <FormControl
            v-model="filters.equipment"
            type="select"
            :options="equipmentOptions"
            :aria-label="__('Equipment')"
          />
        </div>

        <p
          v-if="kind === 'exercise' && data && !data.has_media"
          class="rounded-md bg-surface-gray-2 px-3 py-2 text-p-sm text-ink-gray-7"
        >
          {{
            __(
              'The library’s pictures are not on the server yet: they arrive by themselves within a few hours. The exercises can be chosen already.',
            )
          }}
        </p>

        <div
          v-if="loading && !rows.length"
          class="py-10 text-center text-p-sm text-ink-gray-5"
        >
          {{ __('Loading…') }}
        </div>
        <div
          v-else-if="data && !rows.length"
          class="flex flex-col items-center gap-3 py-10 text-center"
        >
          <p class="text-p-base text-ink-gray-6">
            {{ __('Nothing matches.') }}
          </p>
          <Button
            icon-left="plus"
            :label="__('Add «{0}» to the library', [text])"
            :disabled="!text.trim()"
            @click="adding = true"
          />
        </div>

        <ul
          v-else
          class="grid grid-cols-[repeat(auto-fill,minmax(9.5rem,1fr))] gap-3"
        >
          <li v-for="row in rows" :key="row.name" class="relative">
            <button
              type="button"
              class="flex h-full w-full flex-col overflow-hidden rounded-lg border text-left focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-outline-gray-3"
              :class="
                chosen.has(row.name)
                  ? 'border-transparent ring-2 ring-[var(--brand-action)]'
                  : 'border-outline-gray-2 hover:border-outline-gray-3'
              "
              :aria-pressed="multiple ? chosen.has(row.name) : undefined"
              @click="toggle(row)"
            >
              <span
                v-if="kind === 'exercise'"
                class="flex aspect-square w-full items-center justify-center bg-white"
              >
                <img
                  v-if="thumbnail(row)"
                  :src="thumbnail(row)"
                  alt=""
                  loading="lazy"
                  class="size-full object-contain"
                  @error="rotte.add(thumbnail(row))"
                />
                <span
                  v-else
                  class="lucide-dumbbell size-8 text-ink-gray-4"
                  aria-hidden="true"
                />
              </span>
              <span class="flex min-w-0 flex-1 flex-col gap-0.5 p-2.5">
                <span
                  class="line-clamp-2 text-p-sm font-medium text-ink-gray-8"
                >
                  {{ name(row) }}
                </span>
                <span class="line-clamp-2 text-p-xs text-ink-gray-5">
                  {{ describe(row) }}
                </span>
                <!-- what is used comes first, and says so -->
                <span
                  v-if="usato(row)"
                  class="mt-0.5 flex items-center gap-1 text-p-xs text-ink-gray-6"
                >
                  <span class="lucide-history size-3" aria-hidden="true" />
                  {{ usato(row) }}
                </span>
              </span>
            </button>
            <span
              v-if="chosen.has(row.name)"
              class="pointer-events-none absolute right-2 top-2 flex size-6 items-center justify-center rounded-full bg-[var(--brand-action)] text-ink-white"
              aria-hidden="true"
            >
              <span class="lucide-check size-4" />
            </span>
            <!-- read it whole before choosing it -->
            <button
              v-if="kind === 'exercise'"
              type="button"
              class="touch-target absolute left-2 top-2 flex size-7 items-center justify-center rounded-full bg-surface-white/90 text-ink-gray-7 shadow-sm hover:bg-surface-white"
              :aria-label="__('How it is done: {0}', [row.exercise_name])"
              @click="detail = row"
            >
              <span class="lucide-info size-4" aria-hidden="true" />
            </button>
          </li>
        </ul>

        <div
          v-if="rows.length"
          class="flex flex-wrap items-center justify-between gap-2"
        >
          <span class="text-p-sm text-ink-gray-5">
            {{ __('{0} of {1}', [rows.length, data.total]) }}
          </span>
          <Button
            v-if="rows.length < data.total"
            :label="__('Show more')"
            :loading="loading"
            @click="load(true)"
          />
        </div>
        <p v-if="credit" class="text-p-xs text-ink-gray-5">{{ credit }}</p>
        <ErrorMessage :message="error" />
      </div>
      <LibraryAddDialog
        v-model="adding"
        :kind="kind"
        :name="text"
        @added="added"
      />
    </template>
    <template #actions>
      <div
        class="dialog-footer flex flex-wrap items-center justify-between gap-2"
      >
        <Button
          variant="ghost"
          icon-left="plus"
          :label="kind === 'food' ? __('A new food') : __('A new exercise')"
          @click="adding = true"
        />
        <div class="flex gap-2">
          <Button
            v-if="detail && kind === 'exercise'"
            :variant="multiple && chosen.has(detail.name) ? 'subtle' : 'solid'"
            :label="
              multiple && chosen.has(detail.name)
                ? __('Chosen')
                : __('Choose it')
            "
            @click="toggle(detail, true)"
          />
          <Button
            v-if="multiple"
            variant="solid"
            :disabled="!chosen.size"
            :label="chosen.size ? __('Add {0}', [chosen.size]) : __('Add')"
            @click="done"
          />
        </div>
      </div>
    </template>
  </Dialog>
</template>

<script setup>
import LibraryAddDialog from '@/components/Plans/LibraryAddDialog.vue'
import { tastiera } from '@/utils/tastiera'
import {
  Button,
  Dialog,
  ErrorMessage,
  FormControl,
  call,
  debounce,
} from 'frappe-ui'
import { computed, reactive, ref, watch } from 'vue'

const props = defineProps({
  // 'exercise' or 'food'
  kind: { type: String, default: 'exercise' },
  // several go in a moment at once; one replaces an item's own
  multiple: { type: Boolean, default: true },
  // the moment they go in, named over the list
  moment: { type: String, default: '' },
})
const emit = defineEmits(['choose'])
const show = defineModel({ type: Boolean })

const URL = {
  exercise: 'crm.piani.api.browse_exercises',
  food: 'crm.clinica.piani.browse_foods',
}
const mainFacet = computed(() =>
  props.kind === 'food' ? 'food_group' : 'body_part',
)

const text = ref('')
const filters = reactive({ body_part: '', equipment: '', food_group: '' })
const data = ref(null)
const rows = ref([])
const facets = ref({})
const loading = ref(false)
const error = ref('')
const chosen = reactive(new Map())
const detail = ref(null)
const adding = ref(false)
// the pictures that did not load leave their place to the exercise's mark
const rotte = reactive(new Set())

watch(
  show,
  (open) => {
    if (!open) return
    reset()
  },
  // mounted the first time it opens, already open
  { immediate: true },
)

function reset() {
  text.value = ''
  Object.assign(filters, { body_part: '', equipment: '', food_group: '' })
  chosen.clear()
  detail.value = null
  load()
}

async function load(more = false) {
  loading.value = true
  error.value = ''
  try {
    const params =
      props.kind === 'food'
        ? { text: text.value, group: filters.food_group || null }
        : {
            text: text.value,
            body_part: filters.body_part || null,
            equipment: filters.equipment || null,
          }
    const page = await call(URL[props.kind], {
      ...params,
      start: more ? rows.value.length : 0,
    })
    data.value = page
    rows.value = more ? [...rows.value, ...page.rows] : page.rows
    facets.value = page.facets || {}
  } catch (e) {
    error.value = e.messages?.join(' ') || e.message
  } finally {
    loading.value = false
  }
}

const search = debounce(() => load(), 250)
watch(text, search)
watch(
  () => [filters.body_part, filters.equipment, filters.food_group],
  () => load(),
)

function facetLabel(facet, value) {
  return facet === 'body_part' ? __(value, null, 'Body part') : __(value)
}

const equipmentOptions = computed(() => [
  { label: __('Any equipment'), value: '' },
  ...(facets.value.equipment || []).map((f) => ({
    label: `${f.value} (${f.count})`,
    value: f.value,
  })),
])

function name(row) {
  return props.kind === 'food' ? row.food_name : row.exercise_name
}

function describe(row) {
  if (props.kind === 'food') {
    const parts = [__(row.food_group)]
    if (row.kcal) parts.push(__('{0} kcal/100 g', [row.kcal]))
    if (row.portion_g) parts.push(__('portion {0} g', [row.portion_g]))
    return parts.join(' · ')
  }
  return [
    row.body_part ? __(row.body_part, null, 'Body part') : '',
    row.equipment || '',
  ]
    .filter(Boolean)
    .join(' · ')
}

// how often it is in the plans: one's own first, then the centre's
function usato(row) {
  const { mine = 0, all = 0 } = row.uses || {}
  if (mine)
    return mine === 1
      ? __('In one of your plans')
      : __('In {0} of your plans', [mine])
  if (all)
    return all === 1
      ? __('In one plan of the centre')
      : __('In {0} plans of the centre', [all])
  return ''
}

// the still picture in the list, the animation when it is read whole
function thumbnail(row) {
  return row.picture && !rotte.has(row.picture) ? row.picture : null
}
function figura(row) {
  const animation = row.animation && !rotte.has(row.animation) && row.animation
  return animation || thumbnail(row)
}

// whose the library's pictures are, under the list that shows them
const credit = computed(
  () =>
    rows.value.find((row) => thumbnail(row) && row.media_attribution)
      ?.media_attribution || '',
)

function toggle(row, fromDetail = false) {
  if (!props.multiple) {
    emit('choose', [row])
    show.value = false
    return
  }
  if (chosen.has(row.name)) chosen.delete(row.name)
  else chosen.set(row.name, row)
  if (fromDetail) detail.value = null
}

function added(row) {
  // what was added goes in with the others chosen
  rows.value = [row, ...rows.value]
  toggle(row)
}

function done() {
  emit('choose', [...chosen.values()])
  show.value = false
}
</script>
