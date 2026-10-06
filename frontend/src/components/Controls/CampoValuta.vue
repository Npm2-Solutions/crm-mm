<!--
  Copyright (c) 2026, NPM2 Solutions Srl and contributors
  For license information, please see license.txt

  A currency chosen by its name in the reader's language («Euro», «Franco
  svizzero»), the code stored: the currencies the site has on, asked once for
  every field that draws one. It was a free text where one typed «EUR», or a
  list of codes. `vuota` names the choice of none, where none means another's
  (a price rule counts in its list's).
-->
<template>
  <!-- a select draws no box of its own: a width given to the field goes on
       the box around it, its name on the select -->
  <div :class="$attrs.class" :style="$attrs.style">
    <FormControl
      v-bind="attributi"
      type="select"
      :label="label"
      :placeholder="placeholder"
      :options="scelte"
      :modelValue="modelValue || ''"
      @update:modelValue="(valore) => emit('update:modelValue', valore)"
    />
  </div>
</template>

<script setup>
import { valuteDaScegliere } from '@/utils/valute'
import { appLocale } from '@/utils/locale'
import { FormControl, createResource, getCachedResource } from 'frappe-ui'
import { computed, useAttrs } from 'vue'

defineOptions({ inheritAttrs: false })

const props = defineProps({
  modelValue: { type: String, default: '' },
  label: { type: String, default: '' },
  placeholder: { type: String, default: '' },
  vuota: { type: String, default: '' },
})
const emit = defineEmits(['update:modelValue'])

const attrs = useAttrs()
const attributi = computed(() =>
  Object.fromEntries(
    Object.entries(attrs).filter(
      ([nome]) => !['class', 'style'].includes(nome),
    ),
  ),
)

const CHIAVE = ['valuteAttive']
const valute =
  getCachedResource(CHIAVE) ||
  createResource({
    url: 'frappe.client.get_list',
    cache: CHIAVE,
    params: {
      doctype: 'Currency',
      filters: { enabled: 1 },
      fields: ['name'],
      limit_page_length: 0,
    },
    auto: true,
  })

const scelte = computed(() => [
  ...(props.vuota ? [{ label: props.vuota, value: '' }] : []),
  ...valuteDaScegliere({
    codici: (valute.data || []).map((valuta) => valuta.name),
    scelta: props.modelValue,
    lingua: appLocale() || 'it',
  }),
])
</script>
