<template>
  <div class="flex flex-col gap-8">
    <section
      v-for="section in shownSections"
      :key="section.id"
      class="flex flex-col gap-5"
    >
      <div
        v-if="section.title || section.description"
        class="flex flex-col gap-1"
      >
        <h3 class="text-lg font-semibold text-ink-gray-9">
          {{ section.title }}
        </h3>
        <p
          v-if="section.description"
          class="whitespace-pre-line text-p-base text-ink-gray-6"
        >
          {{ section.description }}
        </p>
      </div>
      <template v-for="field in fieldsOfSection(section)" :key="field.id">
        <FormFieldInput
          v-if="state.visible[field.id]"
          :field="field"
          :model-value="values[field.id]"
          :worked-out="state.values[field.id]"
          :band="state.bands[field.id]"
          :required="required.has(field.id)"
          :missing="showMissing && missing.has(field.id)"
          :stop="stops.get(field.id)"
          :readonly="readonly"
          :consent-texts="consentTexts"
          @update:model-value="(value) => set(field.id, value)"
        />
      </template>
    </section>
  </div>
</template>

<script setup>
import FormFieldInput from '@/components/Moduli/FormFieldInput.vue'
import { evaluate, fieldsOfSection, sectionsOf } from '@/utils/moduli'
import { computed } from 'vue'

const props = defineProps({
  /** A version's schema, or a draft's in the builder's preview. */
  schema: { type: Object, required: true },
  readonly: { type: Boolean, default: false },
  /** Mark what is required and missing: after a first try to finish. */
  showMissing: { type: Boolean, default: false },
  /** A draft's consents have no frozen words yet: the register's, by key. */
  consentTexts: { type: Object, default: () => ({}) },
})

const values = defineModel({ type: Object, default: () => ({}) })

// the same evaluation the server makes when the form is sent
const state = computed(() => evaluate(props.schema, values.value))
const shownSections = computed(() =>
  sectionsOf(props.schema).filter(
    (section) => state.value.sections[section.id],
  ),
)
const required = computed(() => new Set(state.value.required))
const missing = computed(() => new Set(state.value.missing))
const stops = computed(
  () => new Map(state.value.stops.map((stop) => [stop.field, stop.message])),
)

function set(key, value) {
  values.value = { ...values.value, [key]: value }
}

defineExpose({ state })
</script>
