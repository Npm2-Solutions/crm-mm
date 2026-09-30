<!--
  Recipes for one meal of a menu: the assistant proposes which foods of the
  library go together and how to prepare them; the engine scales the grams to the
  meal's energy and counts every number from the tables. The nutritionist picks
  one, and it goes into the meal as their own - to change, save and publish.
-->
<template>
  <Dialog
    v-model="show"
    :options="{
      title: __('Recipes for {0}', [moment?.label || __('the meal')]),
      size: '3xl',
    }"
  >
    <template #body-content>
      <div class="flex flex-col gap-4">
        <p
          class="rounded-md bg-surface-gray-2 px-3 py-2 text-p-sm text-ink-gray-7"
        >
          {{
            __(
              'The assistant proposes recipes made of the library’s foods. The grams are scaled to the energy you set and every number comes from the food tables, not from the AI. Check each one: chosen, it goes into the meal as yours.',
            )
          }}
        </p>
        <div
          class="grid grid-cols-[10rem_minmax(0,1fr)] gap-3 max-md:grid-cols-1"
        >
          <FormControl
            v-model="kcal"
            type="number"
            :label="__('Energy (kcal)')"
            :placeholder="__('Any')"
          />
          <FormControl
            v-model="notes"
            :label="__('What to keep in mind')"
            :placeholder="
              __('For example: vegetarian, no lactose, quick to cook')
            "
          />
        </div>
        <Button
          class="w-fit"
          icon-left="lucide-sparkles"
          :label="recipes.length ? __('Propose others') : __('Propose')"
          :loading="busy === 'propose'"
          @click="propose"
        />
        <div
          v-if="busy === 'propose'"
          class="py-6 text-center text-p-sm text-ink-gray-5"
        >
          {{ __('The assistant is looking through the library…') }}
        </div>
        <div v-else-if="recipes.length" class="flex flex-col gap-3">
          <article
            v-for="(recipe, index) in recipes"
            :key="index"
            class="flex flex-col gap-2 rounded-lg border border-outline-gray-2 p-3"
          >
            <div class="flex flex-wrap items-start justify-between gap-2">
              <h4 class="min-w-0 text-base font-medium text-ink-gray-9">
                {{ recipe.title }}
              </h4>
              <Button
                class="shrink-0"
                variant="solid"
                :label="__('Use this')"
                :loading="busy === 'use-' + index"
                @click="use(recipe, index)"
              />
            </div>
            <p
              v-if="recipe.method"
              class="whitespace-pre-line text-p-sm text-ink-gray-7"
            >
              {{ recipe.method }}
            </p>
            <ul class="flex flex-col gap-0.5 text-p-sm text-ink-gray-8">
              <li
                v-for="item in recipe.items"
                :key="item.food"
                class="flex justify-between gap-3"
              >
                <span class="min-w-0">{{ item.food_name }}</span>
                <span class="shrink-0 text-ink-gray-6">
                  {{ item.quantity_g }} g
                </span>
              </li>
            </ul>
            <p class="text-p-xs text-ink-gray-5">
              {{ nutrientsLine(recipe.nutrients) }}
            </p>
          </article>
        </div>
        <ErrorMessage :message="error" />
      </div>
    </template>
    <template #actions>
      <div class="dialog-footer flex justify-end">
        <Button
          :label="event ? __('Discard them') : __('Close')"
          :loading="busy === 'discard'"
          @click="close"
        />
      </div>
    </template>
  </Dialog>
</template>

<script setup>
import { rigaNutrienti } from '@/utils/piani'
import { Button, Dialog, ErrorMessage, FormControl, call } from 'frappe-ui'
import { ref, watch } from 'vue'

const props = defineProps({
  plan: { type: String, default: null },
  // the meal: its key and its name
  moment: { type: Object, default: null },
  // the energy the meal has left, from the targets: a suggestion
  suggestedKcal: { type: [Number, String], default: '' },
})
const emit = defineEmits(['used'])
const show = defineModel({ type: Boolean })

const nutrientsLine = (n) => rigaNutrienti(n, (text, args) => __(text, args))

const kcal = ref('')
const notes = ref('')
const recipes = ref([])
const event = ref(null)
const busy = ref('')
const error = ref('')

watch(show, (open) => {
  if (!open) return
  kcal.value = props.suggestedKcal ? String(props.suggestedKcal) : ''
  notes.value = ''
  recipes.value = []
  event.value = null
  error.value = ''
  busy.value = ''
})

async function discardPrevious() {
  if (!event.value) return
  const previous = event.value
  event.value = null
  await call('crm.clinica.menu.discard_recipes', { event: previous }).catch(
    () => {},
  )
}

async function propose() {
  busy.value = 'propose'
  error.value = ''
  await discardPrevious()
  recipes.value = []
  try {
    const answer = await call('crm.clinica.menu.propose_recipes', {
      plan: props.plan,
      moment: props.moment.key,
      kcal: kcal.value || null,
      notes: notes.value || null,
    })
    event.value = answer.error ? null : answer.event
    recipes.value = answer.recipes || []
    if (answer.error) {
      error.value = __('The assistant did not answer: {0}', [answer.error])
    }
  } catch (e) {
    error.value = e.messages?.join(' ') || e.message
  } finally {
    busy.value = ''
  }
}

async function use(recipe, index) {
  busy.value = 'use-' + index
  error.value = ''
  try {
    const plan = await call('crm.clinica.menu.use_recipe', {
      event: event.value,
      moment: props.moment.key,
      recipe: JSON.stringify(recipe),
    })
    event.value = null
    emit('used', plan)
    show.value = false
  } catch (e) {
    error.value = e.messages?.join(' ') || e.message
  } finally {
    busy.value = ''
  }
}

async function close() {
  busy.value = 'discard'
  await discardPrevious()
  busy.value = ''
  show.value = false
}
</script>
