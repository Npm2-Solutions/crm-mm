<!--
  A food or an exercise from the centre's library, searched on the server. What
  the library has not got is added from here: a food with its values from a
  table, an exercise with how it is done and a video of the centre's. An
  exercise shows its picture, and the library's pictures whose they are.
-->
<template>
  <Combobox
    trigger="button"
    class="w-full"
    :model-value="modelValue"
    :options="options"
    :query="query"
    :filterable="false"
    :loading="results.loading"
    :placeholder="
      kind === 'food' ? __('Choose a food') : __('Choose an exercise')
    "
    @update:query="search"
    @update:selected-option="pick"
  >
    <template v-if="kind === 'exercise'" #item-prefix="{ item }">
      <img
        v-if="item.picture && !rotte.has(item.picture)"
        :src="item.picture"
        alt=""
        loading="lazy"
        class="size-8 shrink-0 rounded bg-surface-gray-2 object-cover"
        @error="rotte.add(item.picture)"
      />
      <!-- the slot draws every row's start: «Add to the library» keeps its plus -->
      <span
        v-else-if="item.type === 'custom'"
        class="lucide-plus size-4 shrink-0 text-ink-gray-6"
        aria-hidden="true"
      />
      <span
        v-else
        class="lucide-dumbbell size-4 shrink-0 text-ink-gray-5"
        aria-hidden="true"
      />
    </template>
    <template v-if="credito" #footer>
      <p class="px-2.5 py-1.5 text-p-xs text-ink-gray-5">{{ credito }}</p>
    </template>
  </Combobox>
  <LibraryAddDialog
    v-model="adding.show"
    :kind="kind"
    :name="adding.name"
    @added="added"
  />
</template>

<script setup>
import LibraryAddDialog from '@/components/Plans/LibraryAddDialog.vue'
import { appLocale } from '@/utils/locale'
import { numeroDelleTabelle } from '@/utils/piani'
import { Combobox, createResource, debounce } from 'frappe-ui'
import { computed, reactive, ref } from 'vue'

const props = defineProps({
  kind: { type: String, default: 'food' },
  modelValue: { type: String, default: null },
  // the name of what is chosen now, before any search, and its picture
  label: { type: String, default: '' },
  picture: { type: String, default: '' },
})
const emit = defineEmits(['update:modelValue', 'picked'])

const query = ref('')
const results = createResource({
  url:
    props.kind === 'food'
      ? 'crm.clinica.piani.search_foods'
      : 'crm.piani.api.search_exercises',
  makeParams: () => ({ text: query.value }),
  auto: true,
})

const search = debounce((text) => {
  query.value = text || ''
  results.reload()
}, 250)

function describe(row) {
  if (props.kind === 'food') {
    const parts = [__(row.food_group)]
    if (row.portion_g)
      parts.push(
        __('portion {0} g', [numeroDelleTabelle(row.portion_g, appLocale())]),
      )
    if (row.kcal)
      parts.push(
        __('{0} kcal/100 g', [numeroDelleTabelle(row.kcal, appLocale())]),
      )
    // where the numbers come from: a table, or the centre
    if (row.source && row.source !== 'Centre') parts.push(row.source)
    return parts.join(' · ')
  }
  return [
    row.body_part ? __(row.body_part, null, 'Body part') : '',
    row.equipment || '',
  ]
    .filter(Boolean)
    .join(' · ')
}

const options = computed(() => {
  const rows = (results.data || []).map((row) => ({
    label: props.kind === 'food' ? row.food_name : row.exercise_name,
    value: row.name,
    description: describe(row),
    picture: row.picture || null,
    row,
  }))
  // what is chosen stays among the options, so the button can name it
  if (props.modelValue && !rows.some((r) => r.value === props.modelValue)) {
    rows.unshift({
      label: props.label || props.modelValue,
      value: props.modelValue,
      picture: props.picture || null,
    })
  }
  return [
    ...rows,
    {
      type: 'custom',
      key: 'add',
      label: __('Add to the library'),
      icon: 'plus',
      onClick: ({ query: text }) => openAdd(text),
    },
  ]
})

// the pictures that did not load leave their place to the exercise's mark
const rotte = reactive(new Set())

// the library's pictures say whose they are, under the list that shows them
const credito = computed(
  () =>
    (results.data || []).find((row) => row.picture && row.media_attribution)
      ?.media_attribution || '',
)

function pick(option) {
  if (!option || !option.row) return
  emit('update:modelValue', option.value)
  emit('picked', option.row)
}

const adding = reactive({ show: false, name: '' })

function openAdd(text) {
  Object.assign(adding, { show: true, name: text || '' })
}

function added(row) {
  emit('update:modelValue', row.name)
  emit('picked', row)
  results.reload()
}
</script>
