<!--
  Copyright (c) 2026, NPM2 Solutions Srl and contributors
  For license information, please see license.txt

  A list of records with an editor over it, for the three catalogues invoicing
  depends on: qualifications, services and providers.

  One component and not three, because the three differ only in what a row says.
  The editor is the DocType's own layout, so the rules explained on the fields are
  explained here too.
-->
<template>
  <div
    class="flex h-full flex-col gap-6 py-8 px-6 text-ink-gray-8 max-md:px-3 max-md:py-5"
  >
    <div
      class="flex items-start justify-between gap-4 px-2 impostazioni-strette:flex-col impostazioni-strette:items-start impostazioni-strette:gap-3"
    >
      <div class="flex flex-col gap-1">
        <h2
          class="flex gap-2 text-2xl-semibold leading-tight md:h-5 md:leading-none"
        >
          {{ title }}
        </h2>
        <p class="text-p-base text-ink-gray-6">{{ subtitle }}</p>
      </div>
      <Button
        variant="solid"
        :label="addLabel"
        iconLeft="plus"
        @click="apri()"
      />
    </div>

    <slot name="banner" />

    <!-- the empty wrapper still took its gap: the list sat 50px down -->
    <div v-if="rows.data?.length > 8" class="flex flex-col gap-2 px-2">
      <FormControl v-model="filtro" type="text" :placeholder="__('Search')" />
    </div>

    <div class="flex-1 overflow-y-auto px-2">
      <div
        v-if="visibili.length"
        class="divide-y divide-outline-elevation-2 rounded-lg border border-outline-gray-2"
      >
        <div
          v-for="row in visibili"
          :key="row.name"
          class="flex cursor-pointer items-center gap-3 px-3 py-2.5 hover:bg-surface-gray-1 max-md:flex-col max-md:items-start max-md:gap-1.5 max-md:active:bg-surface-gray-2"
          @click="apri(row.name)"
        >
          <!-- on a phone the marks go under the words: beside them they left
               the name «Massaggio decontra…» -->
          <div class="min-w-0 flex-1 max-md:w-full">
            <div
              class="truncate text-p-base-medium text-ink-gray-8 max-md:whitespace-normal"
            >
              {{ row[titleField] || row.name }}
            </div>
            <!-- the regime and the nature are the line's point: on a phone
                 it wraps, cut it said «Prestazioni del professionista sanit…» -->
            <div
              class="truncate text-p-sm text-ink-gray-5 max-md:whitespace-normal"
            >
              {{ describe(row) }}
            </div>
          </div>
          <div v-if="badges(row).length" class="flex shrink-0 gap-1.5">
            <Badge
              v-for="badge in badges(row)"
              :key="badge.label"
              :label="badge.label"
              :theme="badge.theme"
              size="sm"
            />
          </div>
        </div>
      </div>
      <div
        v-else-if="!rows.loading"
        class="rounded-lg border border-outline-gray-2 bg-surface-gray-1 px-4 py-6 text-p-base text-ink-gray-5"
      >
        {{ emptyText }}
      </div>
    </div>
  </div>

  <Dialog
    v-model="mostraEditor"
    :options="{
      title: inModifica ? titoloDi(inModifica) : addLabel,
      size: '3xl',
    }"
  >
    <template #body-content>
      <div class="min-h-[24rem]">
        <DocFields
          v-if="mostraEditor"
          :key="inModifica || 'nuovo'"
          :doctype="doctype"
          :docname="inModifica || ''"
          :defaults="defaults"
          @saved="salvato"
        >
          <template #actions>
            <Button
              v-if="inModifica && deletable"
              variant="ghost"
              theme="red"
              :label="__('Delete')"
              @click="elimina"
            />
          </template>
        </DocFields>
      </div>
    </template>
  </Dialog>
</template>

<script setup>
import DocFields from '@/components/Settings/Invoicing/DocFields.vue'
import { recordDaAprire } from '@/composables/settings'
import {
  createListResource,
  Badge,
  Button,
  Dialog,
  FormControl,
  call,
  toast,
} from 'frappe-ui'
import { computed, ref, watch } from 'vue'

const props = defineProps({
  doctype: { type: String, required: true },
  title: { type: String, required: true },
  subtitle: { type: String, default: '' },
  addLabel: { type: String, required: true },
  emptyText: { type: String, default: '' },
  titleField: { type: String, default: 'name' },
  listFields: { type: Array, default: () => ['name'] },
  orderBy: { type: String, default: 'modified desc' },
  describe: { type: Function, default: () => '' },
  badges: { type: Function, default: () => [] },
  defaults: { type: Object, default: () => ({}) },
  deletable: { type: Boolean, default: true },
  // which rows the list shows, before any search: all of them unless the page says
  visibile: { type: Function, default: null },
})

const filtro = ref('')
const mostraEditor = ref(false)
const inModifica = ref(null)

const rows = createListResource({
  doctype: props.doctype,
  fields: props.listFields,
  orderBy: props.orderBy,
  pageLength: 500,
  auto: true,
})

const visibili = computed(() => {
  const testo = filtro.value.trim().toLowerCase()
  const elenco = (rows.data || []).filter((row) =>
    props.visibile ? props.visibile(row) : true,
  )
  if (!testo) return elenco
  return elenco.filter((row) =>
    Object.values(row).some((v) =>
      String(v ?? '')
        .toLowerCase()
        .includes(testo),
    ),
  )
})

function apri(name = null) {
  inModifica.value = name
  mostraEditor.value = true
}

// a record's editor is headed by its name («Psicologo / psicoterapeuta»), not by
// the list's («Qualification register»)
function titoloDi(name) {
  const riga = (rows.data || []).find((r) => r.name === name)
  return riga?.[props.titleField] || name
}

// a record «Set up» named (a qualification to verify): opened, then forgotten
watch(
  recordDaAprire,
  (record) => {
    if (!record?.name || record.doctype !== props.doctype) return
    recordDaAprire.value = null
    apri(record.name)
  },
  { immediate: true },
)

function salvato() {
  mostraEditor.value = false
  rows.reload()
}

async function elimina() {
  try {
    await call('frappe.client.delete', {
      doctype: props.doctype,
      name: inModifica.value,
    })
    toast.success(__('Deleted'))
    salvato()
  } catch (e) {
    // Usually a link: something already invoiced points at this record, and
    // deleting it would orphan a document that has to stay readable.
    toast.error(e.messages?.[0] || e.message)
  }
}

defineExpose({ reload: () => rows.reload() })
</script>
