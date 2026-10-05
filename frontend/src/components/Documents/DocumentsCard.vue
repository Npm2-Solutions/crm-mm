<!--
  A person's documents (crm.documenti): a signed form, a contract, what they
  brought, what arrived in a conversation; with the clinic the tests, the
  reports, the images, and the report of every signed visit.

  The files are private: opening one is logged by Frappe, and listing one with
  health data is logged like reading the record. A document added by mistake
  goes the same day, with a reason; later the manager takes one away - one with
  health data, the medical director.
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

    <p
      v-if="!archive.data.documents.length && !archive.data.hidden"
      class="text-p-sm text-ink-gray-5"
    >
      {{
        __(
          'Nothing yet. What the person brings or sends goes here: a contract, a certificate, a consent signed on paper.',
        )
      }}
    </p>

    <ul v-if="archive.data.documents.length" class="flex flex-col">
      <li
        v-for="doc in shown"
        :key="doc.name"
        class="relative flex items-start gap-3 border-b border-outline-gray-1 py-2 last:border-0 max-md:flex-wrap"
      >
        <span
          class="mt-0.5 size-4 shrink-0 text-ink-gray-5"
          :class="iconFor(doc.document_type)"
          aria-hidden="true"
        />
        <div class="flex min-w-0 flex-1 flex-col">
          <!-- the whole row opens it: its name alone was a line 16px tall -->
          <a
            v-if="doc.file"
            :href="doc.file"
            target="_blank"
            rel="noopener"
            class="min-w-0 truncate text-base text-ink-gray-8 after:absolute after:inset-0 after:content-[''] hover:underline"
          >
            {{ doc.title }}
          </a>
          <span v-else class="min-w-0 truncate text-base text-ink-gray-8">
            {{ doc.title }}
          </span>
          <span class="text-p-sm text-ink-gray-5">
            {{ describe(doc) }}
          </span>
          <!-- how it reached the person: the latest delivery -->
          <span v-if="doc.deliveries?.length" class="text-p-xs text-ink-gray-5">
            {{ delivered(doc.deliveries[0]) }}
          </span>
        </div>
        <!-- read like the clinical record: the dossier's rules, the access log;
             what kind of data it is, the design system's Tag. On a phone the
             marks go on a line of their own under the words, which beside them
             were squeezed to a column of five lines -->
        <div
          v-if="
            doc.clinical ||
            doc.obscured ||
            ['Only me', 'My discipline'].includes(doc.visibility)
          "
          class="flex shrink-0 flex-wrap items-center gap-1 max-md:order-last max-md:w-full max-md:pl-7"
        >
          <CategoryTag
            v-if="doc.clinical"
            color="rose"
            :label="__('Health data')"
          />
          <Badge
            v-if="doc.visibility === 'Only me'"
            size="sm"
            theme="gray"
            :label="__('Only me')"
          />
          <Badge
            v-if="doc.visibility === 'My discipline'"
            size="sm"
            theme="gray"
            :label="__('My discipline')"
          />
          <Badge
            v-if="doc.obscured"
            size="sm"
            theme="orange"
            :label="__('Obscured')"
          />
        </div>
        <Dropdown
          v-if="actionsFor(doc).length"
          :options="actionsFor(doc)"
          placement="right"
        >
          <Button
            size="sm"
            variant="ghost"
            class="touch-target relative z-[1] shrink-0"
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
    <!-- health data one may know of but does not read: their padlock, as in
         the history, never «Nothing yet» over a list that is not empty -->
    <p
      v-if="archive.data.hidden"
      class="flex items-start gap-2 text-p-sm text-ink-gray-6"
    >
      <span class="lucide-lock mt-0.5 size-4 shrink-0" aria-hidden="true" />
      <span>
        {{
          archive.data.hidden === 1
            ? __('One document with health data you cannot read')
            : __('{0} documents with health data you cannot read', [
                archive.data.hidden,
              ])
        }}
      </span>
    </p>
  </section>

  <DeliverDialog
    v-model="delivering.show"
    :document="delivering.doc"
    @given="archive.reload()"
  />

  <ObscureDialog
    v-model="obscuring.show"
    doctype="CRM Document"
    :name="obscuring.doc?.name"
    :title="obscuring.doc?.title"
    :obscured="Boolean(obscuring.doc?.obscured)"
    @done="archive.reload()"
  />

  <DocumentDialog
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
              '{0} is taken away. The audit log keeps who took it away, why, and the fingerprint of the file.',
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
import CategoryTag from '@/components/Espresso/CategoryTag.vue'
import DeliverDialog from '@/components/Documents/DeliverDialog.vue'
import DocumentDialog from '@/components/Documents/DocumentDialog.vue'
import ObscureDialog from '@/components/Clinic/ObscureDialog.vue'
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
  'Signed form': 'lucide-file-signature',
  Contract: 'lucide-file-pen-line',
  Certificate: 'lucide-award',
  'Identity document': 'lucide-id-card',
  Photo: 'lucide-image',
  // the clinic's
  Report: 'lucide-file-check',
  'External report': 'lucide-file-text',
  'Test result': 'lucide-flask-conical',
  Imaging: 'lucide-scan',
  Prescription: 'lucide-pill',
}

const archive = createResource({
  url: 'crm.documenti.api.get_documents',
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
const obscuring = reactive({ show: false, doc: null })
const delivering = reactive({ show: false, doc: null })
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

// a day or whom it is for never broken across two lines: on a phone «per Laura»
// ended one line and «Bassi» began the next
const unito = (testo) => testo.replace(/ /g, ' ')

function describe(doc) {
  return [
    __(doc.document_type),
    doc.document_date
      ? unito(formatDate(doc.document_date, 'D MMM YYYY'))
      : null,
    doc.source,
    doc.practitioner_name
      ? unito(__('for {0}', [doc.practitioner_name]))
      : null,
  ]
    .filter(Boolean)
    .join(' · ')
}

function delivered(delivery) {
  const when = formatDate(delivery.given_on, 'D MMM YYYY')
  if (delivery.channel === 'By hand') {
    return __('Given by hand to {0}, {1}', [delivery.delivered_to, when])
  }
  if (delivery.status === 'Withdrawn') return __('Online, withdrawn')
  if (delivery.status === 'Expired') return __('Online, expired')
  const until = formatDate(delivery.expires_on, 'D MMM YYYY')
  return delivery.downloads
    ? __('Online until {0}, downloaded', [until])
    : __('Online until {0}, not downloaded yet', [until])
}

function actionsFor(doc) {
  return [
    archive.data?.can_deliver &&
      doc.file && {
        label: __('Give it to the person'),
        icon: 'send',
        onClick: () => Object.assign(delivering, { show: true, doc }),
      },
    doc.can_edit && {
      label: __('Edit'),
      icon: 'edit-2',
      onClick: () => openDialog(doc),
    },
    // the medical director, at the patient's request; a report goes with its visit
    archive.data?.can_obscure &&
      !doc.record && {
        label: doc.obscured ? __('Reveal') : __('Obscure'),
        icon: doc.obscured ? 'eye' : 'eye-off',
        onClick: () => Object.assign(obscuring, { show: true, doc }),
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
    await call('crm.documenti.api.remove_document', {
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
