<!--
  Copyright (c) 2026, NPM2 Solutions Srl and contributors
  For license information, please see license.txt

  Which days a meal, a session or a whole day goes into: the week's days, the one
  it comes from left out, ticked together. What is copied is the editor's to do
  (utils/piani.js, copiaMomento and copiaGiorno).
-->
<template>
  <Dialog v-model="show" :options="{ title, size: 'sm' }">
    <template #body-content>
      <div class="flex flex-col gap-1">
        <p v-if="note" class="pb-1 text-p-sm text-ink-gray-6">{{ note }}</p>
        <label
          v-for="giorno in giorni"
          :key="giorno"
          class="flex min-h-10 items-center gap-3 rounded px-1 hover:bg-surface-gray-2"
        >
          <Checkbox
            class="touch-target shrink-0"
            :model-value="scelti.includes(giorno)"
            @update:model-value="(si) => scegli(giorno, si)"
          />
          <span class="text-base text-ink-gray-8">{{ __(giorno) }}</span>
        </label>
        <Button
          class="mt-1 w-fit"
          variant="ghost"
          :label="tutti ? __('None') : __('All the days')"
          @click="scelti = tutti ? [] : [...giorni]"
        />
      </div>
    </template>
    <template #actions>
      <div class="dialog-footer flex justify-end gap-2">
        <Button :label="__('Cancel')" @click="show = false" />
        <Button
          variant="solid"
          :disabled="!scelti.length"
          :label="__('Copy')"
          @click="copia"
        />
      </div>
    </template>
  </Dialog>
</template>

<script setup>
import { GIORNI } from '@/utils/piani'
import { Button, Checkbox, Dialog } from 'frappe-ui'
import { computed, ref, watch } from 'vue'

const props = defineProps({
  title: { type: String, default: '' },
  // the day it comes from, not offered
  from: { type: String, default: '' },
  // what the copy does to the days chosen, when it is worth saying
  note: { type: String, default: '' },
})
const emit = defineEmits(['copy'])
const show = defineModel({ type: Boolean })

const giorni = computed(() => GIORNI.filter((g) => g !== props.from))
const scelti = ref([])
const tutti = computed(() => scelti.value.length === giorni.value.length)

watch(show, (aperto) => aperto && (scelti.value = []))

function scegli(giorno, si) {
  scelti.value = si
    ? [...scelti.value, giorno]
    : scelti.value.filter((g) => g !== giorno)
}

function copia() {
  emit(
    'copy',
    GIORNI.filter((g) => scelti.value.includes(g)),
  )
  show.value = false
}
</script>
