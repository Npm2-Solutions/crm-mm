<!--
  Copyright (c) 2026, NPM2 Solutions Srl and contributors
  For license information, please see license.txt

  The cash closing at the reception desk (crm/invoicing/cassa.py): what the day
  collected by way of paying and by who issued it, the credit notes that gave
  money back, the cash the drawer should hold; the cash counted, the difference,
  and the closing once saved. A day closed is counted again the same way.
-->
<template>
  <Dialog v-model="show" :options="{ title: __('Cash closing'), size: 'xl' }">
    <template #body-content>
      <div v-if="!conti" class="flex justify-center py-10">
        <LoaderMark />
      </div>
      <div v-else class="flex flex-col gap-5">
        <p class="text-p-base text-ink-gray-6">
          {{ formatDate(conti.date, 'dddd D MMMM YYYY') }}
        </p>
        <!-- the day at a glance: on a phone one short row -->
        <div class="cassa-numeri dc-stat-row grid grid-cols-3 gap-3">
          <StatTile
            :label="__('Collected')"
            :value="formatEuro(conti.collected)"
            blocco
          />
          <StatTile
            :label="__('Given back')"
            :value="formatEuro(conti.refunded)"
          />
          <StatTile
            :label="__('Cash expected')"
            :value="formatEuro(conti.expected_cash)"
          />
        </div>

        <section class="flex flex-col gap-2">
          <h3 class="text-base font-medium text-ink-gray-8">
            {{ __('By payment method') }}
          </h3>
          <p v-if="!conti.methods.length" class="text-p-base text-ink-gray-5">
            {{ __('Nothing collected on this day.') }}
          </p>
          <div
            v-else
            class="divide-y divide-outline-gray-1 rounded-lg border border-outline-gray-2 px-4"
          >
            <div
              v-for="voce in conti.methods"
              :key="voce.method"
              class="flex items-start justify-between gap-3 py-2.5"
            >
              <span class="flex min-w-0 flex-col">
                <span class="text-base text-ink-gray-8">{{ voce.name }}</span>
                <span class="text-p-sm text-ink-gray-5">
                  {{
                    voce.count === 1
                      ? __('1 invoice')
                      : __('{0} invoices', [voce.count])
                  }}
                  <template v-if="voce.refunded">
                    ·
                    {{ __('{0} given back', [formatEuro(voce.refunded)]) }}
                  </template>
                </span>
              </span>
              <span class="shrink-0 text-base tabular-nums text-ink-gray-8">
                {{ formatEuro(voce.net) }}
              </span>
            </div>
          </div>
        </section>

        <section v-if="conti.by_user.length" class="flex flex-col gap-2">
          <h3 class="text-base font-medium text-ink-gray-8">
            {{ __('By who issued them') }}
          </h3>
          <div
            class="divide-y divide-outline-gray-1 rounded-lg border border-outline-gray-2 px-4"
          >
            <div
              v-for="chi in conti.by_user"
              :key="chi.user"
              class="flex items-center justify-between gap-3 py-2.5"
            >
              <span class="min-w-0 truncate text-base text-ink-gray-8">
                {{ chi.full_name }}
              </span>
              <span class="shrink-0 text-base tabular-nums text-ink-gray-8">
                {{ formatEuro(chi.total) }}
              </span>
            </div>
          </div>
        </section>

        <!-- what the drawer holds, counted by hand -->
        <section class="flex flex-col gap-3">
          <FormControl
            v-model="contati"
            type="number"
            step="0.01"
            min="0"
            :label="__('Cash counted in the drawer')"
          />
          <p v-if="Number(contati) < 0" class="text-p-base text-ink-amber-7">
            {{ __('The cash counted cannot be below zero') }}
          </p>
          <p
            v-else-if="frase"
            class="text-p-base"
            :class="tono === 'green' ? 'text-ink-green-7' : 'text-ink-amber-7'"
          >
            {{ frase }}
          </p>
          <FormControl
            v-model="nota"
            type="textarea"
            :rows="2"
            :label="__('Note')"
            :placeholder="__('What explains a difference, if any')"
          />
          <p v-if="conti.closing" class="text-p-sm text-ink-gray-6">
            {{
              __('Closed by {0} at {1}', [
                conti.closing.closed_by_name,
                formatDate(conti.closing.closed_on, 'HH:mm'),
              ])
            }}
          </p>
        </section>
        <ErrorMessage :message="errore" />
      </div>
    </template>
    <template #actions>
      <div class="dialog-footer flex justify-end gap-2">
        <Button :label="__('Cancel')" @click="show = false" />
        <Button
          variant="solid"
          :label="conti?.closing ? __('Close it again') : __('Close the cash')"
          :disabled="!conti || differenza === null"
          :loading="chiudendo"
          @click="chiudi"
        />
      </div>
    </template>
  </Dialog>
</template>

<script setup>
import LoaderMark from '@/components/Espresso/LoaderMark.vue'
import StatTile from '@/components/Espresso/StatTile.vue'
import { formatDate } from '@/utils'
import {
  differenzaDiCassa,
  fraseDellaDifferenza,
  tonoDellaDifferenza,
} from '@/utils/cassa'
import { formatEuro } from '@/utils/invoicing'
import {
  Button,
  Dialog,
  ErrorMessage,
  FormControl,
  call,
  toast,
} from 'frappe-ui'
import { computed, ref, watch } from 'vue'

const props = defineProps({
  // the day the desk shows; nothing is today
  date: { type: String, default: null },
})
const show = defineModel({ type: Boolean })

const conti = ref(null)
const contati = ref('')
const nota = ref('')
const errore = ref('')
const chiudendo = ref(false)

function prendi(dati) {
  conti.value = dati
  contati.value = dati.closing ? dati.closing.counted_cash : ''
  nota.value = dati.closing?.note || ''
}

// asked each time it opens: a payment may have been marked meanwhile
watch(
  show,
  async (aperto) => {
    if (!aperto) return
    errore.value = ''
    conti.value = null
    try {
      prendi(await call('crm.api.oggi.get_cash_summary', { date: props.date }))
    } catch (e) {
      errore.value = e.messages?.join(' ') || e.message
    }
  },
  { immediate: true },
)

const differenza = computed(() =>
  differenzaDiCassa(contati.value, conti.value?.expected_cash),
)
const frase = computed(() =>
  fraseDellaDifferenza(
    differenza.value,
    (testo, valori) => __(testo, valori),
    formatEuro,
  ),
)
const tono = computed(() => tonoDellaDifferenza(differenza.value))

async function chiudi() {
  chiudendo.value = true
  errore.value = ''
  try {
    prendi(
      await call('crm.api.oggi.close_cash_day', {
        date: conti.value.date,
        counted_cash: contati.value,
        note: nota.value,
      }),
    )
    toast.success(__('The cash is closed'))
  } catch (e) {
    errore.value = e.messages?.join(' ') || e.message
  } finally {
    chiudendo.value = false
  }
}
</script>

<style scoped>
/* amounts in euros are wider than the desk's counts: on a phone they get the
   room of a third of the screen, and wrap rather than spill */
@media (max-width: 767px), (max-height: 499px) and (pointer: coarse) {
  .cassa-numeri :deep(.dc-stat__value) {
    font-size: 16px;
    overflow-wrap: anywhere;
  }
}
</style>
