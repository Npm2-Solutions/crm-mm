<!--
  One item of a plan, as its kind wants it: a food and how much, with what the
  patient may have instead; the portions of a food group; an exercise with its
  sets; a habit in words. Any of them may ask for so many times a week.
-->
<template>
  <div class="flex flex-col gap-2 rounded-md bg-surface-gray-1 p-3">
    <div class="flex items-center justify-between gap-2">
      <Badge variant="subtle" theme="gray" :label="__(item.kind)" />
      <Button
        variant="ghost"
        icon="x"
        class="touch-target shrink-0"
        :aria-label="__('Remove')"
        @click="$emit('remove')"
      />
    </div>

    <template v-if="item.kind === CIBO">
      <div class="grid grid-cols-[minmax(0,1fr)_7rem] gap-2 max-md:grid-cols-1">
        <LibraryPicker
          v-model="item.food"
          kind="food"
          :label="item.food_name"
          @picked="(row) => Object.assign(item, pickedFood(row))"
        />
        <FormControl
          v-model="item.quantity_g"
          type="number"
          :placeholder="__('Grams')"
        />
      </div>
      <FormControl
        v-model="item.alternatives"
        :placeholder="__('Or instead: another food, how much')"
      />
    </template>

    <div
      v-else-if="item.kind === GRUPPO"
      class="grid grid-cols-[minmax(0,1fr)_7rem] gap-2 max-md:grid-cols-1"
    >
      <FormControl v-model="item.food_group" type="select" :options="groups" />
      <FormControl
        v-model="item.portions"
        type="number"
        :placeholder="__('Portions')"
      />
    </div>

    <template v-else-if="item.kind === ESERCIZIO">
      <LibraryPicker
        v-model="item.exercise"
        kind="exercise"
        :label="item.exercise_name"
        @picked="(row) => (item.exercise_name = row.exercise_name)"
      />
      <div class="grid grid-cols-5 gap-2 max-md:grid-cols-2">
        <FormControl
          v-model="item.sets"
          type="number"
          inputmode="numeric"
          :label="__('Sets')"
        />
        <FormControl v-model="item.reps" :label="__('Repetitions')" />
        <FormControl
          v-model="item.duration"
          :label="__('Duration')"
          placeholder="30 s"
        />
        <FormControl
          v-model="item.rest"
          :label="__('Rest')"
          placeholder="60 s"
        />
        <FormControl
          v-model="item.load"
          :label="__('Load')"
          placeholder="5 kg"
        />
      </div>
    </template>

    <FormControl
      v-else
      v-model="item.text"
      :placeholder="__('For example: drink two litres of water')"
    />

    <div class="grid grid-cols-[minmax(0,1fr)_9rem] gap-2 max-md:grid-cols-1">
      <FormControl
        v-model="item.note"
        :placeholder="__('A note for the person')"
      />
      <FormControl
        v-model="item.times_per_week"
        type="select"
        :options="weekly"
      />
    </div>
  </div>
</template>

<script setup>
import LibraryPicker from '@/components/Plans/LibraryPicker.vue'
import { CIBO, ESERCIZIO, GRUPPI, GRUPPO } from '@/utils/piani'
import { Badge, Button, FormControl } from 'frappe-ui'

defineEmits(['remove'])
const item = defineModel({ type: Object, required: true })

const groups = GRUPPI.map((g) => ({ label: __(g), value: g }))

// a food picked from the library brings its values for 100 g: the plan's
// totals are counted from them
function pickedFood(row) {
  return { food_name: row.food_name, food_detail: row }
}
// every time the moment comes, or so many times a week
const weekly = [
  { label: __('Every time'), value: '0' },
  ...[1, 2, 3, 4, 5, 6, 7].map((n) => ({
    label: __('{0} times a week', [n]),
    value: String(n),
  })),
]
</script>
