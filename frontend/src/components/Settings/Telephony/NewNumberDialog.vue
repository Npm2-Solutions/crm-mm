<!--
  Copyright (c) 2026, NPM2 Solutions Srl and contributors
  For license information, please see license.txt

  A new Italian number in the centre's Twilio space (doc 52), without leaving
  DottorCloud. The kind with its price a month and whose the number is; the
  fields Twilio asks, with what invoicing knows already in them; the documents,
  uploaded here; sent to Twilio, which checks them in a few days. Documents
  approved - now or for a number before, of the same kind - and the number is
  chosen among those Twilio has and bought, already answering on DottorCloud.
-->
<template>
  <Dialog v-model="show" :options="{ title: titolo, size: 'xl' }">
    <template #body-content>
      <!-- 1: which number, whose -->
      <div v-if="passo === 'tipo'" class="flex flex-col gap-4">
        <div class="flex flex-col gap-2">
          <SceltaRadio
            v-for="tipo in tipi"
            :key="tipo.value"
            v-model="scelta.tipo"
            :scelta="tipo"
            nome="tipo-di-numero"
          />
        </div>
        <FormControl
          v-if="tipoScelto?.area"
          v-model="scelta.zona"
          type="text"
          inputmode="numeric"
          :label="__('Area code')"
          :placeholder="__('02, 06, 011…')"
          :description="
            __('The address on the documents must be in this area.')
          "
        />
        <div class="flex flex-col gap-1">
          <span class="text-p-sm text-ink-gray-6">{{
            __('Whose number')
          }}</span>
          <div class="grid grid-cols-2 gap-2 max-md:grid-cols-1">
            <SceltaRadio
              v-for="titolare in titolari"
              :key="titolare.value"
              v-model="scelta.titolare"
              :scelta="titolare"
              nome="titolare-del-numero"
            />
          </div>
        </div>
        <p
          v-if="disponibili.data && tipoScelto"
          class="text-p-sm"
          :class="
            disponibili.data.numbers.length
              ? 'text-ink-gray-6'
              : 'text-ink-amber-8'
          "
        >
          {{
            disponibili.data.numbers.length
              ? __('Twilio has numbers like {0} ready now.', [
                  disponibili.data.numbers
                    .slice(0, 2)
                    .map((n) => n.label)
                    .join(', '),
                ])
              : __(
                  'Twilio has none of these ready now: the documents can be approved all the same, and the number is bought when Twilio has one.',
                )
          }}
        </p>
      </div>

      <!-- 2: who it is for -->
      <div v-else-if="passo === 'dati'" class="flex flex-col gap-4">
        <p class="text-p-base text-ink-gray-7">
          {{
            __(
              'Twilio asks every Italian number for who it is for. What {brand} knows of the centre is already written: check it.',
            )
          }}
        </p>
        <div class="grid grid-cols-2 gap-4 max-md:grid-cols-1">
          <FormControl
            v-for="campo in requisiti.fields"
            :key="campo.name"
            v-model="valori[campo.name]"
            type="text"
            :label="campo.label"
            :description="campo.description"
          />
        </div>
        <FormControl
          v-model="email"
          type="email"
          :label="__('Email for Twilio')"
          :description="
            __('Twilio writes here about the documents. Not a PEC mailbox.')
          "
        />
      </div>

      <!-- 3: the documents -->
      <div v-else-if="passo === 'documenti'" class="flex flex-col gap-5">
        <p class="text-p-base text-ink-gray-7">
          {{
            __(
              'A PDF, a JPEG or a PNG of each one, of 5 MB at most. Once Twilio approves them, {brand} does not keep them: Twilio has its copy.',
            )
          }}
        </p>
        <div
          v-for="requisito in requisitiDaMostrare"
          :key="requisito.requirement"
          class="flex flex-col gap-2 rounded-lg border border-outline-gray-2 px-4 py-3"
        >
          <FormControl
            v-if="requisito.accepted.length > 1"
            v-model="scelte[requisito.requirement]"
            type="select"
            :label="__('Which document')"
            :options="
              requisito.accepted.map((d) => ({
                label: d.label,
                value: d.type,
              }))
            "
          />
          <span v-else class="text-p-base-medium text-ink-gray-8">
            {{ documentoScelto(requisito, scelte)?.label }}
          </span>
          <span
            v-if="
              requisito.description &&
              !documentoScelto(requisito, scelte)?.known
            "
            class="text-p-sm text-ink-gray-5"
            >{{ requisito.description }}</span
          >
          <template v-if="!documentoScelto(requisito, scelte)?.address">
            <div
              v-for="campo in campiDelDocumento(
                documentoScelto(requisito, scelte),
                requisiti.fields,
              )"
              :key="campo.name"
            >
              <FormControl
                v-model="
                  valoriDeiDocumenti[`${requisito.requirement}:${campo.name}`]
                "
                type="text"
                :label="campo.label"
                :description="campo.description"
              />
            </div>
            <FileUploader
              :uploadArgs="{ private: true }"
              :validateFile="valida"
              @success="(caricato) => fileCaricato(requisito, caricato)"
            >
              <template #default="{ openFileSelector, uploading, progress }">
                <div class="flex min-w-0 flex-wrap items-center gap-2">
                  <Button
                    icon-left="upload"
                    :label="
                      uploading
                        ? __('Uploading {0}%', [progress])
                        : file[requisito.requirement]
                          ? __('Upload another file')
                          : __('Upload the document')
                    "
                    @click="openFileSelector"
                  />
                  <span
                    v-if="file[requisito.requirement]"
                    class="min-w-0 truncate text-p-sm text-ink-gray-7"
                  >
                    {{ file[requisito.requirement].file_name }}
                  </span>
                </div>
              </template>
            </FileUploader>
          </template>
        </div>

        <div
          v-if="chiedeIndirizzo(requisiti.documents, scelte)"
          class="flex flex-col gap-3"
        >
          <span class="text-p-base-medium text-ink-gray-8">
            {{ __("The office's address") }}
          </span>
          <div class="grid grid-cols-2 gap-4 max-md:grid-cols-1">
            <FormControl
              v-model="indirizzo.street"
              type="text"
              class="col-span-2 max-md:col-span-1"
              :label="__('Street and number')"
            />
            <FormControl
              v-model="indirizzo.city"
              type="text"
              :label="__('City')"
            />
            <FormControl
              v-model="indirizzo.region"
              type="text"
              :label="__('Province')"
            />
            <FormControl
              v-model="indirizzo.postal_code"
              type="text"
              inputmode="numeric"
              :label="__('Postal code')"
            />
          </div>
        </div>

        <div
          v-if="mancanti.length"
          class="flex flex-col gap-1 rounded-lg bg-surface-red-1 px-4 py-3"
        >
          <span class="text-p-sm-medium text-ink-red-8">
            {{ __('Twilio says something is missing:') }}
          </span>
          <span
            v-for="riga in mancanti"
            :key="riga"
            class="text-p-sm text-ink-red-8"
            >{{ riga }}</span
          >
        </div>
      </div>

      <!-- sent: Twilio checks them -->
      <div v-else-if="passo === 'inviato'" class="flex flex-col gap-3">
        <p class="text-p-base text-ink-gray-8">
          {{ __('The documents are with Twilio.') }}
        </p>
        <p class="text-p-base text-ink-gray-7">
          {{
            __(
              'Twilio checks them, usually within a few working days, and writes to {0}. {brand} tells you among the notifications when it answers: then you choose the number.',
              [email],
            )
          }}
        </p>
      </div>

      <!-- the number: chosen among those Twilio has, and bought -->
      <div v-else-if="passo === 'numero'" class="flex flex-col gap-4">
        <p class="text-p-base text-ink-gray-7">
          {{
            __(
              'The documents are approved. Choose the number: it answers on {brand} from the moment it is bought.',
            )
          }}
        </p>
        <div class="flex items-end gap-2">
          <FormControl
            v-model="cifre"
            class="min-w-0 flex-1"
            type="text"
            inputmode="numeric"
            :label="__('With these digits')"
            :placeholder="__('Any')"
            @keydown.enter="cerca"
          />
          <Button
            class="shrink-0"
            :label="__('Search')"
            :loading="trovati.loading"
            @click="cerca"
          />
        </div>
        <div
          v-if="trovati.data?.numbers?.length"
          class="flex max-h-72 flex-col gap-2 overflow-y-auto"
        >
          <SceltaRadio
            v-for="numero in trovati.data.numbers"
            :key="numero.phone_number"
            v-model="numeroScelto"
            :scelta="{
              value: numero.phone_number,
              label: numero.label,
              description: [numero.locality, numero.region]
                .filter(Boolean)
                .join(', '),
            }"
            nome="numero-da-comprare"
          />
        </div>
        <p v-else-if="trovati.data" class="text-p-sm text-ink-amber-8">
          {{
            __(
              'Twilio has none of these ready now. Try other digits, or come back in a few days.',
            )
          }}
        </p>
        <p v-if="prezzoDelNumero" class="text-p-sm text-ink-gray-6">
          {{
            __(
              "Twilio charges {0} a month to the centre's account, from today, until the number is released.",
              [prezzoDelNumero],
            )
          }}
        </p>
      </div>

      <ErrorMessage class="mt-4" :message="errore" />
    </template>

    <template #actions>
      <div class="dialog-footer flex justify-between gap-2">
        <Button
          v-if="['dati', 'documenti'].includes(passo)"
          :label="__('Back')"
          @click="indietro"
        />
        <span v-else />
        <div class="flex gap-2">
          <Button
            v-if="passo === 'inviato'"
            variant="solid"
            :label="__('Close')"
            @click="show = false"
          />
          <Button
            v-else-if="passo === 'tipo'"
            variant="solid"
            :label="__('Next')"
            :loading="requisitiRisorsa.loading"
            @click="avanti"
          />
          <Button
            v-else-if="passo === 'dati'"
            variant="solid"
            :label="__('Next')"
            @click="passo = 'documenti'"
          />
          <Button
            v-else-if="passo === 'documenti'"
            variant="solid"
            :label="__('Send to Twilio')"
            :loading="manda.loading"
            @click="invia"
          />
          <Button
            v-else-if="passo === 'numero'"
            variant="solid"
            :label="
              numeroScelto
                ? __('Buy {0}', [etichettaDelNumero])
                : __('Choose a number')
            "
            :disabled="!numeroScelto"
            :loading="compra.loading"
            @click="
              compra.submit({
                request: richiestaApprovata,
                phone_number: numeroScelto,
              })
            "
          />
        </div>
      </div>
    </template>
  </Dialog>
</template>

<script setup>
import SceltaRadio from '@/components/Settings/Invoicing/SceltaRadio.vue'
import { appLocale } from '@/utils/locale'
import {
  campiDelDocumento,
  chiedeIndirizzo,
  cosaMancaPerMandare,
  documentiDaMandare,
  documentoScelto,
  fileAccettato,
  prefisso,
  prezzoAlMese,
} from '@/utils/numeri'
import {
  Button,
  Dialog,
  ErrorMessage,
  FileUploader,
  FormControl,
  createResource,
  toast,
} from 'frappe-ui'
import { computed, reactive, ref, watch } from 'vue'

const props = defineProps({
  // what get_number_offer said: the kinds, whose, the email
  offerta: { type: Object, required: true },
  // a request to go on with: approved, to buy; a draft or refused, to send again
  richiesta: { type: Object, default: null },
})
const emit = defineEmits(['changed'])
const show = defineModel({ type: Boolean })

const lingua = appLocale() || 'it'

const passo = ref('tipo')
const errore = ref('')
const scelta = reactive({
  tipo: props.richiesta?.number_type || 'mobile',
  titolare: props.richiesta?.end_user_type || props.offerta.owner || 'business',
  zona: props.richiesta?.area_code || '',
})
const requisiti = ref(null)
const valori = reactive({})
const valoriDeiDocumenti = reactive({})
const scelte = reactive({})
const file = reactive({})
const indirizzo = reactive({
  street: '',
  city: '',
  region: '',
  postal_code: '',
})
const email = ref(props.offerta.email || '')
const mancanti = ref([])
// the request this dialog writes: a draft sent again keeps its name
const richiestaInCorso = ref(
  props.richiesta?.may_resend ? props.richiesta.name : null,
)
const richiestaApprovata = ref(
  props.richiesta?.may_buy ? props.richiesta.name : null,
)
const cifre = ref('')
const numeroScelto = ref('')

const titolo = computed(() =>
  passo.value === 'numero' ? __('Choose the number') : __('New number'),
)

const tipi = computed(() =>
  (props.offerta.kinds || []).map((tipo) => ({
    value: tipo.key,
    label: tipo.name,
    description: tipo.description,
    extra: tipo.price
      ? __('{0} a month', [prezzoAlMese(tipo.price, tipo.currency, lingua)])
      : '',
  })),
)
const titolari = computed(() =>
  (props.offerta.owners || []).map((o) => ({
    value: o.key,
    label: o.label,
    description: o.description,
  })),
)
const tipoScelto = computed(() =>
  (props.offerta.kinds || []).find((t) => t.key === scelta.tipo),
)
const prezzoDelNumero = computed(() =>
  tipoScelto.value?.price
    ? prezzoAlMese(tipoScelto.value.price, tipoScelto.value.currency, lingua)
    : '',
)
// a requirement only the address satisfies is the address below, not a card
const requisitiDaMostrare = computed(() =>
  (requisiti.value?.documents || []).filter(
    (r) => r.accepted.length > 1 || !r.accepted[0]?.address,
  ),
)
const etichettaDelNumero = computed(
  () =>
    trovati.data?.numbers?.find((n) => n.phone_number === numeroScelto.value)
      ?.label || numeroScelto.value,
)

function messaggio(e) {
  return e?.messages?.[0] || e?.message || __('Something went wrong')
}

// what Twilio has now, of the kind chosen: before the documents too
const disponibili = createResource({
  url: 'crm.telephony.numeri.search_numbers',
  onError: () => (disponibili.data = null),
})
function guardaIDisponibili() {
  if (passo.value !== 'tipo') return
  if (tipoScelto.value?.area && !prefisso(scelta.zona)) {
    disponibili.data = null
    return
  }
  disponibili.submit({ number_type: scelta.tipo, area_code: scelta.zona })
}
let attesa = null
watch(
  () => [scelta.tipo, scelta.zona],
  () => {
    clearTimeout(attesa)
    attesa = setTimeout(guardaIDisponibili, 400)
  },
  { immediate: true },
)

const requisitiRisorsa = createResource({
  url: 'crm.telephony.numeri.get_number_requirements',
  onSuccess: (dati) => {
    if (dati.approved) {
      // documents approved for this kind already: straight to the number
      richiestaApprovata.value = dati.approved
      passo.value = 'numero'
      cerca()
      return
    }
    requisiti.value = dati
    const prima = dati.previous || {}
    for (const campo of dati.fields) {
      valori[campo.name] = prima.values?.[campo.name] ?? campo.value ?? ''
    }
    for (const requisito of dati.documents) {
      if (prima.choices?.[requisito.requirement]) {
        scelte[requisito.requirement] = prima.choices[requisito.requirement]
      } else {
        scelte[requisito.requirement] = requisito.accepted[0]?.type
      }
      if (prima.files?.[requisito.requirement]) {
        file[requisito.requirement] = prima.files[requisito.requirement]
      }
      for (const accettato of requisito.accepted) {
        for (const campo of campiDelDocumento(accettato, dati.fields)) {
          const chiave = `${requisito.requirement}:${campo.name}`
          valoriDeiDocumenti[chiave] =
            prima.document_values?.[chiave] ?? campo.value ?? ''
        }
      }
    }
    Object.assign(indirizzo, dati.address, prima.address || {})
    email.value = prima.email || dati.email || email.value
    passo.value = 'dati'
  },
  onError: (e) => (errore.value = messaggio(e)),
})

function avanti() {
  errore.value = ''
  if (tipoScelto.value?.area && !prefisso(scelta.zona)) {
    errore.value = __('Write the prefix of the area: 02, 06, 011…')
    return
  }
  requisitiRisorsa.submit({
    number_type: scelta.tipo,
    end_user_type: scelta.titolare,
    area_code: scelta.zona,
    request: richiestaInCorso.value,
  })
}

function indietro() {
  errore.value = ''
  passo.value = passo.value === 'documenti' ? 'dati' : 'tipo'
}

function fileCaricato(requisito, caricato) {
  file[requisito.requirement] = caricato
  errore.value = ''
}

function valida(caricato) {
  const problema = fileAccettato(caricato.name, caricato.size)
  if (problema) return __(problema)
}

const manda = createResource({
  url: 'crm.telephony.numeri.send_number_request',
  method: 'POST',
  onSuccess: (esito) => {
    richiestaInCorso.value = esito.request
    mancanti.value = esito.missing || []
    emit('changed', esito.requests)
    if (!mancanti.value.length) passo.value = 'inviato'
  },
  onError: (e) => (errore.value = messaggio(e)),
})

function invia() {
  errore.value = ''
  mancanti.value = []
  const manca = cosaMancaPerMandare({
    documenti: requisiti.value.documents,
    scelte,
    file,
    indirizzo,
    email: email.value,
  })
  if (manca) {
    errore.value = __(manca)
    return
  }
  manda.submit({
    number_type: scelta.tipo,
    end_user_type: scelta.titolare,
    area_code: scelta.zona,
    regulation: requisiti.value.regulation,
    values: JSON.stringify(valori),
    documents: JSON.stringify(
      documentiDaMandare({
        documenti: requisiti.value.documents,
        scelte,
        file,
        valori: valoriDeiDocumenti,
      }),
    ),
    address: JSON.stringify(indirizzo),
    email: email.value,
    request: richiestaInCorso.value,
  })
}

const trovati = createResource({
  url: 'crm.telephony.numeri.search_numbers',
  onSuccess: () => (numeroScelto.value = ''),
  onError: (e) => (errore.value = messaggio(e)),
})

function cerca() {
  errore.value = ''
  trovati.submit({
    number_type: scelta.tipo,
    area_code: scelta.zona,
    contains: cifre.value,
  })
}

const compra = createResource({
  url: 'crm.telephony.numeri.buy_number',
  method: 'POST',
  onSuccess: (esito) => {
    toast.success(
      __("{0} is the centre's, and answers on {brand}.", [esito.label]),
    )
    emit('changed', esito.requests)
    show.value = false
  },
  onError: (e) => (errore.value = messaggio(e)),
})

// approved documents: the dialog opens on the number
if (richiestaApprovata.value) {
  passo.value = 'numero'
  cerca()
}
</script>
