<!--
  Copyright (c) 2026, NPM2 Solutions Srl and contributors
  For license information, please see license.txt

  A number the centre already has, with Telnyx (doc 64). In its own Telnyx
  account: DottorCloud works there already, so no code is asked again - the
  numbers it does not manage, and the one chosen pointed at DottorCloud; one on
  the centre's switchboard stays there. With another operator: shown on calls
  once Telnyx verified it, its calls forwarded to a number of the centre's here,
  or the number ported to Telnyx and then taken in.
-->
<template>
  <Dialog
    v-model="show"
    :options="{ title: __('A number the centre already has'), size: 'xl' }"
  >
    <template #body-content>
      <div class="flex flex-col gap-4">
        <div
          class="grid grid-cols-2 gap-2 max-md:grid-cols-1"
          role="radiogroup"
        >
          <SceltaRadio
            v-model="dove"
            nome="dove-e-il-numero-telnyx"
            :scelta="{
              value: 'telnyx',
              label: __('In the centre’s Telnyx account'),
              description: __('It answers on {brand} from now on.'),
            }"
          />
          <SceltaRadio
            v-model="dove"
            nome="dove-e-il-numero-telnyx"
            :scelta="{
              value: 'operatore',
              label: __('With another operator'),
              description: __(
                'TIM, Vodafone, Fastweb…: forwarded, or ported to Telnyx.',
              ),
            }"
          />
        </div>

        <template v-if="dove === 'telnyx'">
          <p v-if="!delCentro" class="text-p-sm text-ink-amber-8">
            {{
              __(
                'The phone goes through the agency’s Telnyx account: a number of the centre’s cannot be taken into it. Forward its calls instead.',
              )
            }}
          </p>
          <div
            v-else-if="spostato"
            class="flex flex-col gap-1 rounded bg-surface-gray-1 p-3"
          >
            <span class="text-p-base-medium text-ink-gray-8">
              {{ __('{0} answers on {brand} now.', [spostato]) }}
            </span>
            <span class="text-p-sm text-ink-gray-6">
              {{
                __(
                  'Its calls reach {brand}, and its SMS if it can send them: choose who answers it in the phone’s settings.',
                )
              }}
            </span>
          </div>
          <template v-else>
            <p class="text-p-sm text-ink-gray-6">
              {{
                __(
                  'The numbers of the account that do not reach {brand} yet. One that answers on another application of yours leaves it; one on your switchboard stays there.',
                )
              }}
            </p>
            <ErrorMessage :message="errore" />
            <div
              v-if="elenco.loading && !elenco.data"
              class="flex justify-center py-4"
            >
              <LoadingIndicator class="size-5" />
            </div>
            <div v-else-if="elenco.data" class="flex flex-col gap-2">
              <p v-if="!elenco.data.length" class="text-p-sm text-ink-gray-5">
                {{ __('Every number of the account reaches {brand} already.') }}
              </p>
              <div
                v-if="movibili.length"
                class="flex flex-col gap-2"
                role="radiogroup"
              >
                <SceltaRadio
                  v-for="numero in movibili"
                  :key="numero.sid"
                  v-model="scelto"
                  nome="numero-da-prendere"
                  :scelta="{
                    value: numero.sid,
                    label: numero.number,
                    description: descrizione(numero),
                  }"
                />
              </div>
              <div
                v-for="numero in fermi"
                :key="numero.sid"
                class="flex flex-col gap-0.5 rounded-lg border border-outline-gray-1 px-3 py-2.5"
              >
                <span class="text-p-base text-ink-gray-5">
                  {{ numero.number }}
                </span>
                <span class="text-p-sm text-ink-gray-5">
                  {{ numero.reason }}
                </span>
              </div>
            </div>
          </template>
        </template>

        <div v-else class="flex flex-col gap-4 text-p-sm text-ink-gray-7">
          <div class="flex flex-col gap-1.5">
            <span class="text-p-base-medium text-ink-gray-8">
              {{ __('Show it on the calls you make') }}
            </span>
            <span>
              {{
                __(
                  'Telnyx verifies it with a call or an SMS and a code, with no document: calls to it keep ringing where they ring now. In Italy it is shown as far as the operators let it (AGCOM, August 2025): to be sure, port it.',
                )
              }}
            </span>
            <Button
              class="self-start"
              variant="subtle"
              :label="__('Verify it')"
              @click="emit('verifica')"
            />
          </div>
          <div class="flex flex-col gap-1">
            <span class="text-p-base-medium text-ink-gray-8">
              {{ __('Forward its calls') }}
            </span>
            <span>
              {{
                __(
                  'Ask the operator to forward the calls to one of the centre’s numbers in {brand}: they arrive here, and the number stays where it is. Its SMS do not follow.',
                )
              }}
            </span>
          </div>
          <div class="flex flex-col gap-1.5">
            <span class="text-p-base-medium text-ink-gray-8">
              {{ __('Port it to Telnyx') }}
            </span>
            <span>
              {{
                __(
                  'Telnyx takes it with its own port-in request, a geographic number in a few weeks. Once it is in the centre’s Telnyx account, take it in here with «In the centre’s Telnyx account».',
                )
              }}
            </span>
            <Button
              class="self-start"
              variant="subtle"
              icon-left="lucide-external-link"
              :label="__('Porting to Telnyx, for Italy')"
              @click="apri(TELNYX.portabilita)"
            />
          </div>
        </div>
      </div>
    </template>
    <template #actions>
      <div class="dialog-footer flex justify-end gap-2">
        <Button
          v-if="
            spostato || dove === 'operatore' || !delCentro || !movibili.length
          "
          variant="solid"
          :label="__('Close')"
          @click="show = false"
        />
        <Button
          v-else
          variant="solid"
          :label="__('Answer it on {brand}')"
          :disabled="!scelto"
          :loading="sposta.loading"
          @click="prendiIlNumero"
        />
      </div>
    </template>
  </Dialog>
</template>

<script setup>
import SceltaRadio from '@/components/Settings/Invoicing/SceltaRadio.vue'
import { TELNYX } from '@/utils/telnyx'
import {
  createResource,
  Dialog,
  ErrorMessage,
  LoadingIndicator,
} from 'frappe-ui'
import { computed, ref, watch } from 'vue'

const props = defineProps({
  // whether the phone goes through the centre's own Telnyx account
  delCentro: { type: Boolean, default: false },
})
const emit = defineEmits(['moved', 'verifica'])
const show = defineModel({ type: Boolean })

const dove = ref('telnyx')
const scelto = ref('')
const spostato = ref('')
const errore = ref('')

const elenco = createResource({
  url: 'crm.telephony.telnyx.trasloco.get_account_numbers',
  method: 'POST',
  onError: (e) => (errore.value = e.messages?.[0] || e.message),
})
const sposta = createResource({
  url: 'crm.telephony.telnyx.trasloco.move_number',
  method: 'POST',
  onSuccess: (esito) => {
    spostato.value = esito.number
    emit('moved')
  },
  onError: (e) => (errore.value = e.messages?.[0] || e.message),
})

const movibili = computed(() => (elenco.data || []).filter((n) => !n.reason))
const fermi = computed(() => (elenco.data || []).filter((n) => n.reason))

// its name in the account, and the application it leaves
function descrizione(numero) {
  const parti = []
  if (numero.label) parti.push(numero.label)
  if (numero.now_on) parti.push(__('now on {0}', [numero.now_on]))
  return parti.join(' · ')
}

function prendiIlNumero() {
  errore.value = ''
  sposta.submit({ number_sid: scelto.value })
}

function apri(indirizzo) {
  window.open(indirizzo, '_blank', 'noopener')
}

// the account's numbers asked once the dialog shows them
watch(
  [show, dove],
  ([aperto, dove_]) => {
    if (!aperto) {
      scelto.value = ''
      spostato.value = ''
      errore.value = ''
      elenco.reset()
      return
    }
    if (dove_ === 'telnyx' && props.delCentro && !elenco.data) {
      elenco.submit()
    }
  },
  { immediate: true },
)

// the agency's account: only the other operator's way applies
watch(
  () => props.delCentro,
  (delCentro) => {
    if (!delCentro) dove.value = 'operatore'
  },
  { immediate: true },
)
</script>
