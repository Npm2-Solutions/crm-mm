<!--
  Copyright (c) 2026, NPM2 Solutions Srl and contributors
  For license information, please see license.txt

  The register of calls on a phone (docs/progetto-ghl/29): found by a name or a
  number written any way; one line each - with whom, which way and how it went,
  when, how long - the missed ones in red, calling back a thumb away. The line
  opens the call; the list grows as it scrolls.
-->
<template>
  <div class="flex min-h-0 flex-1 flex-col">
    <div class="shrink-0 px-3 pb-2 pt-1">
      <TextInput
        v-model="testo"
        v-bind="tastiera('cerca')"
        size="md"
        :placeholder="__('Name or number')"
        :aria-label="__('Search calls')"
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
      <div
        v-for="c in righe"
        :key="c.name"
        class="flex items-center border-b border-outline-gray-1"
      >
        <button
          type="button"
          class="flex min-h-[3.75rem] min-w-0 flex-1 items-center gap-3 py-2.5 pl-3 text-left active:bg-surface-gray-2"
          @click="emit('apri', c.name)"
        >
          <span
            class="grid size-9 shrink-0 place-items-center rounded-full"
            :class="
              versoDellaChiamata(c) === 'missed'
                ? 'bg-surface-red-2 text-ink-red-6'
                : 'bg-surface-gray-2 text-ink-gray-6'
            "
            aria-hidden="true"
          >
            <span class="size-4" :class="SEGNI[versoDellaChiamata(c)]" />
          </span>
          <span class="flex min-w-0 flex-1 flex-col">
            <span
              class="truncate text-base-medium"
              :class="
                versoDellaChiamata(c) === 'missed'
                  ? 'text-ink-red-7'
                  : 'text-ink-gray-9'
              "
            >
              {{ c.person || leggibile(c.number) || __('Unknown') }}
            </span>
            <span class="truncate text-p-sm text-ink-gray-5">
              {{ comeAndata(c) }}
            </span>
          </span>
          <span class="shrink-0 text-sm text-ink-gray-5">
            {{
              quandoChiamata(c.when, adessoDelCentro(), lingua, __('yesterday'))
            }}
          </span>
        </button>
        <a
          v-if="puoChiamare && c.number"
          href="#"
          class="touch-target ml-1 mr-2 flex size-9 shrink-0 items-center justify-center rounded-full text-ink-gray-6 active:bg-surface-gray-3"
          :aria-label="__('Call back {0}', [c.person || leggibile(c.number)])"
          @click.prevent="makeCall(c.number)"
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
        {{ __('Nothing found for «{0}».', [testo.trim()]) }}
      </p>
      <EmptyState
        v-else-if="!righe.length && carica.fetched"
        :title="__('No calls yet')"
        :text="__('The calls made and received through {brand} are kept here.')"
      />
    </div>
  </div>
</template>

<script setup>
import TiraPerAggiornare from '@/components/Mobile/TiraPerAggiornare.vue'
import { useElencoDelTelefono } from '@/composables/elencoDelTelefono'
import { tastiera } from '@/utils/tastiera'
import EmptyState from '@/components/Espresso/EmptyState.vue'
import { callEnabled } from '@/composables/telephony'
import { globalStore } from '@/stores/global'
import { usersStore } from '@/stores/users'
import { durataDellaChiamata, versoDellaChiamata } from '@/utils/sulTelefono'
import { leggibile, quandoChiamata } from '@/utils/telefono'
import { adessoDelCentro } from '@/utils/scheduler'
import { LoadingIndicator, TextInput } from 'frappe-ui'
import { computed } from 'vue'

const emit = defineEmits(['apri'])

const { puo } = usersStore()
const { makeCall } = globalStore()
const puoChiamare = computed(() => callEnabled.value && puo('telefono.chiama'))
const lingua = window.navigator?.language || 'it-IT'

// the mark of each way a call goes
const SEGNI = {
  missed: 'lucide-phone-missed',
  incoming: 'lucide-phone-incoming',
  outgoing: 'lucide-phone-outgoing',
}

const { testo, righe, contenitore, carica, cerca, forseAltre, tira } =
  useElencoDelTelefono('crm.api.sul_telefono.get_calls', 'chiamate')

// the line under the name: which way, how it went, how long
function comeAndata(c) {
  const verso = versoDellaChiamata(c)
  const parti = [
    verso === 'missed'
      ? c.left_message
        ? __('Missed · left a message')
        : __('Missed')
      : verso === 'incoming'
        ? __('Incoming')
        : __('Outgoing'),
  ]
  if (verso === 'outgoing' && c.status !== 'Completed' && c.status)
    parti.push(__(c.status))
  if (c.person && c.number) parti.push(leggibile(c.number))
  const durata = durataDellaChiamata(c.duration)
  if (durata) parti.push(durata)
  return parti.join(' · ')
}

defineExpose({ ricarica: cerca })
</script>
