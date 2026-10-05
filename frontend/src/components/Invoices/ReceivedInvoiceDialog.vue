<!--
  Copyright (c) 2026, NPM2 Solutions Srl and contributors
  For license information, please see license.txt

  One invoice a supplier sent: who, what, how much of it is VAT, by when; its
  lines as its XML says them. What the desk does with it - seen, passed to the
  accountant, disputed with the reason, paid - and the PDF to read it by, asked
  of Itala the first time (crm/invoicing/ricevute.py).
-->
<template>
  <Dialog v-model="aperta" :options="{ title: titolo, size: 'xl' }">
    <template #body-content>
      <div v-if="vista" class="flex flex-col gap-5">
        <div class="flex flex-wrap items-center gap-2">
          <Badge
            :theme="statoRicevuta(vista.status, __).theme"
            :label="statoRicevuta(vista.status, __).label"
          />
          <Badge
            v-if="scadenza"
            :theme="scadenza.theme"
            :label="scadenza.label"
          />
          <span class="text-p-sm text-ink-gray-6">
            {{
              [
                vista.supplier_tax_id &&
                  __('VAT number {0}', [vista.supplier_tax_id]),
                vista.document_number,
                vista.document_date &&
                  dayjs(vista.document_date).format('DD/MM/YYYY'),
              ]
                .filter(Boolean)
                .join(' · ')
            }}
          </span>
        </div>

        <div class="grid grid-cols-3 gap-3 impostazioni-strette:grid-cols-1">
          <div
            v-for="voce in importi"
            :key="voce.label"
            class="rounded-lg bg-surface-gray-2 px-3 py-2"
          >
            <div class="text-p-sm text-ink-gray-6">{{ voce.label }}</div>
            <div class="text-base-semibold text-ink-gray-8">
              {{ formatEuro(voce.value) }}
            </div>
          </div>
        </div>

        <div
          class="flex items-center justify-between gap-3 max-md:flex-col max-md:items-start"
        >
          <span class="min-w-0 text-p-sm text-ink-gray-7">
            {{
              vista.paid_on
                ? __('Paid on {0}.', [
                    dayjs(vista.paid_on).format('DD/MM/YYYY'),
                  ])
                : vista.due_date
                  ? __('To be paid by {0}.', [
                      dayjs(vista.due_date).format('DD/MM/YYYY'),
                    ])
                  : __('The supplier wrote no due date.')
            }}
          </span>
          <Button
            v-if="vista.can.write"
            class="shrink-0"
            variant="subtle"
            :loading="lavoro === 'pagata'"
            :label="vista.paid_on ? __('Not paid') : __('Paid today')"
            @click="pagata(!vista.paid_on)"
          />
        </div>

        <section v-if="vista.lines?.length" class="flex flex-col gap-1">
          <h3 class="text-p-base-medium text-ink-gray-8">
            {{ __('What it is for') }}
          </h3>
          <div
            v-for="(riga, indice) in vista.lines"
            :key="indice"
            class="flex items-start justify-between gap-3 border-t border-outline-gray-1 py-2 text-p-sm first:border-0"
          >
            <span class="min-w-0 text-ink-gray-7">{{ riga.description }}</span>
            <span class="shrink-0 text-ink-gray-8">
              {{ formatEuro(riga.amount) }}
              <span class="text-ink-gray-6">
                ·
                {{
                  riga.nature
                    ? __('no VAT')
                    : __('VAT {0}%', [Number(riga.vat_rate)])
                }}
              </span>
            </span>
          </div>
        </section>

        <FormControl
          v-model="note"
          type="textarea"
          :label="__('Notes')"
          :disabled="!vista.can.write"
          :placeholder="
            __('Why it is disputed, what the accountant should know')
          "
        />
        <ErrorMessage :message="errore" />
      </div>
    </template>
    <template #actions>
      <div v-if="vista" class="dialog-footer flex items-center gap-2">
        <Button
          v-if="vista.can.pdf"
          iconLeft="file-text"
          :loading="lavoro === 'pdf'"
          :label="__('PDF')"
          @click="pdf"
        />
        <Dropdown v-if="altre.length" :options="altre">
          <Button icon="more-horizontal" :aria-label="__('Other actions')" />
        </Dropdown>
        <Button
          v-if="vista.can.write && vista.status !== 'registrata'"
          class="ml-auto"
          variant="solid"
          :loading="lavoro === 'registrata'"
          :label="__('To the accountant')"
          @click="stato('registrata')"
        />
      </div>
    </template>
  </Dialog>
</template>

<script setup>
import { formatEuro } from '@/utils/invoicing'
import { scadenzaRicevuta, statoRicevuta } from '@/utils/ricevute'
import { oggiDelCentro } from '@/utils/scheduler'
import {
  Badge,
  Button,
  Dialog,
  Dropdown,
  ErrorMessage,
  FormControl,
  call,
  dayjs,
  toast,
} from 'frappe-ui'
import { computed, ref, watch } from 'vue'

const aperta = defineModel({ type: Boolean, default: false })
const props = defineProps({
  invoice: { type: String, default: '' },
})
const emit = defineEmits(['changed'])

const vista = ref(null)
const note = ref('')
const errore = ref('')
const lavoro = ref('')

const titolo = computed(
  () =>
    vista.value?.supplier_name ||
    vista.value?.supplier_tax_id ||
    __('Supplier invoice'),
)

const scadenza = computed(() =>
  scadenzaRicevuta(vista.value, oggiDelCentro(), __),
)

const importi = computed(() => [
  { label: __('Taxable amount'), value: vista.value?.taxable_amount },
  { label: __('VAT'), value: vista.value?.vat_amount },
  { label: __('Total'), value: vista.value?.total_amount },
])

async function carica() {
  if (!props.invoice) return
  errore.value = ''
  vista.value = await call('crm.invoicing.ricevute.get_received_invoice', {
    name: props.invoice,
  })
  note.value = vista.value.notes || ''
  // opened is seen: an invoice nobody had opened stops asking to be
  if (vista.value.status === 'ricevuta' && vista.value.can.write) {
    await stato('letta', { silenzioso: true })
  }
}

watch(
  () => [aperta.value, props.invoice],
  ([aperto]) => aperto && carica(),
  { immediate: true },
)

async function esegui(nome, metodo, parametri) {
  lavoro.value = nome
  errore.value = ''
  try {
    vista.value = await call(metodo, { name: props.invoice, ...parametri })
    emit('changed')
    return true
  } catch (e) {
    errore.value = e.messages?.[0] || e.message
    return false
  } finally {
    lavoro.value = ''
  }
}

async function stato(valore, { silenzioso = false } = {}) {
  const fatto = await esegui(
    valore,
    'crm.invoicing.ricevute.set_received_status',
    {
      status: valore,
      notes: note.value,
    },
  )
  if (fatto && !silenzioso) toast.success(__('Saved'))
}

function pagata(si) {
  return esegui('pagata', 'crm.invoicing.ricevute.set_received_paid', {
    paid_on: si ? oggiDelCentro() : null,
  })
}

async function pdf() {
  if (vista.value.pdf_file) {
    window.open(vista.value.pdf_file, '_blank')
    return
  }
  lavoro.value = 'pdf'
  try {
    const { file } = await call('crm.invoicing.ricevute.make_received_pdf', {
      name: props.invoice,
    })
    vista.value.pdf_file = file
    window.open(file, '_blank')
  } catch (e) {
    toast.error(e.messages?.[0] || e.message)
  } finally {
    lavoro.value = ''
  }
}

const altre = computed(() => {
  if (!vista.value) return []
  const voci = []
  if (vista.value.xml_file) {
    voci.push({
      label: __('The XML file'),
      icon: 'download',
      onClick: () => window.open(vista.value.xml_file, '_blank'),
    })
  }
  if (vista.value.can.write) {
    if (vista.value.status !== 'rifiutata') {
      voci.push({
        label: __('Dispute it'),
        icon: 'alert-triangle',
        onClick: () => stato('rifiutata'),
      })
    }
    if (vista.value.status !== 'letta') {
      voci.push({
        label: __('Back to seen'),
        icon: 'rotate-ccw',
        onClick: () => stato('letta'),
      })
    }
  }
  return voci
})
</script>
