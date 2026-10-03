<!--
  Copyright (c) 2026, NPM2 Solutions Srl and contributors
  For license information, please see license.txt

  The contacts on a phone (docs/progetto-ghl/29): the people of the companies,
  found by typing a name, a company, an email or a number written any way; one
  line each - who, where they work or how to reach them - and the call a thumb
  away. The list grows as it scrolls.
-->
<template>
  <div class="flex min-h-0 flex-1 flex-col">
    <div class="shrink-0 px-3 pb-2 pt-1">
      <TextInput
        v-model="testo"
        type="search"
        size="md"
        :placeholder="__('Name, company, number or email')"
        :aria-label="__('Search contacts')"
        autocomplete="off"
      >
        <template #prefix>
          <span
            class="lucide-search size-4 text-ink-gray-5"
            aria-hidden="true"
          />
        </template>
      </TextInput>
    </div>

    <div
      ref="contenitore"
      class="min-h-0 flex-1 overflow-y-auto pb-20"
      @scroll.passive="forseAltre"
    >
      <div
        v-for="contatto in righe"
        :key="contatto.name"
        class="flex items-center border-b border-outline-gray-1"
      >
        <router-link
          :to="{ name: 'Contact', params: { contactId: contatto.name } }"
          class="flex min-h-[3.75rem] min-w-0 flex-1 items-center gap-3 py-2.5 pl-3 active:bg-surface-gray-2"
        >
          <Avatar
            :image="contatto.image"
            :label="nomeDi(contatto)"
            size="xl"
            class="shrink-0"
          />
          <span class="flex min-w-0 flex-1 flex-col">
            <span class="truncate text-base-medium text-ink-gray-9">
              {{ nomeDi(contatto) }}
            </span>
            <span
              v-if="rigaDi(contatto)"
              class="truncate text-p-sm text-ink-gray-5"
            >
              {{ rigaDi(contatto) }}
            </span>
          </span>
        </router-link>
        <a
          v-if="numeroDi(contatto)"
          :href="indirizzoTel(numeroDi(contatto))"
          class="touch-target ml-1 mr-2 flex size-9 shrink-0 items-center justify-center rounded-full text-ink-gray-6 active:bg-surface-gray-3"
          :aria-label="__('Call {0}', [nomeDi(contatto)])"
        >
          <span class="lucide-phone size-4" aria-hidden="true" />
        </a>
        <span v-else class="mr-2 size-9 shrink-0" />
      </div>

      <div v-if="carica.loading" class="flex justify-center py-6">
        <LoadingIndicator class="size-5" />
      </div>
      <p
        v-else-if="!righe.length && testo.trim()"
        class="px-6 py-12 text-center text-p-base text-ink-gray-5"
      >
        {{ __('Nobody found for «{0}».', [testo.trim()]) }}
      </p>
      <EmptyState
        v-else-if="!righe.length && carica.fetched"
        :title="__('No contacts yet')"
        :text="
          puo('persone.scrivi')
            ? __(
                'The people of the companies you work with: add one with the + button.',
              )
            : ''
        "
      />
    </div>
  </div>
</template>

<script setup>
import EmptyState from '@/components/Espresso/EmptyState.vue'
import { usersStore } from '@/stores/users'
import { indirizzoTel, mascherato } from '@/utils/schedaPersona'
import {
  Avatar,
  LoadingIndicator,
  TextInput,
  createResource,
  debounce,
} from 'frappe-ui'
import { ref, watch } from 'vue'

const { puo } = usersStore()

const testo = ref('')
const righe = ref([])
const altre = ref(false)
const contenitore = ref(null)

const carica = createResource({
  url: 'crm.api.sul_telefono.get_contacts',
  onSuccess(dati) {
    righe.value = dati.start ? [...righe.value, ...dati.rows] : dati.rows
    altre.value = dati.more
  },
})

function cerca() {
  carica.submit({ text: testo.value.trim(), start: 0 })
}

watch(testo, debounce(cerca, 300))
cerca()

// near the bottom: the next page, once
function forseAltre() {
  const el = contenitore.value
  if (!el || !altre.value || carica.loading) return
  if (el.scrollTop + el.clientHeight < el.scrollHeight - 300) return
  carica.submit({ text: testo.value.trim(), start: righe.value.length })
}

function nomeDi(contatto) {
  return contatto.full_name || contatto.first_name || contatto.name
}

// a masked number (Marketing's) is none to call
function numeroDi(contatto) {
  return (
    [contatto.mobile_no, contatto.phone].find((n) => n && !mascherato(n)) || ''
  )
}

// the line under the name: where they work, else how to reach them
function rigaDi(contatto) {
  return (
    contatto.company_name ||
    [contatto.mobile_no, contatto.phone, contatto.email_id].find(
      (valore) => valore && !mascherato(valore),
    ) ||
    ''
  )
}

defineExpose({ ricarica: cerca })
</script>
