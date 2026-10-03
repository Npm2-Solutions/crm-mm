<!--
  Modifications copyright (c) 2026, NPM2 Solutions Srl
-->
<template>
  <div class="space-y-1.5 p-[2px] !-m-[2px]">
    <label v-if="attrs.label" class="block" :class="labelClasses">
      {{ __(attrs.label) }}
    </label>
    <Autocomplete
      ref="autocomplete"
      v-model="value"
      :options="opzioni"
      :size="attrs.size || 'sm'"
      :variant="attrs.variant"
      :placeholder="attrs.placeholder"
      :disabled="attrs.disabled"
      :placement="attrs.placement"
      :filterable="false"
    >
      <template #target="{ open, togglePopover }">
        <slot name="target" v-bind="{ open, togglePopover }" />
      </template>

      <template #prefix>
        <slot name="prefix" />
      </template>

      <template #item-prefix="{ active, selected, option }">
        <slot name="item-prefix" v-bind="{ active, selected, option }" />
      </template>

      <template #item-label="{ active, selected, option }">
        <slot name="item-label" v-bind="{ active, selected, option }">
          <div v-if="option.description" class="flex flex-col gap-1">
            <div class="flex-1 font-semibold truncate text-ink-gray-7">
              {{ option.label }}
            </div>
            <div class="flex-1 text-sm truncate text-ink-gray-5">
              {{ option.description }}
            </div>
          </div>
          <div v-else class="flex-1 truncate text-ink-gray-7">
            {{ option.label }}
          </div>
        </slot>
      </template>

      <template #footer="{ value: v, close }">
        <div v-if="attrs.onCreate">
          <Button
            variant="ghost"
            class="w-full !justify-start"
            :label="__('Create New')"
            iconLeft="plus"
            @click="() => attrs.onCreate(v, close)"
          />
        </div>
        <div>
          <Button
            variant="ghost"
            class="w-full !justify-start"
            :label="__('Clear')"
            iconLeft="x"
            @click="() => clearValue(close)"
          />
        </div>
      </template>
    </Autocomplete>
  </div>
</template>

<script setup>
import Autocomplete from '@/components/frappe-ui/Autocomplete.vue'
import { isTranslatable } from '@/utils'
import { watchDebounced } from '@vueuse/core'
import { call, createResource } from 'frappe-ui'
import { useAttrs, computed, ref, watch } from 'vue'

const props = defineProps({
  doctype: { type: String, required: true },
  filters: { type: [Array, Object, String], default: () => [] },
  modelValue: { type: String, default: '' },
  hideMe: { type: Boolean, default: false },
})

const emit = defineEmits(['update:modelValue', 'change'])

const attrs = useAttrs()

const valuePropPassed = computed(() => 'value' in attrs)

const value = computed({
  get: () => {
    let v = valuePropPassed.value ? attrs.value : props.modelValue

    if (isTranslatable(props.doctype)) return __(v)
    return v
  },
  set: (val) => {
    return (
      val?.value &&
      emit(valuePropPassed.value ? 'change' : 'update:modelValue', val?.value)
    )
  },
})

const autocomplete = ref(null)
const text = ref('')

watchDebounced(
  () => autocomplete.value?.query,
  (val) => {
    val = val || ''
    if (text.value === val) return
    text.value = val
    reload(val)
  },
  { debounce: 300, immediate: true },
)

watchDebounced(
  () => props.doctype,
  () => reload(''),
  { debounce: 300, immediate: true },
)

watchDebounced(
  () => props.filters,
  () => {
    reload('', true)
  },
  { debounce: 300, immediate: true },
)

const options = createResource({
  url: 'frappe.desk.search.search_link',
  cache: [props.doctype, text.value, props.hideMe, props.filters],
  method: 'POST',
  params: {
    txt: text.value,
    doctype: props.doctype,
    filters: props.filters,
  },
  transform: (data) => {
    let allData = data.map((option) => {
      return {
        label: option.label || option.value,
        value: option.value,
        description: senzaIlCodice(stripHtml(option.description), option),
      }
    })
    if (!props.hideMe && props.doctype == 'User') {
      allData.unshift({
        label: '@me',
        value: '@me',
      })
    }
    return allData
  },
})

// A DocType that shows a title in its links shows it here too: a qualification
// reads "Fisioterapista", not `fisioterapista`, also when the search did not
// load it - one a filter leaves out stays, named, among the choices.
const attuale = computed(() =>
  valuePropPassed.value ? attrs.value : props.modelValue,
)
const titolo = ref('')
watch(
  () => [props.doctype, attuale.value, options.data],
  async ([doctype, nome, caricate]) => {
    titolo.value = ''
    // asked only when the search has loaded and did not bring the value
    if (!nome || !caricate || caricate.some((o) => o.value === nome)) return
    if (!(window.link_title_doctypes || []).includes(doctype)) return
    const trovato = await titoloDi(doctype, nome)
    if (nome === attuale.value) titolo.value = trovato
  },
  { immediate: true },
)

const opzioni = computed(() => {
  const caricate = options.data || []
  if (!titolo.value || caricate.some((o) => o.value === attuale.value)) {
    return caricate
  }
  return [...caricate, { label: titolo.value, value: attuale.value }]
})

// A record shown by its title gets its name under it from the search
// («Fisioterapista» over `fisioterapista`): a code nobody reads, left out; and
// so does what only repeats the line above it («Consulenza» under
// «Consulenza», «Dott. Verdi, osteopata» under «Dott. Verdi» reads «osteopata»).
function senzaIlCodice(descrizione, option) {
  let resto = descrizione
  for (const gia of new Set([option.value, option.label])) {
    if (!gia) continue
    if (resto === gia) return ''
    if (resto.startsWith(`${gia}, `)) resto = resto.slice(gia.length + 2)
  }
  return resto
}

function stripHtml(html) {
  if (!html) return ''
  return html
    .replace(/<[^>]*>/g, ' ')
    .replace(/&nbsp;/g, ' ')
    .replace(/\s+/g, ' ')
    .trim()
}

function reload(val, force = false) {
  if (!props.doctype) return
  if (
    !force &&
    options.data?.length &&
    val === options.params?.txt &&
    props.doctype === options.params?.doctype
  )
    return

  options.update({
    params: {
      txt: val,
      doctype: props.doctype,
      filters: props.filters,
    },
  })
  options.reload()
}

function clearValue(close) {
  emit(valuePropPassed.value ? 'change' : 'update:modelValue', '')
  close()
}

// frappe-ui labels its own inputs at text-base whatever their size: a Link at
// 12px beside a select at 14 made one form row look like two
const labelClasses = computed(() => {
  return [
    {
      sm: 'text-base',
      md: 'text-base',
    }[attrs.size || 'sm'],
    'text-ink-gray-5',
  ]
})

defineExpose({ reload })
</script>

<script>
// one question per record, whichever field asks
const titoli = new Map()

function titoloDi(doctype, nome) {
  const chiave = `${doctype}::${nome}`
  if (!titoli.has(chiave)) {
    titoli.set(
      chiave,
      call('frappe.desk.search.get_link_title', { doctype, docname: nome })
        .then((t) => t || nome)
        .catch(() => nome),
    )
  }
  return titoli.get(chiave)
}
</script>
