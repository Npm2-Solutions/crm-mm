<!--
  One item of a plan, in one row, as its kind wants it: a food with its grams and
  the kcal they give; the portions of a food group; an exercise with its picture,
  sets and repetitions; a habit in words. What is said less often - what the
  patient may have instead, a note, so many times a week, an exercise's
  duration, rest and load - opens under the row with one tap, and is said in the
  row's line once written.
-->
<template>
  <div class="flex flex-col gap-2 rounded-md bg-surface-gray-1 px-2.5 py-2">
    <div class="flex min-w-0 flex-wrap items-center gap-2">
      <!-- a food: the library's name, its grams, what they give -->
      <template v-if="item.kind === CIBO">
        <div class="min-w-[12rem] flex-1">
          <LibraryPicker
            v-model="item.food"
            kind="food"
            :label="item.food_name"
            @picked="pickedFood"
          />
        </div>
        <div class="flex shrink-0 items-center gap-2">
          <div class="w-20">
            <FormControl
              v-model="item.quantity_g"
              type="number"
              inputmode="decimal"
              :aria-label="__('Grams')"
              :placeholder="__('Grams')"
            />
          </div>
          <span class="text-p-sm text-ink-gray-5">g</span>
          <span
            class="w-20 text-right text-p-sm tabular-nums text-ink-gray-7"
            :title="__('From the food tables')"
          >
            {{ kcal === null ? '–' : __('{0} kcal', [kcal]) }}
          </span>
        </div>
      </template>

      <!-- the portions of a food group -->
      <template v-else-if="item.kind === GRUPPO">
        <div class="min-w-[12rem] flex-1">
          <FormControl
            v-model="item.food_group"
            type="select"
            :options="groups"
            :aria-label="__('Group')"
          />
        </div>
        <div class="w-24 shrink-0">
          <FormControl
            v-model="item.portions"
            type="number"
            inputmode="decimal"
            :aria-label="__('Portions')"
            :placeholder="__('Portions')"
          />
        </div>
      </template>

      <!-- an exercise: its picture, its name, sets × repetitions -->
      <template v-else-if="item.kind === ESERCIZIO">
        <button
          type="button"
          class="flex min-w-[12rem] flex-1 items-center gap-2.5 rounded text-left focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-outline-gray-3"
          :aria-label="
            item.exercise
              ? __('Change the exercise: {0}', [item.exercise_name])
              : __('Choose')
          "
          @click="browsing = true"
        >
          <span
            class="flex size-11 shrink-0 items-center justify-center overflow-hidden rounded-md bg-white ring-1 ring-outline-gray-1"
          >
            <img
              v-if="picture && !rotta"
              :src="picture"
              alt=""
              loading="lazy"
              class="size-full object-contain"
              @error="rotta = true"
            />
            <span
              v-else
              class="lucide-dumbbell size-5 text-ink-gray-5"
              aria-hidden="true"
            />
          </span>
          <span class="flex min-w-0 flex-col">
            <span class="line-clamp-2 text-base text-ink-gray-8">
              {{ item.exercise_name || __('No exercise chosen') }}
            </span>
            <span
              v-if="item.exercise_detail?.body_part"
              class="truncate text-p-xs text-ink-gray-5"
            >
              {{ __(item.exercise_detail.body_part, null, 'Body part') }}
              <template v-if="item.exercise_detail.equipment">
                · {{ item.exercise_detail.equipment }}
              </template>
            </span>
          </span>
        </button>
        <div class="flex shrink-0 items-center gap-1.5">
          <div class="w-14">
            <FormControl
              v-model="item.sets"
              type="number"
              inputmode="numeric"
              :aria-label="__('Sets')"
              :placeholder="__('Sets')"
            />
          </div>
          <span class="text-ink-gray-5" aria-hidden="true">×</span>
          <div class="w-20">
            <FormControl
              v-model="item.reps"
              :aria-label="__('Repetitions')"
              :placeholder="__('Reps')"
            />
          </div>
        </div>
      </template>

      <!-- a habit, in words -->
      <div v-else class="min-w-[12rem] flex-1">
        <FormControl
          v-model="item.text"
          :aria-label="__('Habit')"
          :placeholder="__('For example: drink two litres of water')"
        />
      </div>

      <div class="ml-auto flex shrink-0 items-center">
        <Button
          variant="ghost"
          class="touch-target"
          :icon="open ? 'chevron-up' : 'more-horizontal'"
          :aria-label="__('More about this item')"
          :aria-expanded="open"
          @click="open = !open"
        />
        <Button
          variant="ghost"
          icon="x"
          class="touch-target"
          :aria-label="__('Remove')"
          @click="$emit('remove')"
        />
      </div>
    </div>

    <!-- what is written but folded away, said in a line -->
    <button
      v-if="!open && riassunto"
      type="button"
      class="truncate pl-0.5 text-left text-p-xs text-ink-gray-6"
      @click="open = true"
    >
      {{ riassunto }}
    </button>

    <div v-if="open" class="flex flex-col gap-2 pt-1">
      <div
        v-if="item.kind === ESERCIZIO"
        class="grid grid-cols-3 gap-2 max-md:grid-cols-1"
      >
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
      <FormControl
        v-if="item.kind === CIBO || item.kind === GRUPPO"
        v-model="item.alternatives"
        :label="__('Or instead')"
        :placeholder="__('Another food, how much')"
      />
      <div
        class="grid grid-cols-[minmax(0,1fr)_10rem] gap-2 max-md:grid-cols-1"
      >
        <FormControl v-model="item.note" :label="__('A note for the person')" />
        <FormControl
          v-model="item.times_per_week"
          type="select"
          :label="__('How often')"
          :options="weekly"
        />
      </div>
      <p
        v-if="
          item.kind === ESERCIZIO &&
          picture &&
          !rotta &&
          item.exercise_detail?.media_attribution
        "
        class="text-p-xs text-ink-gray-5"
      >
        {{ item.exercise_detail.media_attribution }}
      </p>
    </div>

    <LibraryBrowser
      v-if="opened"
      v-model="browsing"
      kind="exercise"
      :multiple="false"
      @choose="([row]) => scelto(row)"
    />
  </div>
</template>

<script setup>
import LibraryBrowser from '@/components/Plans/LibraryBrowser.vue'
import LibraryPicker from '@/components/Plans/LibraryPicker.vue'
import {
  CIBO,
  ESERCIZIO,
  GRUPPI,
  GRUPPO,
  grammiIniziali,
  nutrienti,
} from '@/utils/piani'
import { Button, FormControl } from 'frappe-ui'
import { computed, ref, watch } from 'vue'

defineEmits(['remove'])
const item = defineModel({ type: Object, required: true })

const groups = GRUPPI.map((g) => ({ label: __(g), value: g }))
// every time the moment comes, or so many times a week
const weekly = [
  { label: __('Every time'), value: '0' },
  ...[1, 2, 3, 4, 5, 6, 7].map((n) => ({
    label: __('{0} times a week', [n]),
    value: String(n),
  })),
]

// what is folded away opens with a tap
const open = ref(false)

// a food picked from the library brings its values for 100 g, and starts from
// its portion, or 100 g: a row of 0 kcal said nothing
function pickedFood(row) {
  item.value.food_name = row.food_name
  item.value.food_detail = row
  if (!Number(item.value.quantity_g))
    item.value.quantity_g = grammiIniziali(row)
}

const kcal = computed(() => {
  if (item.value.kind !== CIBO || !item.value.food) return null
  const conti = nutrienti([item.value], {
    [item.value.food]: item.value.food_detail,
  })
  return conti.missing.length ? null : conti.kcal
})

// an exercise picked from the library brings its picture and whose it is
function scelto(row) {
  item.value.exercise = row.name
  item.value.exercise_name = row.exercise_name
  item.value.exercise_detail = row
}

const browsing = ref(false)
// the library is mounted the first time it is browsed, and stays
const opened = ref(false)
watch(browsing, (aperto) => aperto && (opened.value = true))
const picture = computed(() => item.value.exercise_detail?.picture || '')
// a picture that did not load leaves its place to the exercise's mark
const rotta = ref(false)
watch(picture, () => (rotta.value = false))

// what is folded away and written, in one line
const riassunto = computed(() => {
  const voce = item.value
  const parti = []
  if (voce.kind === ESERCIZIO) {
    if (voce.duration) parti.push(voce.duration)
    if (voce.rest) parti.push(__('rest {0}', [voce.rest]))
    if (voce.load) parti.push(voce.load)
  }
  if (voce.alternatives) parti.push(__('Or instead: {0}', [voce.alternatives]))
  const volte = Number(voce.times_per_week)
  if (volte) parti.push(__('{0} times a week', [volte]))
  if (voce.note) parti.push(voce.note)
  return parti.join(' · ')
})
</script>
