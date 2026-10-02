<!--
  Copyright (c) 2026, NPM2 Solutions Srl and contributors
  For license information, please see license.txt

  Settings > Email > Accounts: {brand}'s own emails (doc 51).

  Reminders, codes, confirmations and notifications leave through the sending
  service the agency runs for every centre, in the centre's name: the centre sets
  nothing up, it only says where the answers go. The service itself - its server,
  syncing it after a change - is the agency's.
-->
<template>
  <section
    v-if="dati"
    class="flex flex-col gap-4 rounded-xl border border-outline-gray-2 px-4 py-4"
  >
    <div class="flex items-start gap-3">
      <LucideSend class="mt-0.5 size-4 shrink-0 text-ink-gray-5" />
      <div class="flex min-w-0 flex-col gap-1">
        <h3 class="text-base-semibold text-ink-gray-8">
          {{ __("{brand}'s emails") }}
        </h3>
        <p class="text-p-sm text-ink-gray-6">
          {{
            dati.active
              ? __(
                  "Reminders, codes, confirmations and notifications leave from {brand}'s sending service, in the centre's name. People read:",
                )
              : __(
                  "Reminders, codes, confirmations and notifications leave from the centre's mailbox that sends them.",
                )
          }}
        </p>
        <span
          v-if="dati.active && dati.sender"
          class="break-all text-p-sm-medium text-ink-gray-8"
        >
          {{ dati.sender }}
        </span>
      </div>
    </div>

    <!-- where the answers go: the one thing the centre chooses -->
    <div
      v-if="dati.active"
      class="flex flex-col gap-2 border-t border-outline-gray-2 pt-4"
    >
      <span class="text-p-sm-medium text-ink-gray-8">
        {{ __('Answers go to') }}
      </span>
      <div class="flex items-start gap-2 max-md:flex-col max-md:items-stretch">
        <FormControl
          v-model="scelta"
          class="min-w-0 flex-1"
          type="select"
          :options="opzioni"
        />
        <FormControl
          v-if="scelta === ALTRO"
          v-model="altro"
          class="min-w-0 flex-1"
          type="email"
          :placeholder="__('reception@yourcentre.com')"
        />
        <Button
          class="shrink-0"
          variant="solid"
          :label="__('Save')"
          :disabled="!cambiato"
          :loading="salvando"
          @click="salvaRisposte"
        />
      </div>
      <ErrorMessage v-if="errore" :message="errore" />
      <p
        v-else-if="risposteSenzaCasella(dati)"
        class="text-p-sm text-ink-amber-8"
      >
        {{
          __(
            'Nobody reads the answers yet: add a mailbox that receives, or write an address.',
          )
        }}
      </p>
      <p v-else-if="scelta === ALTRO" class="text-p-sm text-ink-gray-5">
        {{
          __(
            'An address not read in {brand}: the answers stay in that mailbox, not on the person’s page.',
          )
        }}
      </p>
      <p v-else class="text-p-sm text-ink-gray-5">
        {{
          __(
            'People answer a reminder as any email, and the answer arrives on their page.',
          )
        }}
      </p>
    </div>

    <!-- the agency's: the service's server, and following a change now -->
    <div
      v-if="dati.agency"
      class="flex items-start justify-between gap-3 border-t border-outline-gray-2 pt-4 max-md:flex-col"
    >
      <div class="flex min-w-0 flex-col gap-0.5 text-p-sm">
        <span class="text-ink-gray-5">
          {{ __('Sending service, for the agency') }}
        </span>
        <span class="break-all text-ink-gray-8">
          {{
            dati.server ||
            __(
              'Not configured: write it in the server’s configuration (dottorcloud_posta), then sync.',
            )
          }}
        </span>
      </div>
      <Button
        class="shrink-0"
        :label="__('Sync now')"
        :loading="sincronizzando"
        @click="sincronizza"
      />
    </div>
  </section>
</template>

<script setup>
import { Button, call, ErrorMessage, FormControl, toast } from 'frappe-ui'
import { computed, ref, watch } from 'vue'
import LucideSend from '~icons/lucide/send'
import {
  ALTRO,
  rispostaDaSalvare,
  risposteSenzaCasella,
  sceltaDelleRisposte,
} from '@/utils/caselle'

const props = defineProps({
  // the resource of `crm.posta.servizio.get_sending_service`
  stato: { type: Object, required: true },
})

const dati = computed(() => props.stato.data)

const scelta = ref('')
const altro = ref('')
watch(
  dati,
  (valore) => {
    if (!valore) return
    const iniziale = sceltaDelleRisposte(valore)
    scelta.value = iniziale.scelta
    altro.value = iniziale.altro
  },
  { immediate: true },
)

const opzioni = computed(() => {
  const principale = dati.value?.reply_to_main
  return [
    {
      label: principale
        ? __('The main mailbox ({0})', [principale])
        : __('The main mailbox (none yet)'),
      value: '',
    },
    ...(dati.value?.inboxes || [])
      .filter((indirizzo) => indirizzo !== principale)
      .map((indirizzo) => ({ label: indirizzo, value: indirizzo })),
    { label: __('Another address…'), value: ALTRO },
  ]
})

const cambiato = computed(
  () =>
    rispostaDaSalvare(scelta.value, altro.value) !==
    (dati.value?.reply_to_chosen || ''),
)

const errore = ref('')
const salvando = ref(false)
async function salvaRisposte() {
  errore.value = ''
  salvando.value = true
  try {
    const nuovo = await call('crm.posta.servizio.set_reply_address', {
      address: rispostaDaSalvare(scelta.value, altro.value),
    })
    props.stato.setData(nuovo)
    toast.success(__('Saved'))
  } catch (e) {
    errore.value = e.messages?.[0] || __('Could not save the address')
  } finally {
    salvando.value = false
  }
}

const sincronizzando = ref(false)
async function sincronizza() {
  sincronizzando.value = true
  try {
    props.stato.setData(await call('crm.posta.servizio.sync_sending_service'))
    toast.success(__('The sending service is up to date'))
  } catch (e) {
    toast.error(e.messages?.[0] || __('Could not sync the sending service'))
  } finally {
    sincronizzando.value = false
  }
}
</script>
