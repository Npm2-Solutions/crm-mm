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
  <div class="flex flex-col gap-4" :class="scroll ? 'h-full' : ''">
    <div
      v-if="fields.loading || doc.get?.loading"
      class="flex flex-1 items-center justify-center"
    >
      <LoadingIndicator class="size-6" />
    </div>
    <template v-else>
      <div :class="scroll ? 'flex-1 overflow-y-auto' : ''">
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
import { buildTabs, valorePredefinito } from '@/utils/settingsTabs'
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
  // the fields scroll inside the section with the save bar pinned under them;
  // off, they take their own height and the page around them scrolls
  scroll: { type: Boolean, default: true },
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

// A new record starts where its DocType says, filled in front of whoever creates
// it: one place decides, not a copy here that drifts (the SdI channel once read
// "provider" on this screen and "export" everywhere else).
watch(
  () => fields.data,
  (campi) => {
    if (props.docname || !campi) return
    for (const campo of campi) {
      if (local[campo.fieldname] !== undefined) continue
      const valore = valorePredefinito(campo)
      if (valore !== undefined) local[campo.fieldname] = valore
    }
  },
  { immediate: true },
)

async function save() {
  saving.value = true
  error.value = ''
  try {
    // `save` and not `set_value`: it handles a Single, it inserts when there is no
    // name, and it carries `modified` through, so two people editing the same
    // company collide instead of silently overwriting each other.
    const payload = { ...local, doctype: props.doctype }
    if (props.docname) payload.name = props.docname
    const salvato = await call('frappe.client.save', { doc: payload })
    Object.assign(local, salvato)
    toast.success(props.docname ? __('Saved') : __('Created'))
    emit('saved', salvato.name)
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
