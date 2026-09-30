<!--
  A food of the library, put right: its name in the centre's words, its group,
  its portion, on or off. A table's numbers stay the table's, shown with where
  they come from; the centre's own food has its numbers written here.
-->
<template>
  <Dialog v-model="show" :options="{ title: __('Food'), size: 'lg' }">
    <template #body-content>
      <div v-if="form" class="flex flex-col gap-3">
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
        <label class="flex items-center justify-between gap-3">
          <span class="flex min-w-0 flex-col">
            <span class="text-base text-ink-gray-8">
              {{ __('In the library') }}
            </span>
            <span class="text-p-sm text-ink-gray-5">
              {{
                __(
                  'Switched off, it is no longer offered; the plans that have it keep it.',
                )
              }}
            </span>
          </span>
          <Switch v-model="form.enabled" class="shrink-0" />
        </label>

        <template v-if="own">
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
        </template>
        <div
          v-else
          class="flex flex-col gap-1 rounded-md bg-surface-gray-2 px-3 py-2 text-p-sm text-ink-gray-7"
        >
          <span class="font-medium text-ink-gray-8">
            {{ __('Per 100 g, from {0}', [food.source]) }}
          </span>
          <span>{{ rigaValori(food, (text, args) => __(text, args)) }}</span>
          <span v-if="food.kcal_computed" class="text-ink-gray-6">
            {{
              __(
                'The table gives no energy: computed from the nutrients with the factors of the Regulation EU 1169/2011.',
              )
            }}
          </span>
          <span class="text-ink-gray-5">
            {{ food.name_in_source }}
            <template v-if="food.source_code">
              · {{ __('code {0}', [food.source_code]) }}
            </template>
          </span>
          <span v-if="food.source_note" class="text-ink-gray-5">
            {{ food.source_note }}
          </span>
        </div>
        <ErrorMessage :message="error" />
      </div>
    </template>
    <template #actions>
      <div class="dialog-footer flex justify-end gap-2">
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
import { rigaValori } from '@/utils/librerie'
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
const emit = defineEmits(['saved'])
const show = defineModel({ type: Boolean })

const form = ref(null)
const saving = ref(false)
const error = ref('')

const own = computed(() => (props.food?.source || 'Centre') === 'Centre')
const groupOptions = GRUPPI.map((g) => ({ label: __(g), value: g }))
const fields = [
  { key: 'kcal', label: __('kcal') },
  { key: 'protein_g', label: __('Proteins (g)') },
  { key: 'carbs_g', label: __('Carbohydrates (g)') },
  { key: 'fat_g', label: __('Fats (g)') },
  { key: 'fibre_g', label: __('Fibre (g)') },
]

watch(show, (open) => {
  if (!open || !props.food) return
  error.value = ''
  const food = props.food
  form.value = {
    food_name: food.food_name,
    food_group: food.food_group,
    portion_g: food.portion_g || '',
    enabled: Boolean(food.enabled),
    source_note: food.source_note || '',
    ...Object.fromEntries(fields.map(({ key }) => [key, food[key] ?? ''])),
  }
})

async function save() {
  saving.value = true
  error.value = ''
  try {
    await call('crm.clinica.librerie.save_food', {
      name: props.food.name,
      data: JSON.stringify({
        ...form.value,
        enabled: form.value.enabled ? 1 : 0,
      }),
    })
    toast.success(__('Saved'))
    emit('saved')
    show.value = false
  } catch (e) {
    error.value = e.messages?.join(' ') || e.message
  } finally {
    saving.value = false
  }
}
</script>
