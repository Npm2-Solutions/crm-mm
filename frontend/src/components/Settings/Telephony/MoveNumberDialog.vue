<!--
  Copyright (c) 2026, NPM2 Solutions Srl and contributors
  For license information, please see license.txt

  A number the centre already has (doc 52, sixth part). In its own Twilio account:
  the account's codes pasted again - for this alone, never kept - the numbers
  there, and the one chosen moved into DottorCloud's space with its documents and
  its address, answering on DottorCloud. With another operator: its calls
  forwarded to a number of the centre's here, or the number ported to Twilio and
  then moved.
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
            nome="dove-e-il-numero"
            :scelta="{
              value: 'twilio',
              label: __('In the centre’s Twilio account'),
              description: __(
                'It moves into {brand}’s space, with its documents.',
              ),
            }"
          />
          <SceltaRadio
            v-model="dove"
            nome="dove-e-il-numero"
            :scelta="{
              value: 'operatore',
              label: __('With another operator'),
              description: __(
                'TIM, Vodafone, Fastweb…: forwarded, or ported to Twilio.',
              ),
            }"
          />
        </div>

        <template v-if="dove === 'twilio'">
          <p v-if="!delCentro" class="text-p-sm text-ink-amber-8">
            {{
              __(
                'The space is in the agency’s Twilio account: a number of the centre’s cannot move into it. Forward its calls instead.',
              )
            }}
          </p>
          <div
            v-else-if="spostato"
            class="flex flex-col gap-1 rounded bg-surface-gray-1 p-3"
          >
            <span class="text-p-base-medium text-ink-gray-8">
              {{ __('{0} is in {brand}’s space now.', [spostato]) }}
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
                  'Paste the codes of the centre’s Twilio account again: they serve to move the number, and {brand} does not keep them.',
                )
              }}
            </p>
            <div class="grid grid-cols-2 gap-3 max-md:grid-cols-1">
              <FormControl
                v-model="codici.sid"
                :label="__('Account SID')"
                autocomplete="off"
                @update:model-value="elenco.reset()"
              />
              <FormControl
                v-model="codici.token"
                type="password"
                :label="__('Auth Token')"
                autocomplete="off"
                @update:model-value="elenco.reset()"
              />
            </div>
            <ErrorMessage :message="errore" />
            <div v-if="elenco.data" class="flex flex-col gap-2">
              <p v-if="!elenco.data.length" class="text-p-sm text-ink-gray-5">
                {{
                  __(
                    'There is no number in the account outside {brand}’s space.',
                  )
                }}
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
                  nome="numero-da-spostare"
                  :scelta="{
                    value: numero.sid,
                    label: numero.number,
                    description: numero.label,
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
              {{ __('Port it to Twilio') }}
            </span>
            <span>
              {{
                __(
                  'Twilio takes it with its own form, from the big operators, in up to six weeks. Once it is in the centre’s Twilio account, move it here with «In the centre’s Twilio account».',
                )
              }}
            </span>
            <Button
              class="self-start"
              variant="subtle"
              icon-left="lucide-external-link"
              :label="__('Porting to Twilio, for Italy')"
              @click="apri(TWILIO.portabilita)"
            />
          </div>
        </div>
      </div>
    </template>
    <template #actions>
      <div class="dialog-footer flex justify-end gap-2">
        <Button
          v-if="spostato || dove === 'operatore' || !delCentro"
          variant="solid"
          :label="__('Close')"
          @click="show = false"
        />
        <Button
          v-else-if="!elenco.data"
          variant="solid"
          :label="__('Show the numbers')"
          :loading="elenco.loading"
          @click="mostra"
        />
        <Button
          v-else
          variant="solid"
          :label="__('Move it into the space')"
          :disabled="!scelto"
          :loading="sposta.loading"
          @click="spostaIlNumero"
        />
      </div>
    </template>
  </Dialog>
</template>

<script setup>
import SceltaRadio from '@/components/Settings/Invoicing/SceltaRadio.vue'
import { TWILIO, cosaManca, pulito } from '@/utils/twilio'
import { createResource, Dialog, ErrorMessage, FormControl } from 'frappe-ui'
import { computed, reactive, ref, watch } from 'vue'

const props = defineProps({
  // whether DottorCloud's space is in the centre's own account
  delCentro: { type: Boolean, default: false },
})
const emit = defineEmits(['moved'])
const show = defineModel({ type: Boolean })

const dove = ref('twilio')
const codici = reactive({ sid: '', token: '' })
const scelto = ref('')
const spostato = ref('')
const errore = ref('')

const elenco = createResource({
  url: 'crm.telephony.trasloco.get_account_numbers',
  onError: (e) => (errore.value = e.messages?.[0] || e.message),
})
const sposta = createResource({
  url: 'crm.telephony.trasloco.move_number',
  onSuccess: (esito) => {
    spostato.value = esito.number
    // the codes served their one purpose
    codici.token = ''
    emit('moved')
  },
  onError: (e) => (errore.value = e.messages?.[0] || e.message),
})

const movibili = computed(() => (elenco.data || []).filter((n) => !n.reason))
const fermi = computed(() => (elenco.data || []).filter((n) => n.reason))

function parametri() {
  return { account_sid: pulito(codici.sid), auth_token: pulito(codici.token) }
}

function mostra() {
  const manca = cosaManca(codici.sid, codici.token)
  errore.value = manca ? __(manca) : ''
  if (manca) return
  scelto.value = ''
  elenco.submit(parametri())
}

function spostaIlNumero() {
  errore.value = ''
  sposta.submit({ ...parametri(), number_sid: scelto.value })
}

function apri(indirizzo) {
  window.open(indirizzo, '_blank', 'noopener')
}

// closed, nothing of the codes stays behind
watch(show, (aperto) => {
  if (aperto) return
  Object.assign(codici, { sid: '', token: '' })
  scelto.value = ''
  spostato.value = ''
  errore.value = ''
  elenco.reset()
})

// the agency's space: only the other operator's way applies
watch(
  () => props.delCentro,
  (delCentro) => {
    if (!delCentro) dove.value = 'operatore'
  },
  { immediate: true },
)
</script>
