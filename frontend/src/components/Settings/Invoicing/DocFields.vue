<!--
  One record of one DocType, rendered from the DocType's own layout.

  The point is that the explanations live in one place. Every rule this module
  enforces is written on the field that carries it — why a numbering format is
  validated against the Sistema TS alphabet, why a virtual stamp duty needs its
  authorisation number, why a facility needs a Codice Proprietario and a
  professional must not have one — and rendering the meta puts those sentences in
  front of whoever is about to get it wrong.
-->
<template>
  <div class="flex h-full flex-col gap-4">
    <div
      v-if="fields.loading || doc.get?.loading"
      class="flex flex-1 items-center justify-center"
    >
      <LoadingIndicator class="size-6" />
    </div>
    <template v-else>
      <div class="flex-1 overflow-y-auto">
        <FieldLayout
          v-if="tabs.length"
          :tabs="tabs"
          :data="local"
          :doctype="doctype"
          :docname="docname || ''"
          :context="context"
        />
      </div>
      <div
        class="flex items-center justify-between gap-3 border-t border-outline-gray-2 pt-3"
      >
        <ErrorMessage :message="error" />
        <div class="ml-auto flex items-center gap-2">
          <slot name="actions" />
          <Button
            variant="solid"
            :loading="saving"
            :label="docname ? __('Update') : __('Create')"
            @click="save"
          />
        </div>
      </div>
    </template>
  </div>
</template>

<script setup>
import FieldLayout from '@/components/FieldLayout/FieldLayout.vue'
import { buildTabs } from '@/utils/settingsTabs'
import {
  createDocumentResource,
  createResource,
  Button,
  ErrorMessage,
  LoadingIndicator,
  call,
  toast,
} from 'frappe-ui'
import { computed, reactive, ref, watch } from 'vue'

const props = defineProps({
  doctype: { type: String, required: true },
  docname: { type: String, default: '' },
  defaults: { type: Object, default: () => ({}) },
})
const emit = defineEmits(['saved'])

const local = reactive({})
const error = ref('')
const saving = ref(false)

// Standalone: the fields write into a local object and nothing is persisted until
// Save. A settings screen that wrote through on every keystroke would leave a
// half-configured company behind the first time somebody changed their mind.
const context = reactive({ fieldPropertyOverrides: {}, fieldHtmlMap: {} })

const fields = createResource({
  url: 'crm.api.doc.get_fields',
  cache: ['fields', props.doctype],
  params: { doctype: props.doctype, allow_all_fieldtypes: true },
  auto: true,
})

const tabs = computed(() => buildTabs(fields.data))

const doc = props.docname
  ? createDocumentResource({
      doctype: props.doctype,
      name: props.docname,
      fields: ['*'],
      auto: true,
      onSuccess: (data) => Object.assign(local, data),
    })
  : { doc: null }

watch(
  () => props.defaults,
  (valori) => Object.assign(local, valori || {}),
  { immediate: true, deep: true },
)

async function save() {
  saving.value = true
  error.value = ''
  try {
    if (props.docname) {
      await call('frappe.client.set_value', {
        doctype: props.doctype,
        name: props.docname,
        fieldname: { ...local },
      })
      toast.success(__('Saved'))
      emit('saved', props.docname)
    } else {
      const creato = await call('frappe.client.insert', {
        doc: { doctype: props.doctype, ...local },
      })
      toast.success(__('Created'))
      emit('saved', creato.name)
    }
  } catch (e) {
    // The controllers refuse for reasons worth reading — a numbering format the
    // Sistema TS would not take, a stamp duty without its authorisation. The
    // message is theirs, not a generic failure.
    error.value = stripHtml(e.messages?.[0] || e.message)
  } finally {
    saving.value = false
  }
}

function stripHtml(text) {
  return String(text || '')
    .replace(/<br\s*\/?>/gi, ' ')
    .replace(/<[^>]*>/g, '')
}
</script>
