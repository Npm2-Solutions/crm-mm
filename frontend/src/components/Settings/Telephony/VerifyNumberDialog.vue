<!--
  Copyright (c) 2026, NPM2 Solutions Srl and contributors
  For license information, please see license.txt

  A number the centre has with another operator, verified to be shown on the calls
  it makes (doc 52): Twilio calls it, a recorded voice in English asks for the code
  shown here, and whoever answers types it on the phone's keypad. No document is
  asked. The page asks how it went while Twilio's call goes on; Twilio says it too,
  and whoever asked hears of it if the page was closed.
-->
<template>
  <Dialog
    v-model="show"
    :options="{ title: __('Show a number of yours on calls'), size: 'lg' }"
  >
    <template #body-content>
      <!-- the number -->
      <div v-if="fase === 'numero'" class="flex flex-col gap-4">
        <p class="text-p-sm text-ink-gray-6">
          {{
            __(
              'Twilio calls the number from {0}: a recorded voice, in English, asks for a code that appears here, to type on the phone’s keypad. No document is needed: answering proves the line is the centre’s. Calls to the number keep ringing where they ring now.',
              [DA_TWILIO],
            )
          }}
        </p>
        <div class="grid grid-cols-2 gap-3 max-md:grid-cols-1">
          <FormControl
            v-model="modulo.phone_number"
            type="tel"
            :label="__('Number')"
            placeholder="+39 02 1234 5678"
            autocomplete="off"
          />
          <FormControl
            v-model="modulo.label"
            :label="__('Name')"
            :placeholder="__('Reception')"
          />
        </div>

        <p
          v-if="tipo"
          class="flex gap-1.5 rounded bg-surface-amber-1 px-3 py-2 text-p-sm text-ink-amber-8"
        >
          <span
            class="lucide-triangle-alert mt-0.5 size-3.5 shrink-0"
            aria-hidden="true"
          />
          <span>{{ avvisoItalia }}</span>
        </p>

        <div class="flex flex-col gap-3">
          <Switch
            v-model="centralino"
            :label="__('The line has a switchboard')"
            :description="
              __(
                'Twilio dials an extension once the call is answered, or waits before calling.',
              )
            "
          />
          <div
            v-if="centralino"
            class="grid grid-cols-2 gap-3 max-md:grid-cols-1"
          >
            <FormControl
              v-model="modulo.extension"
              :label="__('Digits after the answer')"
              :description="
                __('The extension, w to wait half a second: ww101.')
              "
              autocomplete="off"
            />
            <FormControl
              v-model="modulo.call_delay"
              type="number"
              :label="__('Seconds before the call')"
              :description="__('Time to get to the phone: from 0 to 60.')"
            />
          </div>
        </div>
        <ErrorMessage :message="errore" />
      </div>

      <!-- Twilio's call -->
      <div
        v-else-if="fase === 'chiamata'"
        class="flex flex-col items-center gap-4 py-2 text-center"
      >
        <p class="text-p-base text-ink-gray-7">
          {{
            __(
              'Twilio is calling {0}. Answer, and when the voice asks, type this code:',
              [numero],
            )
          }}
        </p>
        <div class="flex gap-2" :aria-label="__('Code')" role="group">
          <span
            v-for="(cifra, indice) in cifre"
            :key="indice"
            class="flex h-12 w-10 items-center justify-center rounded-lg border border-outline-gray-2 bg-surface-gray-1 text-2xl-semibold text-ink-gray-9"
          >
            {{ cifra }}
          </span>
        </div>
        <div
          class="flex items-center gap-2 text-p-sm text-ink-gray-5"
          aria-live="polite"
        >
          <LoadingIndicator class="size-3.5" />
          {{ __('Waiting for the code…') }}
        </div>
        <p class="text-p-xs text-ink-gray-5">
          {{ __('The call comes from {0}.', [DA_TWILIO]) }}
        </p>
      </div>

      <!-- how it went -->
      <div
        v-else
        class="flex flex-col items-center gap-3 py-2 text-center"
        aria-live="polite"
      >
        <span
          class="size-10"
          :class="
            fase === 'verificato'
              ? 'lucide-circle-check text-ink-green-6'
              : 'lucide-circle-x text-ink-red-6'
          "
          aria-hidden="true"
        />
        <p class="text-p-base-medium text-ink-gray-8">
          {{
            fase === 'verificato'
              ? __('{0} is verified: it can be shown on calls.', [numero])
              : __(
                  '{0} was not verified: the call was not answered or the code was not typed.',
                  [numero],
                )
          }}
        </p>
        <p
          v-if="fase === 'verificato' && tipo"
          class="text-p-sm text-ink-gray-6"
        >
          {{ avvisoItalia }}
        </p>
      </div>
    </template>

    <template #actions>
      <div class="dialog-footer flex justify-end gap-2">
        <template v-if="fase === 'numero'">
          <Button :label="__('Cancel')" @click="show = false" />
          <Button
            variant="solid"
            :label="__('Call the number')"
            :loading="avvio"
            :disabled="!modulo.phone_number.trim()"
            @click="verifica"
          />
        </template>
        <Button
          v-else-if="fase === 'chiamata'"
          :label="__('Close')"
          @click="show = false"
        />
        <template v-else-if="fase === 'fallita'">
          <Button :label="__('Close')" @click="show = false" />
          <Button
            variant="solid"
            :label="__('Try again')"
            @click="fase = 'numero'"
          />
        </template>
        <Button
          v-else
          variant="solid"
          :label="__('Done')"
          @click="show = false"
        />
      </div>
    </template>
  </Dialog>
</template>

<script setup>
import {
  DA_TWILIO,
  IN_ATTESA,
  OGNI,
  VERIFICATO,
  cifreDelCodice,
  internoPulito,
  internoValido,
  numeroItaliano,
} from '@/utils/verificati'
import {
  Dialog,
  ErrorMessage,
  FormControl,
  LoadingIndicator,
  Switch,
  call,
} from 'frappe-ui'
import { computed, onBeforeUnmount, reactive, ref, watch } from 'vue'

const props = defineProps({
  // a number to verify again, with its name
  numeroIniziale: { type: String, default: '' },
  nomeIniziale: { type: String, default: '' },
})
const emit = defineEmits(['changed'])
const show = defineModel({ type: Boolean })

const fase = ref('numero')
const modulo = reactive({
  phone_number: '',
  label: '',
  extension: '',
  call_delay: '',
})
const centralino = ref(false)
const errore = ref('')
const avvio = ref(false)
const numero = ref('')
const cifre = ref([])
let attesa = null

const tipo = computed(() =>
  numeroItaliano(fase.value === 'numero' ? modulo.phone_number : numero.value),
)
const avvisoItalia = computed(() =>
  tipo.value === 'mobile'
    ? __(
        'An Italian mobile is not shown on calls to Italy since November 2025 (AGCOM): verify it only to call abroad.',
      )
    : __(
        'In Italy it is shown as far as the operators let it: since August 2025 an Italian operator may block a call from abroad that shows an Italian landline of another network (AGCOM). To be sure it is shown, move the number to Twilio.',
      ),
)

async function verifica() {
  errore.value = ''
  if (centralino.value && !internoValido(modulo.extension)) {
    errore.value = __(
      'The extension takes digits, * and #, and w for half a second’s wait: at most 32.',
    )
    return
  }
  avvio.value = true
  try {
    const esito = await call('crm.telephony.verificati.verify_number', {
      phone_number: modulo.phone_number,
      label: modulo.label || null,
      extension: centralino.value ? internoPulito(modulo.extension) : null,
      call_delay: centralino.value ? modulo.call_delay || 0 : 0,
    })
    numero.value = esito.phone_number
    emit('changed')
    if (esito.status === VERIFICATO) {
      // verified already in Twilio: nothing to type
      fase.value = 'verificato'
      return
    }
    cifre.value = cifreDelCodice(esito.validation_code)
    fase.value = 'chiamata'
    chiediPiuTardi()
  } catch (e) {
    errore.value = e.messages?.[0] || __('Could not start the verification')
  } finally {
    avvio.value = false
  }
}

function chiediPiuTardi() {
  clearTimeout(attesa)
  attesa = setTimeout(chiedi, OGNI)
}

// while Twilio's call goes on: what Twilio said, or what it has now
async function chiedi() {
  if (!show.value || fase.value !== 'chiamata') return
  try {
    const esito = await call('crm.telephony.verificati.verification_state', {
      phone_number: numero.value,
    })
    if (fase.value !== 'chiamata') return
    if (esito.status === IN_ATTESA) return chiediPiuTardi()
    fase.value = esito.status === VERIFICATO ? 'verificato' : 'fallita'
    emit('changed')
  } catch {
    // a moment of silence on the network: ask again
    chiediPiuTardi()
  }
}

// opened again: from the start, with the number to verify again if there is one
watch(
  show,
  (aperto) => {
    clearTimeout(attesa)
    if (!aperto) return
    fase.value = 'numero'
    errore.value = ''
    centralino.value = false
    Object.assign(modulo, {
      phone_number: props.numeroIniziale,
      label: props.nomeIniziale,
      extension: '',
      call_delay: '',
    })
  },
  { immediate: true },
)

onBeforeUnmount(() => clearTimeout(attesa))
</script>
