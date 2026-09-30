<!--
  The clinical archive of one person: reports, tests, images, prescriptions.

  What the patient brings, what arrived in a conversation, and the report of
  every signed visit. The files are private: opening one is logged by Frappe,
  and listing them here is logged like reading the record. A document added by
  mistake goes the same day, with a reason; later only the medical director
  takes one away.
-->
<template>
  <section
    v-if="archive.data"
    class="flex flex-col gap-3 rounded-lg border border-outline-gray-2 p-4"
  >
    <div class="flex flex-wrap items-center justify-between gap-2">
      <h3 class="text-base-semibold text-ink-gray-8">
        {{ __('Documents') }}
        <span
          v-if="archive.data.documents.length"
          class="text-ink-gray-5 tabular-nums"
        >
          {{ archive.data.documents.length }}
        </span>
      </h3>
      <Button
        v-if="archive.data.can_add"
        class="shrink-0"
        icon-left="plus"
        :label="__('Add document')"
        @click="openDialog(null)"
      />
    </div>

    <p v-if="!archive.data.documents.length" class="text-p-sm text-ink-gray-5">
      {{
        __(
          'Nothing yet. The tests, reports and images the patient brings go here, and the report of every signed visit.',
        )
      }}
    </p>

    <ul v-else class="flex flex-col">
      <li
        v-for="doc in shown"
        :key="doc.name"
        class="flex items-start gap-3 border-b border-outline-gray-1 py-2 last:border-0"
      >
        <span
          class="mt-0.5 size-4 shrink-0 text-ink-gray-5"
          :class="iconFor(doc.document_type)"
          aria-hidden="true"
        />
        <div class="flex min-w-0 flex-1 flex-col">
          <a
            v-if="doc.file"
            :href="doc.file"
            target="_blank"
            rel="noopener"
            class="min-w-0 truncate text-base text-ink-gray-8 hover:underline"
          >
            {{ doc.title }}
          </a>
          <span v-else class="min-w-0 truncate text-base text-ink-gray-8">
            {{ doc.title }}
          </span>
          <span class="text-p-sm text-ink-gray-5">
            {{ describe(doc) }}
          </span>
        </div>
        <Badge
          v-if="doc.visibility === 'Only me'"
          size="sm"
          theme="gray"
          class="shrink-0"
          :label="__('Only me')"
        />
        <Dropdown
          v-if="doc.can_edit || doc.can_remove"
          :options="actionsFor(doc)"
          placement="right"
        >
          <Button
            size="sm"
            variant="ghost"
            class="touch-target shrink-0"
            icon="more-horizontal"
            :aria-label="__('Actions')"
          />
        </Dropdown>
      </li>
    </ul>
    <Button
      v-if="archive.data.documents.length > LIMIT"
      variant="ghost"
      class="w-fit"
      :label="
        showAll
          ? __('Show fewer')
          : __('Show all {0}', [archive.data.documents.length])
      "
      @click="showAll = !showAll"
    />
  </section>

  <ClinicDocumentDialog
    v-model="dialog.show"
    :lead="lead"
    :document="dialog.document"
    @saved="archive.reload()"
  />

  <Dialog
    v-model="removing.show"
    :options="{ title: __('Take the document away'), size: 'md' }"
  >
    <template #body-content>
      <div class="flex flex-col gap-3">
        <p class="text-p-base text-ink-gray-7">
          {{
            __(
              '{0} leaves the archive. The audit log keeps who took it away, why, and the fingerprint of the file.',
              [removing.doc?.title],
            )
          }}
        </p>
        <FormControl
          v-model="removing.reason"
          type="textarea"
          :rows="2"
          :label="__('Why')"
          :placeholder="__('The wrong person, the wrong file…')"
        />
        <ErrorMessage :message="removing.error" />
      </div>
    </template>
    <template #actions>
      <div class="dialog-footer flex justify-end gap-2">
        <Button :label="__('Cancel')" @click="removing.show = false" />
        <Button
          variant="solid"
          theme="red"
          :label="__('Take it away')"
          :disabled="!removing.reason.trim()"
          :loading="removing.busy"
          @click="remove"
        />
      </div>
    </template>
  </Dialog>
</template>

<script setup>
import ClinicDocumentDialog from '@/components/Clinic/ClinicDocumentDialog.vue'
import { formatDate } from '@/utils'
import {
  Badge,
  Button,
  Dialog,
  Dropdown,
  ErrorMessage,
  FormControl,
  call,
  createResource,
} from 'frappe-ui'
import { computed, reactive, ref, watch } from 'vue'

const props = defineProps({ lead: { type: String, required: true } })

const LIMIT = 5
const ICONS = {
  Report: 'lucide-file-check',
  'External report': 'lucide-file-text',
  'Test result': 'lucide-flask-conical',
  Imaging: 'lucide-scan',
  Prescription: 'lucide-pill',
  'Signed form': 'lucide-file-signature',
}

const archive = createResource({
  url: 'crm.clinica.archivio.get_documents',
  makeParams: () => ({ lead: props.lead }),
})
watch(
  () => props.lead,
  (lead) => lead && archive.reload(),
  { immediate: true },
)

const showAll = ref(false)
const shown = computed(() => {
  const documents = archive.data?.documents || []
  return showAll.value ? documents : documents.slice(0, LIMIT)
})

const dialog = reactive({ show: false, document: null })
const removing = reactive({
  show: false,
  doc: null,
  reason: '',
  busy: false,
  error: '',
})

function iconFor(kind) {
  return ICONS[kind] || 'lucide-file'
}

function describe(doc) {
  return [
    __(doc.document_type),
    doc.document_date ? formatDate(doc.document_date, 'D MMM YYYY') : null,
    doc.source,
    doc.practitioner_name ? __('for {0}', [doc.practitioner_name]) : null,
  ]
    .filter(Boolean)
    .join(' · ')
}

function actionsFor(doc) {
  return [
    doc.can_edit && {
      label: __('Edit'),
      icon: 'edit-2',
      onClick: () => openDialog(doc),
    },
    doc.can_remove && {
      label: __('Take away'),
      icon: 'trash-2',
      theme: 'red',
      onClick: () =>
        Object.assign(removing, {
          show: true,
          doc,
          reason: '',
          error: '',
        }),
    },
  ].filter(Boolean)
}

function openDialog(doc) {
  dialog.document = doc
  dialog.show = true
}

async function remove() {
  removing.busy = true
  removing.error = ''
  try {
    await call('crm.clinica.archivio.remove_document', {
      name: removing.doc.name,
      reason: removing.reason,
    })
    removing.show = false
    archive.reload()
  } catch (e) {
    removing.error = e.messages?.join(' ') || e.message
  } finally {
    removing.busy = false
  }
}

defineExpose({ reload: () => archive.reload() })
</script>
