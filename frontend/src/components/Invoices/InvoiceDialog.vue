<!--
  The invoice made inside DottorCloud (crm/invoicing/emissione.py).

  Who it is for, what was done and by whom, how it was paid - and, before anything
  is issued, where it goes: a PDF to the patient and the expense to the Sistema TS,
  or the SdI. A new invoice lives in memory: every change asks the server where it
  would go and what it adds up to, and nothing is saved until somebody says so.
  Issued, it has its number, its PDF, the way to the SdI when it takes it, and the
  credit note that corrects it.
-->
<template>
  <Dialog v-model="stato.aperto" :options="{ size: '4xl' }">
    <template #body-title>
      <div class="flex min-w-0 items-center gap-2">
        <h3 class="truncate text-2xl font-semibold text-ink-gray-9">
          {{ titolo }}
        </h3>
        <Badge
          v-if="vista?.name && vista.docstatus === 0"
          :label="__('Draft')"
          theme="orange"
        />
        <!-- issued in test, or to be issued while invoicing is in test -->
        <Badge
          v-if="vista?.test"
          :label="__('Test')"
          theme="red"
          :title="
            vista.docstatus === 1
              ? __('A test invoice: it has no fiscal value and reached nobody.')
              : __(
                  'Invoicing is in test: this invoice will be numbered PROVA and reach nobody.',
                )
          "
        />
      </div>
    </template>
    <template #body-content>
      <div v-if="!vista" class="flex justify-center py-12">
        <LoadingIndicator class="size-6" />
      </div>
      <div v-else class="flex flex-col gap-6">
        <!-- where it goes, before anything else: the one thing that cannot be
             undone once it has left -->
        <div
          v-if="vista.destination"
          class="flex flex-col gap-0.5 rounded-lg border px-4 py-3"
          :class="
            vista.destination.value === 'sdi'
              ? 'border-outline-blue-2 bg-surface-blue-1'
              : 'border-outline-green-2 bg-surface-green-1'
          "
        >
          <span class="text-p-sm text-ink-gray-6">
            {{
              vista.docstatus === 1 ? __('Where it went') : __('Where it goes')
            }}
          </span>
          <span class="text-p-base-medium text-ink-gray-8">
            {{ vista.destination.label }}
          </span>
          <span
            v-if="vista.destination.description"
            class="text-p-sm text-ink-gray-6"
          >
            {{ vista.destination.description }}
          </span>
          <span
            v-if="vista.states.sdi || vista.states.ts"
            class="text-p-sm text-ink-gray-6"
          >
            {{
              [
                vista.states.sdi && `SdI: ${vista.states.sdi}`,
                vista.states.ts && `Sistema TS: ${vista.states.ts}`,
              ]
                .filter(Boolean)
                .join(' · ')
            }}
          </span>
        </div>
        <div
          v-if="vista.rejection"
          class="flex flex-col gap-1 rounded-lg border border-outline-red-2 bg-surface-red-1 px-4 py-3"
        >
          <span class="text-p-base-medium text-ink-red-8">
            {{ __('The SdI refused it') }}
          </span>
          <span class="whitespace-pre-line text-p-sm text-ink-red-7">
            {{ vista.rejection }}
          </span>
          <span class="text-p-sm text-ink-gray-7">
            {{
              __(
                'A refused invoice counts as never issued: correct it and issue it again with the same number and date, within five days of the notice.',
              )
            }}
          </span>
        </div>
        <div
          v-if="vista.findings?.length"
          class="flex flex-col gap-1 rounded-lg border border-outline-amber-2 bg-surface-amber-1 px-4 py-3"
        >
          <span class="text-p-base-medium text-ink-gray-8">
            {{ __('Before sending it') }}
          </span>
          <span
            v-for="rilievo in vista.findings"
            :key="rilievo"
            class="text-p-sm text-ink-gray-7"
          >
            {{ rilievo }}
          </span>
        </div>
        <div v-if="vista.reference?.number" class="text-p-sm text-ink-gray-6">
          {{ __('It corrects invoice {0}.', [vista.reference.number]) }}
        </div>

        <!-- who it is for -->
        <section class="flex flex-col gap-3">
          <h4 class="text-p-base-medium text-ink-gray-8">
            {{ __('Who it is for') }}
          </h4>
          <div
            v-if="modificabile"
            class="grid grid-cols-2 gap-3 max-md:grid-cols-1"
          >
            <Link
              class="form-control"
              doctype="CRM Lead"
              :label="__('Client')"
              :value="
                vista.client.party_type === 'CRM Lead' ? vista.client.party : ''
              "
              :placeholder="__('Choose the client')"
              @change="scegliPersona"
            />
            <FormControl
              v-model="vista.client.recipient_type"
              type="select"
              :label="__('Recipient')"
              :options="vista.options.recipient_type"
              :description="
                spiegazioneDi(
                  vista.options.recipient_type,
                  vista.client.recipient_type,
                )
              "
            />
          </div>
          <div class="text-p-sm text-ink-gray-7">
            {{ riepilogoCliente || __('Nobody yet: choose the client.') }}
          </div>
          <Button
            v-if="modificabile"
            class="self-start"
            variant="ghost"
            :iconLeft="datiAperti ? 'chevron-down' : 'chevron-right'"
            :label="__('Details on the invoice')"
            @click="datiAperti = !datiAperti"
          />
          <div
            v-if="modificabile && datiAperti"
            class="grid grid-cols-3 gap-3 max-md:grid-cols-1"
          >
            <FormControl
              v-model="vista.client.billing_name"
              :label="__('Name on the invoice')"
            />
            <FormControl
              v-model="vista.client.fiscal_code"
              v-bind="tastiera('codice')"
              :label="__('Codice fiscale')"
            />
            <FormControl
              v-if="vista.client.recipient_type !== 'persona_fisica'"
              v-model="vista.client.tax_id"
              v-bind="tastiera('codice')"
              :label="__('Partita IVA / VAT number')"
            />
            <FormControl
              v-model="vista.client.address_line"
              :label="__('Address')"
            />
            <FormControl
              v-model="vista.client.postal_code"
              :label="__('Postal code')"
            />
            <FormControl v-model="vista.client.city" :label="__('City')" />
            <template v-if="vista.client.recipient_type === 'soggetto_iva'">
              <FormControl
                v-model="vista.client.recipient_code"
                v-bind="tastiera('codice')"
                :label="__('Codice destinatario')"
              />
              <FormControl
                v-model="vista.client.pec"
                v-bind="tastiera('email')"
                :label="__('PEC')"
              />
            </template>
          </div>
        </section>

        <!-- what was done, and by whom -->
        <section class="flex flex-col gap-2">
          <h4 class="text-p-base-medium text-ink-gray-8">
            {{ __('What was done') }}
          </h4>
          <div
            v-for="(riga, indice) in vista.items"
            :key="indice"
            class="grid gap-2 rounded-lg border border-outline-gray-2 px-3 py-2"
            :class="[
              mostraProfessionista
                ? 'grid-cols-[1fr_1fr_5rem_7rem_6rem_2rem] max-md:grid-cols-2'
                : 'grid-cols-[2fr_5rem_7rem_6rem_2rem] max-md:grid-cols-2',
              modificabile ? 'items-end' : 'items-center',
            ]"
          >
            <template v-if="modificabile">
              <Link
                class="form-control max-md:col-span-2"
                doctype="CRM Billable Service"
                :label="indice === 0 ? __('Service') : ''"
                :value="riga.billable_service"
                :filters="{ enabled: 1 }"
                :placeholder="__('Choose the service')"
                @change="(v) => scegliServizio(riga, v)"
              />
              <Link
                v-if="mostraProfessionista"
                class="form-control max-md:col-span-2"
                doctype="CRM Service Provider"
                :label="indice === 0 ? __('Professional') : ''"
                :value="riga.service_provider"
                :filters="{ enabled: 1 }"
                :placeholder="__('Who performed it')"
                @change="(v) => (riga.service_provider = v)"
              />
              <FormControl
                v-model="riga.qty"
                type="number"
                :label="indice === 0 ? __('Quantity') : ''"
                min="1"
              />
              <FormControl
                v-model="riga.rate"
                type="number"
                :label="indice === 0 ? __('Unit price') : ''"
                step="0.01"
              />
            </template>
            <template v-else>
              <div class="flex min-w-0 flex-col max-md:col-span-2">
                <span class="truncate text-p-base text-ink-gray-8">
                  {{ riga.service_label || riga.billable_service }}
                </span>
                <span
                  v-if="
                    riga.description && riga.description !== riga.service_label
                  "
                  class="truncate text-p-sm text-ink-gray-5"
                >
                  {{ riga.description }}
                </span>
              </div>
              <span
                v-if="mostraProfessionista"
                class="truncate text-p-sm text-ink-gray-6 max-md:col-span-2"
              >
                {{ riga.provider_label }}
              </span>
              <span class="text-p-sm text-ink-gray-6">× {{ riga.qty }}</span>
              <span class="text-p-sm text-ink-gray-6">
                {{ formatEuro(riga.rate) }}
              </span>
            </template>
            <div class="flex flex-col items-end text-right">
              <span class="text-p-base text-ink-gray-8">
                {{ formatEuro(riga.amount) }}
              </span>
              <span v-if="riga.vat" class="text-p-xs text-ink-gray-5">
                {{ riga.vat }}
              </span>
            </div>
            <Button
              v-if="modificabile"
              variant="ghost"
              icon="x"
              class="touch-target"
              :aria-label="__('Remove the line')"
              @click="vista.items.splice(indice, 1)"
            />
            <span v-else />
          </div>
          <Button
            v-if="modificabile"
            class="self-start"
            variant="subtle"
            iconLeft="plus"
            :label="__('Add a line')"
            @click="vista.items.push(rigaVuota(vista.shape?.provider))"
          />
        </section>

        <!-- how it was paid -->
        <section class="flex flex-col gap-3">
          <h4 class="text-p-base-medium text-ink-gray-8">
            {{ __('How it was paid') }}
          </h4>
          <div
            v-if="modificabile"
            class="grid grid-cols-2 gap-3 max-md:grid-cols-1"
          >
            <FormControl
              v-model="vista.payment.payment_method"
              type="select"
              :label="__('Payment method')"
              :options="vista.options.payment_method"
              :description="
                spiegazioneDi(
                  vista.options.payment_method,
                  vista.payment.payment_method,
                )
              "
            />
            <!-- a refund is paid on the day of its credit note -->
            <FormControl
              v-if="!vista.is_note"
              v-model="vista.payment.payment_date"
              type="date"
              :label="__('Payment date')"
            />
          </div>
          <div v-else class="text-p-sm text-ink-gray-7">
            {{ metodoDiPagamento }}
          </div>
          <FormControl
            v-if="modificabile && pagataPrima"
            v-model="vista.payment.advance_payment"
            type="checkbox"
            :label="__('Paid before the invoice')"
            :description="
              __(
                'A prepaid package, a deposit: otherwise one of the two dates is wrong.',
              )
            "
          />
          <FormControl
            v-if="
              vista.destination?.value === 'pdf_ts' &&
              modificabile &&
              !vista.is_note
            "
            v-model="vista.payment.privacy_opposition"
            type="checkbox"
            :label="
              __(
                'The patient opposes the use of this expense in their pre-filled tax return',
              )
            "
            :description="
              __(
                'Asked by the patient: the expense still goes to the Sistema TS, without their codice fiscale.',
              )
            "
          />
        </section>

        <!-- what is still wrong: all of it, not the first item -->
        <div
          v-if="vista.errors.length && vista.docstatus === 0"
          class="flex flex-col gap-1 rounded-lg border border-outline-red-2 bg-surface-red-1 px-4 py-3"
        >
          <span class="text-p-base-medium text-ink-red-8">
            {{ __('Before it can be issued') }}
          </span>
          <span
            v-for="problema in vista.errors"
            :key="problema"
            class="text-p-sm text-ink-red-7"
          >
            {{ problema }}
          </span>
        </div>
        <!-- on a draft what is worth knowing before issuing it; on an issued
             invoice what was found when it was issued (the Sistema TS's report) -->
        <div
          v-if="vista.warnings.length"
          class="flex flex-col gap-1 rounded-lg border border-outline-amber-2 bg-surface-amber-1 px-4 py-3"
        >
          <span
            v-for="avviso in vista.warnings"
            :key="avviso"
            class="text-p-sm text-ink-gray-7"
          >
            {{ avviso }}
          </span>
        </div>

        <!-- what it adds up to, once every line is complete -->
        <div
          v-if="vista.totals"
          class="ml-auto flex w-72 flex-col gap-1 max-md:w-full"
        >
          <div
            v-for="riga in totali"
            :key="riga.chiave"
            class="flex items-center justify-between gap-4"
            :class="
              riga.forte
                ? 'border-t border-outline-gray-2 pt-1 text-p-base-medium text-ink-gray-9'
                : 'text-p-sm text-ink-gray-6'
            "
          >
            <span>{{ __(riga.etichetta) }}</span>
            <span>{{ formatEuro(riga.valore) }}</span>
          </div>
        </div>
        <ErrorMessage :message="errore" />
      </div>
    </template>
    <template #actions>
      <div
        v-if="vista"
        class="dialog-footer flex flex-wrap items-center justify-end gap-2"
      >
        <template v-if="vista.docstatus === 0">
          <Button
            v-if="vista.can.delete"
            class="mr-auto"
            variant="ghost"
            theme="red"
            :label="__('Throw the draft away')"
            :loading="azione === 'elimina'"
            @click="elimina"
          />
          <Button
            v-if="vista.can.save"
            :label="__('Save the draft')"
            :loading="azione === 'salva'"
            @click="salva"
          />
          <Button
            v-if="vista.can.issue"
            variant="solid"
            :label="__('Issue')"
            :disabled="Boolean(vista.errors.length) || inAttesa"
            :loading="azione === 'emetti'"
            @click="emetti"
          />
        </template>
        <template v-else>
          <Button
            v-if="vista.can.credit_note"
            class="mr-auto"
            variant="ghost"
            :label="__('Credit note')"
            :loading="azione === 'nota'"
            @click="notaDiCredito"
          />
          <Button
            v-if="vista.can.reopen"
            :label="__('Correct it')"
            :loading="azione === 'riapri'"
            @click="riapri"
          />
          <Button
            v-if="vista.can.transmit"
            :label="__('Send to the SdI')"
            :loading="azione === 'sdi'"
            @click="trasmetti"
          />
          <Button
            v-if="vista.can.pdf"
            variant="solid"
            iconLeft="download"
            :label="__('Download the PDF')"
            @click="scaricaPdf"
          />
          <Button
            v-else-if="vista.can.make_pdf"
            variant="solid"
            :label="__('Make the PDF')"
            :loading="azione === 'pdf'"
            @click="faiPdf"
          />
        </template>
      </div>
    </template>
  </Dialog>
</template>

<script setup>
import Link from '@/components/Controls/Link.vue'
import { useFattura } from '@/composables/fattura'
import {
  datiDaInviare,
  righeDeiTotali,
  rigaVuota,
  titoloDellaFattura,
} from '@/utils/fattura'
import { formatEuro } from '@/utils/invoicing'
import { spiegazioneDi } from '@/utils/scelte'
import { tastiera } from '@/utils/tastiera'
import { watchDebounced } from '@vueuse/core'
import {
  Badge,
  Button,
  Dialog,
  ErrorMessage,
  FormControl,
  LoadingIndicator,
  call,
  toast,
} from 'frappe-ui'
import { computed, ref, watch } from 'vue'

const { stato, chiudiFattura } = useFattura()

const vista = ref(null)
const errore = ref('')
const azione = ref('')
const inAttesa = ref(false)
const datiAperti = ref(false)
// the answer to the last question only: an older one that arrives late is dropped
let domanda = 0

const modificabile = computed(
  () => vista.value?.docstatus === 0 && vista.value?.can?.save,
)
const mostraProfessionista = computed(() => !vista.value?.shape?.solo)
// paid before the invoice's date: a prepaid package, or a wrong date
const pagataPrima = computed(() => {
  const pagata = vista.value?.payment?.payment_date
  const emessa = vista.value?.posting_date
  return Boolean(pagata && emessa && pagata < emessa)
})

const titolo = computed(() =>
  __(titoloDellaFattura(vista.value), [vista.value?.document_number]),
)

const totali = computed(() => righeDeiTotali(vista.value?.totals || {}))

const riepilogoCliente = computed(() => {
  const cliente = vista.value?.client || {}
  return [
    cliente.billing_name || cliente.party_label,
    cliente.fiscal_code,
    cliente.tax_id,
    [cliente.address_line, cliente.postal_code, cliente.city]
      .filter(Boolean)
      .join(' '),
  ]
    .filter(Boolean)
    .join(' · ')
})

const metodoDiPagamento = computed(() => {
  const metodo = vista.value?.payment?.payment_method
  return (
    (vista.value?.options?.payment_method || []).find(
      (opzione) => opzione.value === metodo,
    )?.label || metodo
  )
})

function applica(risposta, { tutta = false } = {}) {
  if (tutta || !vista.value) {
    vista.value = risposta
    return
  }
  // while somebody types, only what the server works out comes back: where it
  // goes, the totals, what is wrong, each line's amount, the client's details it
  // filled from their profile
  const attuale = vista.value
  for (const chiave of [
    'destination',
    'errors',
    'warnings',
    'totals',
    'options',
    'can',
    'shape',
    'states',
  ]) {
    attuale[chiave] = risposta[chiave]
  }
  for (const [chiave, valore] of Object.entries(risposta.client || {})) {
    if (!attuale.client[chiave] && valore) attuale.client[chiave] = valore
  }
  risposta.items.forEach((riga, indice) => {
    const nostra = attuale.items.filter((r) => r.billable_service)[indice]
    // a line removed or changed while the answer travelled: the next one says it
    if (nostra?.billable_service !== riga.billable_service) return
    Object.assign(nostra, {
      amount: riga.amount,
      vat: riga.vat,
      service_label: riga.service_label,
      provider_label: riga.provider_label,
      description: nostra.description || riga.description,
      rate: Number(nostra.rate) ? nostra.rate : riga.rate,
      service_provider: nostra.service_provider || riga.service_provider,
    })
  })
}

async function anteprima() {
  if (!modificabile.value) return
  const questa = ++domanda
  inAttesa.value = true
  try {
    const risposta = await call('crm.invoicing.emissione.preview', {
      data: datiDaInviare(vista.value),
      invoice: vista.value.name,
    })
    if (questa === domanda) {
      applica(risposta)
      errore.value = ''
    }
  } catch (e) {
    if (questa === domanda) errore.value = e.messages?.[0] || e.message
  } finally {
    if (questa === domanda) inAttesa.value = false
  }
}

watchDebounced(
  () => vista.value && JSON.stringify(datiDaInviare(vista.value)),
  (adesso, prima) => {
    // an invoice just opened is not a change
    if (prima && adesso !== prima) anteprima()
  },
  { debounce: 450 },
)

async function apri() {
  vista.value = null
  errore.value = ''
  datiAperti.value = false
  try {
    if (stato.nome) {
      applica(
        await call('crm.invoicing.emissione.get_invoice', {
          invoice: stato.nome,
        }),
        { tutta: true },
      )
    } else {
      // what proposed it (an appointment) fills in what it knows; the rest is asked
      const bozza = stato.bozza || {}
      const nuova = await call('crm.invoicing.emissione.preview', {
        data: { ...(stato.cliente || {}), ...bozza, items: bozza.items || [] },
      })
      if (!nuova.items?.length) nuova.items = [rigaVuota(nuova.shape?.provider)]
      applica(nuova, { tutta: true })
    }
  } catch (e) {
    errore.value = e.messages?.[0] || e.message
    vista.value = null
  }
}

watch(
  () => stato.richiesta,
  () => stato.aperto && apri(),
)

function scegliServizio(riga, servizio) {
  // the service's own price, words and professional come back with the preview:
  // the last one's would stay on a line that is now something else
  Object.assign(riga, {
    billable_service: servizio || '',
    rate: 0,
    description: '',
  })
}

function scegliPersona(persona) {
  Object.assign(vista.value.client, {
    party_type: persona ? 'CRM Lead' : '',
    party: persona || '',
    // the new person's details come from their profile: none of the last one's
    billing_name: '',
    first_name: '',
    last_name: '',
    fiscal_code: '',
    address_line: '',
    postal_code: '',
    city: '',
  })
}

async function esegui(nome, metodo, parametri, messaggio) {
  azione.value = nome
  errore.value = ''
  try {
    const risposta = await call(metodo, parametri)
    // the invoice as it now is, when the answer is one (not a file, not a receipt)
    if (risposta?.name && risposta.can) {
      applica(risposta, { tutta: true })
      stato.nome = risposta.name
    }
    if (messaggio) toast.success(messaggio)
    stato.alCambio?.()
    return risposta
  } catch (e) {
    // a refusal at the SdI's door says which lines and why, with line breaks
    errore.value = (e.messages || [e.message])
      .join(' ')
      .replace(/<br\s*\/?>/gi, ' ')
      .replace(/<[^>]*>/g, '')
  } finally {
    azione.value = ''
  }
}

function salva() {
  return esegui(
    'salva',
    'crm.invoicing.emissione.save',
    { data: datiDaInviare(vista.value), invoice: vista.value.name },
    __('Draft saved'),
  )
}

function emetti() {
  return esegui(
    'emetti',
    'crm.invoicing.emissione.issue',
    { data: datiDaInviare(vista.value), invoice: vista.value.name },
    __('Invoice issued'),
  )
}

async function elimina() {
  const risposta = await esegui(
    'elimina',
    'crm.invoicing.emissione.delete_draft',
    { invoice: vista.value.name },
    __('Draft thrown away'),
  )
  if (risposta?.deleted) chiudiFattura()
}

function notaDiCredito() {
  return esegui(
    'nota',
    'crm.invoicing.emissione.credit_note',
    { invoice: vista.value.name },
    __('Credit note ready: check it and issue it'),
  )
}

async function riapri() {
  const risposta = await esegui(
    'riapri',
    'crm.invoicing.api.reopen_rejected',
    { invoice: vista.value.name },
    __('Back in draft, with its number: correct it and issue it again'),
  )
  if (risposta) apri()
}

async function trasmetti() {
  const risposta = await esegui('sdi', 'crm.invoicing.api.send_to_sdi', {
    invoice: vista.value.name,
  })
  if (!risposta) return
  // with no provider the file is downloaded and uploaded on the portal by hand
  if (risposta.file) window.open(risposta.file, '_blank')
  toast.success(
    risposta.sent
      ? __('Sent to the SdI')
      : __('The file is ready to be transmitted'),
  )
  apri()
}

async function faiPdf() {
  const risposta = await esegui('pdf', 'crm.invoicing.api.generate_pdf', {
    invoice: vista.value.name,
  })
  if (risposta?.skipped && !risposta.file) {
    errore.value = risposta.reason
    return
  }
  if (risposta) apri()
}

function scaricaPdf() {
  window.open(vista.value.pdf, '_blank')
}
</script>
