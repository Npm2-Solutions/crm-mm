<!--
  Copyright (c) 2026, NPM2 Solutions Srl and contributors
  For license information, please see license.txt

  What the library has not got, added while a plan is written: a food with its
  values for 100 g from a table, an exercise with how it is done and a video of
  the centre's. The entry added is handed back, ready to go in the plan.
-->
<template>
  <Dialog
    v-model="show"
    :options="{
      title: kind === 'food' ? __('A new food') : __('A new exercise'),
      size: 'md',
    }"
  >
    <template #body-content>
      <div class="flex flex-col gap-3">
        <FormControl v-model="form.name" :label="__('Name')" />
        <template v-if="kind === 'food'">
          <FormControl
            v-model="form.group"
            type="select"
            :label="__('Group')"
            :options="groupOptions"
          />
          <div class="grid grid-cols-2 gap-3">
            <FormControl
              v-model="form.portion"
              type="number"
              :label="__('Portion (g)')"
            />
            <FormControl
              v-model="form.kcal"
              type="number"
              :label="__('kcal per 100 g')"
            />
          </div>
          <div class="grid grid-cols-4 gap-3 max-md:grid-cols-2">
            <FormControl
              v-for="nutrient in macros"
              :key="nutrient.key"
              v-model="form[nutrient.key]"
              type="number"
              :label="nutrient.label"
            />
          </div>
          <FormControl
            v-model="form.source"
            :label="__('From which table')"
            :placeholder="__('For example CREA, or the label of the product')"
          />
        </template>
        <template v-else>
          <FormControl
            v-model="form.part"
            type="select"
            :label="__('Body part')"
            :options="partOptions"
          />
          <FormControl
            v-model="form.instructions"
            type="textarea"
            :label="__('How it is done')"
          />
          <FormControl
            v-model="form.video"
            :label="__('Video (YouTube or Vimeo)')"
            placeholder="https://"
          />
        </template>
        <ErrorMessage :message="form.error" />
      </div>
    </template>
    <template #actions>
      <div class="dialog-footer flex justify-end gap-2">
        <Button :label="__('Cancel')" @click="show = false" />
        <Button
          variant="solid"
          :label="__('Add to the library')"
          :disabled="!form.name.trim()"
          :loading="form.busy"
          @click="add"
        />
      </div>
    </template>
  </Dialog>
</template>

<script setup>
import { GRUPPI, PARTI } from '@/utils/piani'
import { Button, Dialog, ErrorMessage, FormControl, call } from 'frappe-ui'
import { reactive, watch } from 'vue'

const props = defineProps({
  kind: { type: String, default: 'food' },
  // the words typed in the search, the name to start from
  name: { type: String, default: '' },
})
const emit = defineEmits(['added'])
const show = defineModel({ type: Boolean })

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

const form = reactive({})

watch(show, (open) => {
  if (!open) return
  Object.assign(form, {
    name: props.name || '',
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
})

async function add() {
  form.busy = true
  form.error = ''
  try {
    const row =
      props.kind === 'food'
        ? await call('crm.clinica.piani.add_food', {
            food_name: form.name,
            food_group: form.group,
            portion_g: form.portion || null,
            kcal: form.kcal === '' ? null : form.kcal,
            ...Object.fromEntries(
              macros.map(({ key }) => [
                key,
                form[key] === '' ? null : form[key],
              ]),
            ),
            source_note: form.source || null,
          })
        : await call('crm.piani.api.add_exercise', {
            exercise_name: form.name,
            body_part: form.part,
            instructions: form.instructions || null,
            video_url: form.video || null,
          })
    show.value = false
    emit('added', row)
  } catch (e) {
    form.error = e.messages?.join(' ') || e.message
  } finally {
    form.busy = false
  }
}
</script>
