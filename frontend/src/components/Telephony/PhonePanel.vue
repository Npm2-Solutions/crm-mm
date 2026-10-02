<!--
  Copyright (c) 2026, NPM2 Solutions Srl and contributors
  For license information, please see license.txt

  The phone at hand (docs/progetto-ghl/34), what the phone button at the top of
  every page opens: a number or a name, the keypad, the call; the last calls,
  the ones nobody took in red; the way to the callbacks owed, the round of
  calls and the whole register. Calling goes through the centre's telephony
  (`makeCall`), whose server says yes or no before anything leaves.
-->
<template>
  <div class="flex flex-col gap-3 p-3">
    <template v-if="puoChiamare">
      <div class="relative">
        <TextInput
          ref="campo"
          v-model="testo"
          size="md"
          :placeholder="__('Number or name')"
          :aria-label="__('Number or name')"
          autocomplete="off"
          @keydown.enter.prevent="chiama"
        >
          <template #suffix>
            <button
              v-if="testo"
              type="button"
              class="touch-target grid size-5 place-items-center rounded text-ink-gray-5 hover:text-ink-gray-8"
              :aria-label="__('Delete')"
              @click="testo = cancella(testo)"
            >
              <span class="lucide-delete size-4" aria-hidden="true" />
            </button>
          </template>
        </TextInput>
      </div>

      <!-- people found by name or by number: a tap puts their number in -->
      <div
        v-if="trovate.length"
        class="-mx-1 flex max-h-44 flex-col overflow-y-auto"
        role="listbox"
        :aria-label="__('People')"
      >
        <button
          v-for="persona in trovate"
          :key="persona.name"
          type="button"
          role="option"
          class="flex items-center gap-2 rounded px-1 py-1.5 text-left hover:bg-surface-gray-2"
          @click="scegli(persona)"
        >
          <Avatar size="sm" :label="persona.lead_name" :image="persona.image" />
          <span class="min-w-0 flex-1">
            <span class="block truncate text-sm text-ink-gray-8">
              {{ persona.lead_name }}
            </span>
            <span class="block truncate text-xs text-ink-gray-5">
              {{ persona.mobile_no || persona.phone }}
            </span>
          </span>
        </button>
      </div>
      <div
        v-else-if="scelta"
        class="-mt-1 truncate px-1 text-xs text-ink-gray-6"
      >
        {{ scelta }}
      </div>

      <!-- the keypad, as a phone has it -->
      <div
        class="grid grid-cols-3 gap-1.5"
        role="group"
        :aria-label="__('Keypad')"
      >
        <button
          v-for="tasto in TASTI.flat()"
          :key="tasto"
          type="button"
          class="touch-target h-10 rounded-md bg-surface-gray-2 text-lg tabular-nums text-ink-gray-8 hover:bg-surface-gray-3 active:bg-surface-gray-4"
          @click="premi(tasto)"
        >
          {{ tasto }}
        </button>
      </div>
      <Button
        variant="solid"
        size="md"
        class="w-full"
        :label="__('Call')"
        :disabled="!daChiamare"
        @click="chiama"
      >
        <template #prefix>
          <PhoneIcon class="size-4" />
        </template>
      </Button>
    </template>

    <!-- what the answering service promised, owed now -->
    <router-link
      v-if="dovute"
      :to="{ name: 'Dialer' }"
      class="flex items-center justify-between gap-2 rounded-md bg-[var(--brand-subtle)] px-3 py-2 text-sm text-[var(--on-brand-subtle)] hover:bg-[var(--brand-subtle-hover)]"
      @click="emit('done')"
    >
      <span>{{ __('To call back now') }}</span>
      <span class="font-semibold tabular-nums">{{ dovute }}</span>
    </router-link>

    <div v-if="chiamate.length" class="flex flex-col">
      <div
        class="mb-1 px-1 text-[11px] font-medium uppercase tracking-wide text-ink-gray-5"
      >
        {{ __('Last calls') }}
      </div>
      <div
        v-for="c in chiamate"
        :key="c.name"
        class="flex items-center gap-2 rounded px-1 py-1.5 hover:bg-surface-gray-2"
      >
        <span
          class="size-4 shrink-0"
          :class="[
            c.missed
              ? 'lucide-phone-missed text-ink-red-6'
              : c.type === 'Incoming'
                ? 'lucide-phone-incoming text-ink-gray-5'
                : 'lucide-phone-outgoing text-ink-gray-5',
          ]"
          aria-hidden="true"
        />
        <component
          :is="paginaDi(c) ? 'router-link' : 'span'"
          :to="paginaDi(c) || undefined"
          class="min-w-0 flex-1"
          @click="paginaDi(c) && emit('done')"
        >
          <span
            class="block truncate text-sm"
            :class="c.missed ? 'text-ink-red-7' : 'text-ink-gray-8'"
          >
            {{ c.person || c.number || __('Unknown') }}
          </span>
          <span class="block truncate text-xs text-ink-gray-5">
            {{
              [
                c.missed
                  ? __('Missed')
                  : c.type === 'Incoming'
                    ? __('Incoming')
                    : __('Outgoing'),
                quandoChiamata(c.when, new Date(), lingua, __('yesterday')),
              ].join(' · ')
            }}
          </span>
        </component>
        <Button
          v-if="puoChiamare && c.number"
          variant="ghost"
          size="sm"
          class="touch-target shrink-0"
          :tooltip="__('Call back')"
          :aria-label="__('Call back')"
          @click="richiama(c)"
        >
          <template #icon>
            <PhoneIcon class="size-3.5" />
          </template>
        </Button>
      </div>
    </div>
    <div
      v-else-if="pannello.data && !puoChiamare"
      class="px-1 py-2 text-sm text-ink-gray-5"
    >
      {{ __('No calls yet') }}
    </div>

    <div
      class="flex flex-wrap items-center gap-x-3 gap-y-1 border-t border-outline-gray-1 pt-2 text-sm"
    >
      <router-link
        v-if="puo('telefono.registro')"
        :to="{ name: 'Call Logs' }"
        class="text-ink-gray-7 hover:text-ink-gray-9"
        @click="emit('done')"
      >
        {{ __('All calls') }}
      </router-link>
      <router-link
        v-if="puoChiamare"
        :to="{ name: 'Dialer' }"
        class="text-ink-gray-7 hover:text-ink-gray-9"
        @click="emit('done')"
      >
        {{ __('Call round') }}
      </router-link>
    </div>
  </div>
</template>

<script setup>
import PhoneIcon from '@/components/Icons/PhoneIcon.vue'
import { globalStore } from '@/stores/global'
import { usersStore } from '@/stores/users'
import { TASTI } from '@/utils/chiamate'
import {
  cancella,
  daComporre,
  digita,
  eNumero,
  paginaDi,
  quandoChiamata,
} from '@/utils/telefono'
import { usePannelloTelefono } from '@/composables/pannelloTelefono'
import { Avatar, TextInput, createResource } from 'frappe-ui'
import { useDebounceFn } from '@vueuse/core'
import { computed, nextTick, onMounted, ref, watch } from 'vue'

const emit = defineEmits(['done'])

const { makeCall } = globalStore()
const { puo } = usersStore()
const { pannello, dovute } = usePannelloTelefono()

const lingua = window.navigator?.language || 'it-IT'
const puoChiamare = computed(() => puo('telefono.chiama'))

const testo = ref('')
// the person whose number the keypad holds, when it was chosen from the list
const scelta = ref('')
const numeroScelto = ref('')
const campo = ref(null)

const daChiamare = computed(() =>
  eNumero(testo.value) ? daComporre(testo.value) : '',
)

const chiamate = computed(() => pannello.data?.calls || [])

const ricerca = createResource({
  url: 'crm.telephony.pannello.find_people',
})
const trovate = computed(() =>
  testo.value.trim().length >= 2 && !scelta.value ? ricerca.data || [] : [],
)

const cerca = useDebounceFn((valore) => {
  if (valore.trim().length >= 2) ricerca.submit({ text: valore })
}, 250)

watch(testo, (valore) => {
  if (scelta.value && valore !== numeroScelto.value) scelta.value = ''
  cerca(valore)
})

function premi(tasto) {
  testo.value = digita(eNumero(testo.value) ? testo.value : '', tasto)
}

function scegli(persona) {
  numeroScelto.value = persona.mobile_no || persona.phone
  scelta.value = persona.lead_name
  testo.value = numeroScelto.value
}

function chiama() {
  if (!daChiamare.value) return
  makeCall(daChiamare.value)
  emit('done')
}

function richiama(chiamata) {
  makeCall(chiamata.number)
  emit('done')
}

onMounted(async () => {
  pannello.reload()
  await nextTick()
  campo.value?.el?.focus?.()
})
</script>
