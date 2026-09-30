<!--
  A diet's shopping list, to give the patient: the foods of the days ahead with
  how much to buy, an exchange diet's portions by group. The sums come from the
  server, from the plan's grams; here they are rounded up as a person buys them,
  and copied as words to paste in a message.
-->
<template>
  <Dialog v-model="show" :options="{ title: __('Shopping list'), size: 'xl' }">
    <template #body-content>
      <div class="flex flex-col gap-4">
        <div class="grid grid-cols-2 gap-3 max-md:grid-cols-1">
          <FormControl v-model="from" type="date" :label="__('From')" />
          <FormControl
            v-model="days"
            type="select"
            :label="__('For')"
            :options="dayOptions"
          />
        </div>
        <p v-if="list" class="text-p-sm text-ink-gray-6">
          {{
            list.days === list.asked
              ? __('{0} days, from {1} to {2}.', [
                  list.days,
                  formatDate(list.from, 'D MMM'),
                  formatDate(list.until, 'D MMM'),
                ])
              : __(
                  '{0} days of the plan between {1} and {2}: the others are outside its period.',
                  [
                    list.days,
                    formatDate(list.from, 'D MMM'),
                    formatDate(list.until, 'D MMM'),
                  ],
                )
          }}
        </p>
        <div v-if="loading" class="py-6 text-center text-p-sm text-ink-gray-5">
          {{ __('Loading…') }}
        </div>
        <template v-else-if="list">
          <section
            v-for="group in groups"
            :key="group.group"
            class="flex flex-col gap-1"
          >
            <h4 class="text-sm font-medium text-ink-gray-7">
              {{ __(group.group) }}
            </h4>
            <div
              v-for="row in group.items"
              :key="row.food"
              class="flex items-baseline justify-between gap-3 border-b border-outline-gray-1 py-1.5 last:border-0"
            >
              <span class="flex min-w-0 flex-col">
                <span class="text-p-base text-ink-gray-8">
                  {{ row.food_name }}
                </span>
                <span v-if="how(row)" class="text-p-xs text-ink-gray-5">
                  {{ how(row) }}
                </span>
              </span>
              <span class="shrink-0 text-p-base text-ink-gray-8">
                {{ quantitaDaComprare(row.grams, appLocale()) || __('to buy') }}
              </span>
            </div>
          </section>
          <section v-if="list.groups.length" class="flex flex-col gap-1">
            <h4 class="text-sm font-medium text-ink-gray-7">
              {{ __('To choose in the group') }}
            </h4>
            <div
              v-for="group in list.groups"
              :key="group.food_group"
              class="flex items-baseline justify-between gap-3 border-b border-outline-gray-1 py-1.5 last:border-0"
            >
              <span class="text-p-base text-ink-gray-8">
                {{ __(group.food_group) }}
              </span>
              <span class="shrink-0 text-p-base text-ink-gray-8">
                {{ __('{0} portions', [group.portions]) }}
              </span>
            </div>
          </section>
          <p
            v-if="!list.foods.length && !list.groups.length"
            class="text-p-base text-ink-gray-5"
          >
            {{ __('Nothing to buy in these days.') }}
          </p>
        </template>
        <ErrorMessage :message="error" />
      </div>
    </template>
    <template #actions>
      <div class="dialog-footer flex justify-end gap-2">
        <Button
          icon-left="copy"
          :label="__('Copy')"
          :disabled="!list || (!list.foods.length && !list.groups.length)"
          @click="copy"
        />
        <Button variant="solid" :label="__('Done')" @click="show = false" />
      </div>
    </template>
  </Dialog>
</template>

<script setup>
import { copyToClipboard, formatDate } from '@/utils'
import { appLocale } from '@/utils/locale'
import {
  GIORNI_SPESA,
  comeSiArriva,
  perGruppo,
  quantitaDaComprare,
  testoDellaSpesa,
} from '@/utils/piani'
import { Button, Dialog, ErrorMessage, FormControl, call } from 'frappe-ui'
import { computed, ref, watch } from 'vue'

const props = defineProps({ plan: { type: String, default: null } })
const show = defineModel({ type: Boolean })

const from = ref('')
const days = ref('7')
const list = ref(null)
const loading = ref(false)
const error = ref('')

const dayOptions = GIORNI_SPESA.map((n) => ({
  label: n === 7 ? __('A week') : __('{0} weeks', [n / 7]),
  value: String(n),
}))
const groups = computed(() => perGruppo(list.value?.foods))

async function load() {
  if (!props.plan) return
  loading.value = true
  error.value = ''
  try {
    list.value = await call('crm.clinica.piani.shopping_list', {
      name: props.plan,
      start: from.value || null,
      days: Number(days.value),
    })
    if (!from.value) from.value = list.value.from
  } catch (e) {
    error.value = e.messages?.join(' ') || e.message
  } finally {
    loading.value = false
  }
}

watch(show, (open) => {
  if (!open) return
  from.value = ''
  days.value = '7'
  list.value = null
  load()
})
watch([from, days], ([day], [before]) => {
  // the first answer fills the date: that is not a change to ask again for
  if (show.value && !(before === '' && day === list.value?.from)) load()
})

function how(row) {
  return comeSiArriva(row, (text, args) => __(text, args))
}

function copy() {
  // the CRM's own copy: the clipboard where the page allows it, else the old way
  copyToClipboard(testoDellaSpesa(list.value, (s, a) => __(s, a), appLocale()))
}
</script>
