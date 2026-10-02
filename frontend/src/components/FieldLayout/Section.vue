<template>
  <div
    v-if="!section.hidden && applies"
    class="section"
    :class="[
      section.hideBorder
        ? 'pt-4'
        : 'border-t border-outline-elevation-2 mt-5 pt-5',
    ]"
  >
    <CollapsibleSection
      class="flex sm:flex-row flex-col gap-4 text-lg-medium"
      :class="{ 'px-3 sm:px-5': hasTabs }"
      :labelClass="['text-lg font-medium', { 'px-3 sm:px-5': hasTabs }]"
      :label="section.label"
      :hideLabel="section.hideLabel || !section.label"
      :opened="section.opened"
      :collapsible="section.collapsible"
      collapseIconPosition="right"
    >
      <template v-for="column in section.columns" :key="column.name">
        <Column
          :class="{ 'mt-6': section.label && !section.hideLabel }"
          :column="column"
          :data-name="column.name"
        />
      </template>
    </CollapsibleSection>
  </div>
</template>
<script setup>
import CollapsibleSection from '@/components/CollapsibleSection.vue'
import Column from '@/components/FieldLayout/Column.vue'
import { evaluateDependsOnValue } from '@/utils/expressions'
import { computed, inject } from 'vue'

const props = defineProps({
  section: { type: Object, required: true },
})

const hasTabs = inject('hasTabs')
const data = inject('data', null)

// a section the DocType shows only when the document needs it (the Sistema TS
// fields of a service that is not healthcare)
const applies = computed(() =>
  props.section.dependsOn
    ? evaluateDependsOnValue(props.section.dependsOn, data?.value)
    : true,
)
</script>
