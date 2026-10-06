<!--
  Copyright (c) 2026, NPM2 Solutions Srl and contributors
  For license information, please see license.txt

  Whose agenda: the professionals (or the rooms) a day and a month show -
  everybody, or some ticked - and the one a week is of (`singolo`). On a
  phone the list is a sheet from the bottom (`data-foglio`, telefono.css).
-->
<template>
  <Popover placement="bottom-start">
    <template #target="{ togglePopover }">
      <Button :aria-label="etichetta" @click="togglePopover">
        <template #prefix>
          <UserAvatar
            v-if="unoSolo?.utente"
            :user="unoSolo.utente"
            size="xs"
            class="shrink-0"
          />
          <span
            v-else
            :class="[icona, 'size-4 text-ink-gray-6']"
            aria-hidden="true"
          />
        </template>
        <span class="max-w-[12rem] truncate max-md:hidden">{{
          etichetta
        }}</span>
        <!-- on a phone «All» beside the icon that says of whom -->
        <span class="max-w-[7rem] truncate md:hidden">{{ breve }}</span>
        <template #suffix>
          <span
            class="lucide-chevron-down size-3.5 text-ink-gray-5"
            aria-hidden="true"
          />
        </template>
      </Button>
    </template>
    <template #body-main="{ close }">
      <div
        data-foglio
        class="flex max-h-80 w-72 flex-col gap-0.5 overflow-y-auto p-1.5"
      >
        <span class="px-1.5 pb-1 text-xs-medium text-ink-gray-5">
          {{ titolo }}
        </span>
        <label
          v-if="!singolo"
          class="flex cursor-pointer items-center gap-2 rounded px-1.5 py-1 hover:bg-surface-gray-2"
        >
          <Checkbox
            :modelValue="!scelti.length"
            @update:modelValue="emit('update:modelValue', [])"
          />
          <span class="truncate text-p-sm text-ink-gray-8">{{ tutti }}</span>
        </label>
        <label
          v-for="opzione in opzioni"
          :key="opzione.value"
          class="flex cursor-pointer items-center gap-2 rounded px-1.5 py-1 hover:bg-surface-gray-2"
          :class="
            singolo && opzione.value === modelValue ? 'bg-surface-gray-2' : ''
          "
        >
          <Checkbox
            v-if="!singolo"
            :modelValue="scelti.includes(opzione.value)"
            @update:modelValue="cambia(opzione.value)"
          />
          <input
            v-else
            type="radio"
            class="sr-only"
            :name="`chi-${uid}`"
            :checked="opzione.value === modelValue"
            @change="scegli(opzione.value, close)"
          />
          <UserAvatar
            v-if="opzione.utente"
            :user="opzione.utente"
            size="sm"
            class="shrink-0"
          />
          <span
            v-else
            class="size-2.5 shrink-0 rounded-full"
            :style="{ backgroundColor: opzione.colore || 'var(--ink-gray-4)' }"
            aria-hidden="true"
          />
          <span class="flex min-w-0 flex-1 flex-col">
            <span class="truncate text-p-sm text-ink-gray-8">
              {{ opzione.label }}
            </span>
            <span
              v-if="opzione.nota"
              class="truncate text-p-xs text-ink-gray-5"
            >
              {{ opzione.nota }}
            </span>
          </span>
          <span
            v-if="singolo && opzione.value === modelValue"
            class="lucide-check size-4 shrink-0 text-ink-gray-7"
            aria-hidden="true"
          />
        </label>
        <p v-if="!opzioni.length" class="px-1.5 py-2 text-p-sm text-ink-gray-5">
          {{ vuoto }}
        </p>
      </div>
    </template>
  </Popover>
</template>

<script setup>
import UserAvatar from '@/components/UserAvatar.vue'
import { Button, Checkbox, Popover } from 'frappe-ui'
import { computed, useId } from 'vue'

const props = defineProps({
  /** the ones ticked (a list), or the one a week is of (`singolo`) */
  modelValue: { type: [Array, String], default: () => [] },
  /** `[{ value, label, utente?, colore?, nota? }]` */
  opzioni: { type: Array, default: () => [] },
  singolo: { type: Boolean, default: false },
  /** «Professionisti», above the list */
  titolo: { type: String, default: '' },
  /** «Tutti i professionisti»: the button with nobody ticked */
  tutti: { type: String, default: '' },
  /** the button with more than one ticked: `(n) => __('{0} professionals', [n])` */
  quanti: { type: Function, default: (n) => String(n) },
  vuoto: { type: String, default: '' },
  icona: { type: String, default: 'lucide-users' },
})
const emit = defineEmits(['update:modelValue'])
const uid = useId()

const scelti = computed(() =>
  Array.isArray(props.modelValue) ? props.modelValue : [],
)

const unoSolo = computed(() => {
  const valore = props.singolo
    ? props.modelValue
    : scelti.value.length === 1
      ? scelti.value[0]
      : ''
  return props.opzioni.find((opzione) => opzione.value === valore) || null
})

const etichetta = computed(() => {
  if (unoSolo.value) return unoSolo.value.label
  if (props.singolo || !scelti.value.length) return props.tutti
  return props.quanti(scelti.value.length)
})
const breve = computed(() =>
  !unoSolo.value && !props.singolo && !scelti.value.length
    ? __('All', null, 'Agenda whose')
    : etichetta.value,
)

function cambia(valore) {
  emit(
    'update:modelValue',
    scelti.value.includes(valore)
      ? scelti.value.filter((v) => v !== valore)
      : [...scelti.value, valore],
  )
}

function scegli(valore, close) {
  emit('update:modelValue', valore)
  close?.()
}
</script>
