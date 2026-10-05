<!--
  Copyright (c) 2026, NPM2 Solutions Srl and contributors
  For license information, please see license.txt

  A food of the library, to read and to switch off or on: its numbers for 100 g
  and where they come from, never changed by the centre. One of the centre's
  own, written here: its name, its group, its portion, its numbers, on or off.
-->
<template>
  <Dialog v-model="show" :options="{ title, size: 'lg' }">
    <template #body-content>
      <!-- the library's: what it is, and whether the plans offer it -->
      <div v-if="food && !own" class="flex flex-col gap-3">
        <span class="text-p-base text-ink-gray-7">
          {{ __(food.food_group) }}
        </span>
        <div
          class="flex flex-col gap-1 rounded-md bg-surface-gray-2 px-3 py-2 text-p-sm text-ink-gray-7"
        >
          <span class="font-medium text-ink-gray-8">
            {{ __('Per 100 g, from {0}', [food.source]) }}
          </span>
          <span>{{
            rigaValori(food, (text, args) => __(text, args), lingua)
          }}</span>
          <span v-if="food.kcal_computed" class="text-ink-gray-6">
            {{
              __(
                'The table gives no energy: computed from the nutrients with the factors of the Regulation EU 1169/2011.',
              )
            }}
          </span>
          <!-- the table's own words for it, and its code there: where to
               find it, in the table's language -->
          <span class="text-ink-gray-5">
            {{ __('In {0}: {1}', [food.source, food.name_in_source]) }}
            <template v-if="food.source_code">
              · {{ __('code {0}', [food.source_code]) }}
            </template>
          </span>
          <span v-if="food.source_note" class="text-ink-gray-5">
            {{ food.source_note }}
          </span>
        </div>
        <SettingsRow
          class="!px-0"
          :label="__('Offered in the plans')"
          :description="
            __(
              'Switched off, it is no longer offered; the plans that have it keep it.',
            )
          "
        >
          <Switch
            :model-value="acceso"
            :disabled="switching"
            @update:model-value="switchIt"
          />
        </SettingsRow>
        <ErrorMessage :message="error" />
      </div>

      <!-- the centre's own: written here -->
      <div v-else-if="form" class="flex flex-col gap-3">
        <FormControl v-model="form.food_name" :label="__('Name')" />
        <div class="grid grid-cols-2 gap-3 max-md:grid-cols-1">
          <FormControl
            v-model="form.food_group"
            type="select"
            :label="__('Group')"
            :options="groupOptions"
          />
          <FormControl
            v-model="form.portion_g"
            type="number"
            :label="__('Portion (g)')"
          />
        </div>
        <span class="text-sm font-medium text-ink-gray-7">
          {{ __('Per 100 g') }}
        </span>
        <div class="grid grid-cols-5 gap-3 max-md:grid-cols-2">
          <FormControl
            v-for="field in fields"
            :key="field.key"
            v-model="form[field.key]"
            type="number"
            :label="field.label"
          />
        </div>
        <FormControl
          v-model="form.source_note"
          :label="__('From which table')"
          :placeholder="__('For example CREA, or the label of the product')"
        />
        <SettingsRow
          class="!px-0"
          :label="__('Offered in the plans')"
          :description="
            __(
              'Switched off, it is no longer offered; the plans that have it keep it.',
            )
          "
        >
          <Switch v-model="form.enabled" />
        </SettingsRow>
        <ErrorMessage :message="error" />
      </div>
    </template>
    <template #actions>
      <div v-if="food && !own" class="dialog-footer flex justify-end gap-2">
        <Button :label="__('Close')" @click="show = false" />
      </div>
      <div v-else class="dialog-footer flex justify-end gap-2">
        <Button :label="__('Cancel')" @click="show = false" />
        <Button
          variant="solid"
          :label="__('Save')"
          :loading="saving"
          :disabled="!form?.food_name?.trim()"
          @click="save"
        />
      </div>
    </template>
  </Dialog>
</template>

<script setup>
import SettingsRow from '@/components/Settings/SettingsRow.vue'
import { rigaValori } from '@/utils/librerie'
import { appLocale } from '@/utils/locale'
import { GRUPPI } from '@/utils/piani'
import {
  Button,
  Dialog,
  ErrorMessage,
  FormControl,
  Switch,
  call,
  toast,
} from 'frappe-ui'
import { computed, ref, watch } from 'vue'

const props = defineProps({ food: { type: Object, default: null } })
// saved: a new one, the list is read again; changed: one row, in its place
const emit = defineEmits(['saved', 'changed'])
const show = defineModel({ type: Boolean })

const form = ref(null)
const saving = ref(false)
const switching = ref(false)
// the library's: offered or not, as the last switch left it
const acceso = ref(false)
const error = ref('')

const own = computed(() => (props.food?.source || 'Centre') === 'Centre')
// the numbers as the reader writes them («27,1» in Italian)
const lingua = appLocale() || 'it'
const title = computed(() => {
  if (!props.food) return __('New food')
  return own.value ? __('Food') : props.food.food_name
})
const groupOptions = computed(() => [
  // a new food: its group chosen, never guessed
  ...(props.food ? [] : [{ label: __('Choose the group'), value: '' }]),
  ...GRUPPI.map((g) => ({ label: __(g), value: g })),
])
const fields = [
  { key: 'kcal', label: __('kcal') },
  { key: 'protein_g', label: __('Proteins (g)') },
  { key: 'carbs_g', label: __('Carbohydrates (g)') },
  { key: 'fat_g', label: __('Fats (g)') },
  { key: 'fibre_g', label: __('Fibre (g)') },
]

watch(show, (open) => {
  if (!open) return
  error.value = ''
  const food = props.food || { food_group: '', enabled: 1 }
  acceso.value = Boolean(food.enabled)
  form.value = {
    food_name: food.food_name || '',
    food_group: food.food_group,
    portion_g: food.portion_g || '',
    enabled: Boolean(food.enabled),
    source_note: food.source_note || '',
    ...Object.fromEntries(fields.map(({ key }) => [key, food[key] ?? ''])),
  }
})

// the library's, switched off or on from here as from its row
async function switchIt(si) {
  switching.value = true
  error.value = ''
  try {
    const fatto = await call('crm.clinica.librerie.switch_food', {
      name: props.food.name,
      enabled: si ? 1 : 0,
    })
    acceso.value = Boolean(fatto.enabled)
    emit('changed', fatto)
  } catch (e) {
    error.value = e.messages?.join(' ') || e.message
  } finally {
    switching.value = false
  }
}

async function save() {
  saving.value = true
  error.value = ''
  try {
    const riga = await call('crm.clinica.librerie.save_food', {
      name: props.food?.name || null,
      data: JSON.stringify({
        ...form.value,
        enabled: form.value.enabled ? 1 : 0,
      }),
    })
    toast.success(__('Saved'))
    if (props.food?.name) emit('changed', riga)
    else emit('saved')
    show.value = false
  } catch (e) {
    error.value = e.messages?.join(' ') || e.message
  } finally {
    saving.value = false
  }
}
</script>
