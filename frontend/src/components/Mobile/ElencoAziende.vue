<!--
  Copyright (c) 2026, NPM2 Solutions Srl and contributors
  For license information, please see license.txt

  The companies on a phone (docs/progetto-ghl/29): found by typing a name, a
  website or what they do; one line each - who, what they do and where they are
  online, how many deals - the whole line opening the company. The list grows as
  it scrolls.
-->
<template>
  <div class="flex min-h-0 flex-1 flex-col">
    <div class="shrink-0 px-3 pb-2 pt-1">
      <TextInput
        v-model="testo"
        type="search"
        size="md"
        :placeholder="__('Name, website or industry')"
        :aria-label="__('Search organizations')"
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
      <!-- pulled down from the top, the list reloads -->
      <TiraPerAggiornare v-bind="tira" />
      <router-link
        v-for="azienda in righe"
        :key="azienda.name"
        :to="{
          name: 'Organization',
          params: { organizationId: azienda.name },
        }"
        class="flex min-h-[3.75rem] items-center gap-3 border-b border-outline-gray-1 px-3 py-2.5 active:bg-surface-gray-2"
      >
        <Avatar
          :image="azienda.organization_logo"
          :label="azienda.organization_name || azienda.name"
          size="xl"
          class="shrink-0"
        />
        <span class="flex min-w-0 flex-1 flex-col">
          <span class="truncate text-base-medium text-ink-gray-9">
            {{ azienda.organization_name || azienda.name }}
          </span>
          <span
            v-if="rigaDellAzienda(azienda)"
            class="truncate text-p-sm text-ink-gray-5"
          >
            {{ rigaDellAzienda(azienda) }}
          </span>
        </span>
        <span
          v-if="azienda.deals"
          class="shrink-0 rounded bg-surface-gray-2 px-1.5 py-0.5 text-xs text-ink-gray-7"
        >
          {{
            azienda.deals === 1
              ? __('1 deal')
              : __('{0} deals', [azienda.deals])
          }}
        </span>
      </router-link>

      <div v-if="carica.loading" class="flex justify-center py-6">
        <LoadingIndicator class="size-5" />
      </div>
      <p
        v-else-if="!righe.length && testo.trim()"
        class="px-6 py-12 text-center text-p-base text-ink-gray-5"
      >
        {{ __('Nothing found for «{0}».', [testo.trim()]) }}
      </p>
      <EmptyState
        v-else-if="!righe.length && carica.fetched"
        :title="__('No organizations yet')"
        :text="
          puo('persone.scrivi')
            ? __(
                'The companies your people work for: add one with the + button.',
              )
            : ''
        "
      />
    </div>
  </div>
</template>

<script setup>
import TiraPerAggiornare from '@/components/Mobile/TiraPerAggiornare.vue'
import { useTiraPerAggiornare } from '@/composables/tiraPerAggiornare'
import EmptyState from '@/components/Espresso/EmptyState.vue'
import { usersStore } from '@/stores/users'
import { rigaDellAzienda } from '@/utils/sulTelefono'
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
  url: 'crm.api.sul_telefono.get_organizations',
  onSuccess(dati) {
    righe.value = dati.start ? [...righe.value, ...dati.rows] : dati.rows
    altre.value = dati.more
  },
})

function cerca() {
  return carica.submit({ text: testo.value.trim(), start: 0 })
}

const tira = useTiraPerAggiornare(contenitore, cerca)

watch(testo, debounce(cerca, 300))
cerca()

// near the bottom: the next page, once
function forseAltre() {
  const el = contenitore.value
  if (!el || !altre.value || carica.loading) return
  if (el.scrollTop + el.clientHeight < el.scrollHeight - 300) return
  carica.submit({ text: testo.value.trim(), start: righe.value.length })
}

defineExpose({ ricarica: cerca })
</script>
