<!--
  Copyright (c) 2026, NPM2 Solutions Srl and contributors
  For license information, please see license.txt

  The notes on a phone (docs/crm/29): found by typing their title or
  their words; one line each - the title, the first words, who wrote it, about
  whom and when - the whole line opening the note. The list grows as it
  scrolls; its data from `crm.api.sul_telefono.get_notes`.
-->
<template>
  <div class="flex min-h-0 flex-1 flex-col">
    <div class="shrink-0 px-3 pb-2 pt-1">
      <TextInput
        v-model="testo"
        v-bind="tastiera('cerca')"
        size="md"
        :placeholder="__('Title or words of the note')"
        :aria-label="__('Search notes')"
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
      <button
        v-for="nota in righe"
        :key="nota.name"
        type="button"
        class="flex w-full flex-col gap-0.5 border-b border-outline-gray-1 px-3 py-3 text-left active:bg-surface-gray-2"
        @click="emit('apri', nota.name)"
      >
        <span class="truncate text-base-medium text-ink-gray-9">
          {{ nota.title || __('Note') }}
        </span>
        <span
          v-if="nota.content"
          class="line-clamp-2 text-p-sm text-ink-gray-7"
        >
          {{ nota.content }}
        </span>
        <span class="truncate text-p-sm text-ink-gray-5">
          {{ rigaDellaNota(nota) }}
        </span>
      </button>

      <!-- the list's first load is the brand's cross (the design system's
           Progress); more rows coming under the ones there, a spinner -->
      <div
        v-if="carica.loading && !righe.length"
        class="flex justify-center py-10"
      >
        <LoaderMark />
      </div>
      <div v-else-if="carica.loading" class="flex justify-center py-6">
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
        :title="__('No notes yet')"
        :text="
          puo('note.scrivi')
            ? __(
                'What is worth remembering about a person or a deal: write it with the + button.',
              )
            : ''
        "
      />
    </div>
  </div>
</template>

<script setup>
import TiraPerAggiornare from '@/components/Mobile/TiraPerAggiornare.vue'
import { useElencoDelTelefono } from '@/composables/elencoDelTelefono'
import { tastiera } from '@/utils/tastiera'
import EmptyState from '@/components/Espresso/EmptyState.vue'
import LoaderMark from '@/components/Espresso/LoaderMark.vue'
import { usersStore } from '@/stores/users'
import { timeAgo } from '@/utils'
import { rigaDellaNota as riga } from '@/utils/sulTelefono'
import { LoadingIndicator, TextInput } from 'frappe-ui'

const emit = defineEmits(['apri'])

const { puo, getUser } = usersStore()

const { testo, righe, contenitore, carica, cerca, forseAltre, tira } =
  useElencoDelTelefono('crm.api.sul_telefono.get_notes', 'note')

// who wrote it, about whom, when: «Anna Bianchi · Laura Rossi · 2 ore fa»
function rigaDellaNota(nota) {
  return riga(nota, {
    autore: getUser(nota.owner)?.full_name || '',
    quando: __(timeAgo(nota.modified)),
  })
}

defineExpose({ ricarica: cerca })
</script>
