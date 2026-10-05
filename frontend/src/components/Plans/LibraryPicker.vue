<!--
  A food or an exercise from the centre's library, searched on the server. What
  the library has not got is added from here: a food with its values from a
  table, an exercise with how it is done and a video of the centre's.
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
  />
  <Dialog
    v-model="adding.show"
    :options="{
      title: kind === 'food' ? __('A new food') : __('A new exercise'),
      size: 'md',
    }"
  >
    <template #body-content>
      <div class="flex flex-col gap-3">
        <FormControl v-model="adding.name" :label="__('Name')" />
        <template v-if="kind === 'food'">
          <FormControl
            v-model="adding.group"
            type="select"
            :label="__('Group')"
            :options="groupOptions"
          />
          <div class="grid grid-cols-2 gap-3">
            <FormControl
              v-model="adding.portion"
              type="number"
              :label="__('Portion (g)')"
            />
            <FormControl
              v-model="adding.kcal"
              type="number"
              :label="__('kcal per 100 g')"
            />
          </div>
          <div class="grid grid-cols-4 gap-3 max-md:grid-cols-2">
            <FormControl
              v-for="nutrient in macros"
              :key="nutrient.key"
              v-model="adding[nutrient.key]"
              type="number"
              :label="nutrient.label"
            />
          </div>
          <FormControl
            v-model="adding.source"
            :label="__('From which table')"
            :placeholder="__('For example CREA, or the label of the product')"
          />
        </template>
        <template v-else>
          <FormControl
            v-model="adding.part"
            type="select"
            :label="__('Body part')"
            :options="partOptions"
          />
          <FormControl
            v-model="adding.instructions"
            type="textarea"
            :label="__('How it is done')"
          />
          <FormControl
            v-model="adding.video"
            :label="__('Video (YouTube or Vimeo)')"
            placeholder="https://"
          />
        </template>
        <ErrorMessage :message="adding.error" />
      </div>
    </template>
    <template #actions>
      <div class="dialog-footer flex justify-end gap-2">
        <Button :label="__('Cancel')" @click="adding.show = false" />
        <Button
          variant="solid"
          :label="__('Add to the library')"
          :disabled="!adding.name.trim()"
          :loading="adding.busy"
          @click="add"
        />
      </div>
    </template>
  </Dialog>
</template>

<script setup>
import { GRUPPI, PARTI } from '@/utils/piani'
import {
  Button,
  Combobox,
  Dialog,
  ErrorMessage,
  FormControl,
  call,
  createResource,
  debounce,
} from 'frappe-ui'
import { computed, reactive, ref } from 'vue'

const props = defineProps({
  kind: { type: String, default: 'food' },
  modelValue: { type: String, default: null },
  // the name of what is chosen now, before any search
  label: { type: String, default: '' },
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
    if (row.portion_g) parts.push(__('portion {0} g', [row.portion_g]))
    if (row.kcal) parts.push(__('{0} kcal/100 g', [row.kcal]))
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
    row,
  }))
  // what is chosen stays among the options, so the button can name it
  if (props.modelValue && !rows.some((r) => r.value === props.modelValue)) {
    rows.unshift({
      label: props.label || props.modelValue,
      value: props.modelValue,
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

function pick(option) {
  if (!option || !option.row) return
  emit('update:modelValue', option.value)
  emit('picked', option.row)
}

const groupOptions = GRUPPI.map((g) => ({ label: __(g), value: g }))
const partOptions = PARTI.map((p) => ({
  label: __(p, null, 'Body part'),
  value: p,
}))

// grams per 100 g, as the table says: what a menu's totals are made of
const macros = [
  { key: 'protein_g', label: __('Proteins (g)') },
  { key: 'carbs_g', label: __('Carbohydrates (g)') },
  { key: 'fat_g', label: __('Fats (g)') },
  { key: 'fibre_g', label: __('Fibre (g)') },
]

const adding = reactive({
  show: false,
  name: '',
  group: GRUPPI[0],
  portion: '',
  kcal: '',
  protein_g: '',
  carbs_g: '',
  fat_g: '',
  fibre_g: '',
  source: '',
  part: PARTI[0],
  instructions: '',
  video: '',
  busy: false,
  error: '',
})

function openAdd(text) {
  Object.assign(adding, {
    show: true,
    name: text || '',
    portion: '',
    kcal: '',
    protein_g: '',
    carbs_g: '',
    fat_g: '',
    fibre_g: '',
    source: '',
    instructions: '',
    video: '',
    busy: false,
    error: '',
  })
}

async function add() {
  adding.busy = true
  adding.error = ''
  try {
    const row =
      props.kind === 'food'
        ? await call('crm.clinica.piani.add_food', {
            food_name: adding.name,
            food_group: adding.group,
            portion_g: adding.portion || null,
            kcal: adding.kcal === '' ? null : adding.kcal,
            ...Object.fromEntries(
              macros.map(({ key }) => [
                key,
                adding[key] === '' ? null : adding[key],
              ]),
            ),
            source_note: adding.source || null,
          })
        : await call('crm.piani.api.add_exercise', {
            exercise_name: adding.name,
            body_part: adding.part,
            instructions: adding.instructions || null,
            video_url: adding.video || null,
          })
    adding.show = false
    emit('update:modelValue', row.name)
    emit('picked', row)
    results.reload()
  } catch (e) {
    adding.error = e.messages?.join(' ') || e.message
  } finally {
    adding.busy = false
  }
}
</script>
