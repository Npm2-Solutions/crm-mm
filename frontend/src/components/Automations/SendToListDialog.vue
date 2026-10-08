<!--
  Copyright (c) 2026, NPM2 Solutions Srl and contributors
  For license information, please see license.txt

  «Send to a list» (crm/automation/campagne.py): the manager of automations picks
  a campaign - an automation started by hand - and sends it to the People list's
  view or to the rows chosen. Before anything happens, the server counts the list
  as the reader sees it and who would be left out and why; confirmed, a job
  enrols them and the report goes on the automation's Enrolments.
-->
<template>
  <Dialog v-model="show" :options="{ title: __('Send to a list'), size: 'lg' }">
    <template #body-content>
      <div class="flex flex-col gap-5">
        <p class="text-p-base text-ink-gray-7">
          {{ fonte }}
        </p>

        <div
          v-if="campagne.loading && !campagne.data"
          class="flex justify-center py-6"
        >
          <LoaderMark />
        </div>
        <div
          v-else-if="!campagne.data?.length"
          class="flex flex-col items-start gap-3 rounded-lg border border-outline-gray-2 p-4"
        >
          <span class="text-base font-medium text-ink-gray-8">
            {{ __('No campaign to send yet') }}
          </span>
          <span class="text-p-sm text-ink-gray-6">
            {{
              __(
                'A campaign is an automation that starts «Started by Hand», switched on: make one in Automations, with the messages it sends.',
              )
            }}
          </span>
          <Button
            icon-left="zap"
            :label="__('Go to Automations')"
            @click="vaiAlleAutomazioni"
          />
        </div>
        <fieldset v-else class="flex flex-col gap-2">
          <legend class="mb-2 text-base font-medium text-ink-gray-8">
            {{ __('Which campaign') }}
          </legend>
          <SceltaRadio
            v-for="campagna in campagne.data"
            :key="campagna.name"
            v-model="scelta"
            nome="campagna-da-mandare"
            :scelta="{
              value: campagna.name,
              label: campagna.title,
              description: descrizione(campagna),
            }"
          />
        </fieldset>

        <section v-if="scelta" class="flex flex-col gap-3" aria-live="polite">
          <div v-if="anteprima.loading" class="flex justify-center py-6">
            <LoaderMark />
          </div>
          <ErrorMessage
            v-else-if="anteprima.error"
            :message="messaggio(anteprima.error)"
          />
          <template v-else-if="conti">
            <div class="dc-stat-row grid grid-cols-3 gap-3">
              <StatTile
                :label="__('In the list')"
                :value="numero(conti.total)"
              />
              <StatTile
                :label="__('To enrol')"
                :value="numero(conti.enrolled)"
                blocco
              />
              <StatTile
                :label="__('Left out', null, 'Campaign')"
                :value="numero(quantiSaltati(conti.skipped))"
              />
            </div>
            <div
              v-if="righe.length"
              class="divide-y divide-outline-gray-1 rounded-lg border border-outline-gray-2 px-4"
            >
              <div
                v-for="riga in righe"
                :key="riga.chiave"
                class="flex items-baseline justify-between gap-3 py-2.5"
              >
                <span class="min-w-0 text-p-base text-ink-gray-8">
                  {{ riga.testo }}
                </span>
                <span class="shrink-0 text-base font-medium text-ink-gray-8">
                  {{ numero(riga.quanti) }}
                </span>
              </div>
            </div>
            <p class="text-p-sm text-ink-gray-6">
              {{
                __(
                  'Every message waits for the consent, a STOP, the promotional hours and the time window of the automation, as an automation started by an event does.',
                )
              }}
            </p>
            <p v-if="conti.demo" class="text-p-sm text-ink-gray-6">
              {{
                conti.demo === 1
                  ? __(
                      '1 person of the list is of the demo data: what the campaign writes to them stays in {brand}.',
                    )
                  : __(
                      '{0} people of the list are of the demo data: what the campaign writes to them stays in {brand}.',
                      [numero(conti.demo)],
                    )
              }}
            </p>
          </template>
        </section>
        <ErrorMessage :message="errore" />
      </div>
    </template>
    <template #actions>
      <div class="dialog-footer flex flex-wrap justify-end gap-2">
        <Button :label="__('Cancel')" @click="show = false" />
        <Button
          v-if="campagne.data?.length"
          variant="solid"
          :label="etichettaInvio"
          :disabled="!conti?.enrolled || anteprima.loading"
          :loading="invio"
          @click="invia"
        />
      </div>
    </template>
  </Dialog>
</template>

<script setup>
import SceltaRadio from '@/components/Settings/Invoicing/SceltaRadio.vue'
import StatTile from '@/components/Espresso/StatTile.vue'
import LoaderMark from '@/components/Espresso/LoaderMark.vue'
import {
  fonteDellaLista,
  quantiSaltati,
  righeDeiSalti,
  vieDellaCampagna,
} from '@/utils/campagne'
import {
  Button,
  Dialog,
  ErrorMessage,
  call,
  createResource,
  toast,
} from 'frappe-ui'
import { appLocale } from '@/utils/locale'
import { computed, ref, watch } from 'vue'
import { useRouter } from 'vue-router'

const props = defineProps({
  // the view's filters, or the rows chosen (then the filters do not count)
  filters: { type: Object, default: () => ({}) },
  names: { type: Array, default: null },
  // the view's name, for the words and the report
  vista: { type: String, default: '' },
})
const emit = defineEmits(['sent'])
const show = defineModel({ type: Boolean })
const router = useRouter()

const scelta = ref('')
const errore = ref('')
const invio = ref(false)

const fonte = computed(() =>
  fonteDellaLista({ scelti: props.names?.length || 0, vista: props.vista }, __),
)

const campagne = createResource({
  url: 'crm.automation.campagne.get_campaigns_to_send',
  auto: true,
  onSuccess(dati) {
    // one campaign: chosen already
    if (dati?.length === 1) scelta.value = dati[0].name
  },
})

function parametri() {
  return props.names?.length
    ? { names: JSON.stringify(props.names) }
    : { filters: JSON.stringify(props.filters || {}) }
}

const anteprima = createResource({
  url: 'crm.automation.campagne.preview_campaign',
  makeParams: () => ({ automation: scelta.value, ...parametri() }),
})

watch(scelta, (nome) => {
  errore.value = ''
  if (nome) anteprima.fetch()
})

const conti = computed(() =>
  anteprima.data?.automation === scelta.value ? anteprima.data : null,
)

const righe = computed(() =>
  righeDeiSalti(conti.value?.skipped, conti.value?.channels, __),
)

const etichettaInvio = computed(() => {
  const quanti = conti.value?.enrolled || 0
  if (quanti === 1) return __('Enrol 1 person')
  return quanti
    ? __('Enrol {0} people', [numero(quanti)])
    : __('Enrol', null, 'Campaign')
})

function descrizione(campagna) {
  const vie = vieDellaCampagna(campagna.channels, __)
  return campagna.marketing_consent
    ? __('{0} · only to who agreed to marketing', [vie])
    : vie
}

function numero(valore) {
  return new Intl.NumberFormat(appLocale()).format(valore || 0)
}

function messaggio(errore) {
  return errore?.messages?.join(' ') || errore?.message || ''
}

function vaiAlleAutomazioni() {
  show.value = false
  router.push({ name: 'Automations' })
}

async function invia() {
  invio.value = true
  errore.value = ''
  try {
    await call('crm.automation.campagne.send_campaign', {
      automation: scelta.value,
      ...parametri(),
      source: fonte.value,
    })
    toast.success(
      __(
        "The campaign is being sent: the report will be on the automation's Enrolments.",
      ),
    )
    show.value = false
    emit('sent')
  } catch (e) {
    errore.value = messaggio(e)
  } finally {
    invio.value = false
  }
}
</script>
