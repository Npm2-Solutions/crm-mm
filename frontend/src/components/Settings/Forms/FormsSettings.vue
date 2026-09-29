<!--
  One builder, two kinds of form (docs/gestionale-medico, design, "Il motore dei
  modelli"): the web form that captures a lead from the site, as before, and the
  form a person fills and signs — a privacy notice, a consent, a questionnaire —
  kept in versions. Each shows to whoever may build it.
-->
<template>
  <div class="flex h-full flex-col">
    <div
      v-if="kinds.length > 1 && screen === 'list'"
      class="px-8 pt-6 max-md:px-3 max-md:pt-4"
    >
      <TabButtons v-model="kind" :buttons="kinds" />
    </div>
    <template v-if="kind === 'web'">
      <FormsList v-if="screen === 'list'" ref="listRef" @open="open" />
      <FormBuilderPanel
        v-else
        :key="activeName"
        :name="activeName"
        @back="backToList"
        @saved="() => listRef?.reload?.()"
      />
    </template>
    <template v-else>
      <TemplatesList v-if="screen === 'list'" ref="listRef" @open="open" />
      <TemplateBuilder
        v-else
        :key="activeName"
        :name="activeName"
        @back="backToList"
      />
    </template>
  </div>
</template>

<script setup>
import FormsList from './FormsList.vue'
import FormBuilderPanel from './FormBuilderPanel.vue'
import TemplatesList from './TemplatesList.vue'
import TemplateBuilder from './TemplateBuilder.vue'
import { usersStore } from '@/stores/users'
import { TabButtons } from 'frappe-ui'
import { computed, nextTick, ref, watch } from 'vue'

const { puo } = usersStore()

const kinds = computed(() =>
  [
    puo('moduli_lead.gestisci') && { label: __('Web forms'), value: 'web' },
    puo('moduli.configura') && {
      label: __('Forms to sign'),
      value: 'templates',
    },
  ].filter(Boolean),
)

const kind = ref(kinds.value[0]?.value || 'web')
const screen = ref('list')
const activeName = ref(null)
const listRef = ref(null)

watch(kind, () => {
  screen.value = 'list'
  activeName.value = null
})

function open(name) {
  activeName.value = name
  screen.value = 'builder'
}

async function backToList() {
  screen.value = 'list'
  await nextTick()
  listRef.value?.reload?.()
}
</script>
