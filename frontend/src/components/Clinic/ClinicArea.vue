<!--
  Copyright (c) 2026, NPM2 Solutions Srl and contributors
  For license information, please see license.txt
-->
<template>
  <!--
    The clinical record of one person: visits and notes, newest first.

    A draft is its author's to change; signed, a record is not rewritten but
    added to. Every opening of this tab is written in the access log, which is
    why the record is read only here and not in the history, where a visit is a
    padlock.
  -->
  <div class="flex flex-col gap-4 px-3 pb-6 pt-1 sm:px-10">
    <!-- opened out of the care team: until when, and the reason given -->
    <div
      v-if="record.data?.out_of_care"
      class="flex items-start gap-2 rounded-lg bg-surface-amber-1 px-3 py-2 text-p-sm text-ink-amber-8"
    >
      <span
        class="lucide-lock-open mt-0.5 size-4 shrink-0"
        aria-hidden="true"
      />
      <span class="min-w-0">
        {{
          __('You opened this record out of your care, until {0}: {1}', [
            formatDate(record.data.out_of_care.expires_on, ''),
            record.data.out_of_care.reason,
          ])
        }}
      </span>
    </div>
    <div
      class="flex flex-wrap items-center justify-between gap-2 max-md:flex-col max-md:items-stretch"
    >
      <div class="flex min-w-0 flex-wrap items-center gap-2 text-p-sm">
        <!-- a sentence, not a word: on a phone it wraps, or its one line made
             the header wider than the screen and pushed the buttons off it -->
        <Badge
          v-if="record.data"
          class="max-w-full max-md:h-auto max-md:whitespace-normal max-md:rounded-lg max-md:py-0.5"
          variant="subtle"
          :theme="record.data.dossier ? 'green' : 'gray'"
          :label="
            record.data.dossier
              ? __('Health dossier: consent given')
              : __('No health dossier: each practitioner reads their own')
          "
        />
      </div>
      <div class="flex shrink-0 gap-2 max-md:justify-end">
        <!-- on a phone two of them go under one button: three in a row pushed
             «New visit» off the screen -->
        <Dropdown v-if="sottoAltro" :options="altreAzioni" placement="left">
          <Button
            class="shrink-0"
            icon="more-horizontal"
            :aria-label="__('More')"
          />
        </Dropdown>
        <template v-else>
          <Button
            v-for="azione in altreAzioni"
            :key="azione.label"
            :label="azione.label"
            :iconLeft="azione.icon"
            @click="azione.onClick"
          />
        </template>
        <!-- a free visit, or one on the specialty's clinical sheet -->
        <Dropdown
          v-if="
            record.data?.can_write &&
            !composer.open &&
            record.data.sheets?.length
          "
          :options="newOptions"
          placement="right"
        >
          <Button variant="solid" :label="__('New visit')" iconLeft="plus" />
        </Dropdown>
        <Button
          v-else-if="record.data?.can_write && !composer.open"
          variant="solid"
          :label="__('New visit')"
          iconLeft="plus"
          @click="startNew()"
        />
      </div>
    </div>

    <!-- allergies, medications, parameters: what a practitioner confirmed -->
    <ClinicSummary v-if="record.data?.can_read" ref="summaryRef" :lead="lead" />

    <!-- the teeth, and the care plans proposed as quotes -->
    <DentalCard :lead="lead" />

    <!-- writing: a visit or a note, for the care team or for oneself; opened, it
         comes into view (on a phone it opened below the summary, off screen) -->
    <section
      v-if="composer.open"
      ref="composerRef"
      class="scroll-mt-3 flex flex-col gap-3 rounded-lg border border-outline-gray-3 p-4"
    >
      <div v-if="composer.addendumTo" class="text-p-sm text-ink-gray-6">
        {{ __('Addendum to the record of {0}', [composer.addendumLabel]) }}
      </div>
      <div v-if="composer.sheet" class="text-base-semibold text-ink-gray-8">
        {{ composer.sheet.title }}
      </div>
      <div class="grid grid-cols-2 gap-3 max-md:grid-cols-1">
        <FormControl
          v-model="composer.kind"
          type="select"
          :label="__('Kind')"
          :options="kindOptions"
        />
        <FormControl
          v-model="composer.visibility"
          type="select"
          :label="__('Who reads it')"
          :options="visibilityOptions"
        />
      </div>
      <FormRenderer
        v-if="composer.sheet"
        v-model="composer.answers"
        :schema="composer.sheet.schema"
        :show-missing="composer.tried"
      />
      <FormControl
        v-model="composer.content"
        type="textarea"
        :rows="composer.sheet ? 3 : 7"
        :label="composer.sheet ? __('Notes') : __('What happened')"
        :placeholder="
          __(
            'Reason for the visit, what you found, what you did, what comes next',
          )
        "
      />
      <ErrorMessage :message="composer.error" />
      <div
        class="flex flex-wrap items-center justify-end gap-2 max-md:[&>button]:flex-1"
      >
        <Button :label="__('Cancel')" @click="closeComposer" />
        <Button
          :label="__('Save draft')"
          :loading="composer.saving === 'draft'"
          @click="save(false)"
        />
        <Button
          variant="solid"
          :label="__('Sign')"
          :loading="composer.saving === 'sign'"
          @click="save(true)"
        />
      </div>
      <p class="text-p-xs text-ink-gray-5">
        {{
          __(
            'Signed, a record is not changed any more: it is added to. Attachments are added to a draft, and stay private.',
          )
        }}
      </p>
    </section>

    <!-- the manager: who opened the record, never what it says; the desk files
         what the patient brings, and reads no record -->
    <div
      v-if="record.data && !record.data.can_read"
      class="rounded-lg border border-dashed border-outline-gray-2 px-4 py-8 text-center text-p-base text-ink-gray-5"
    >
      {{
        record.data.can_see_log
          ? __(
              'You see who opened this record and when, not what it says: that is for the care team.',
            )
          : __(
              'The visits are for the care team. Here you file what the patient brings, for the practitioner it is for.',
            )
      }}
    </div>
    <div
      v-else-if="record.data && !record.data.records.length && !composer.open"
      class="rounded-lg border border-dashed border-outline-gray-2 px-4 py-8 text-center text-p-base text-ink-gray-5"
    >
      {{
        record.data.can_write
          ? __(
              'Nothing in the record yet. The first visit you write makes them a patient.',
            )
          : __('Nothing you can read in this record.')
      }}
    </div>

    <article
      v-for="entry in shownRecords"
      :key="entry.name"
      class="flex flex-col gap-2 rounded-lg border border-outline-gray-2 p-4"
    >
      <header class="flex flex-wrap items-start justify-between gap-2">
        <div class="flex min-w-0 flex-col">
          <div class="flex flex-wrap items-center gap-2">
            <span class="text-base-semibold text-ink-gray-8">
              {{
                entry.template
                  ? entry.title
                  : entry.kind === 'Note'
                    ? __('Note')
                    : __('Visit')
              }}
            </span>
            <Badge
              v-if="entry.docstatus === 0"
              size="sm"
              theme="orange"
              :label="__('Draft')"
            />
            <Badge
              v-if="entry.visibility === 'Only me'"
              size="sm"
              theme="gray"
              :label="__('Only me')"
            />
            <Badge
              v-if="entry.visibility === 'My discipline'"
              size="sm"
              theme="gray"
              :label="__('My discipline')"
            />
            <Badge
              v-if="entry.obscured"
              size="sm"
              theme="orange"
              :label="__('Obscured')"
            />
            <Badge
              v-if="entry.addendum_to"
              size="sm"
              theme="blue"
              :label="__('Addendum')"
            />
          </div>
          <span class="text-p-sm text-ink-gray-5">
            {{ formatDate(entry.record_date, '') }} ·
            {{ entry.practitioner_name }}
          </span>
        </div>
        <!-- the medical director, at the patient's request: the whole episode -->
        <Button
          v-if="
            record.data.can_obscure &&
            entry.docstatus === 1 &&
            !entry.addendum_to
          "
          size="sm"
          variant="ghost"
          class="touch-target shrink-0"
          :icon-left="entry.obscured ? 'eye' : 'eye-off'"
          :label="entry.obscured ? __('Reveal') : __('Obscure')"
          @click="askObscure('Clinic Record', entry)"
        />
        <!-- the actions wrap: on a phone attaching, dictating, editing and
             deleting a draft are wider than the card, and held in one line they
             pushed the whole Clinic tab sideways -->
        <div v-if="entry.mine" class="flex min-w-0 flex-wrap gap-1">
          <template v-if="entry.docstatus === 0">
            <FileUploader
              :uploadArgs="{
                doctype: 'Clinic Record',
                docname: entry.name,
                private: true,
              }"
              @success="record.reload()"
            >
              <template #default="{ openFileSelector, uploading }">
                <Button
                  size="sm"
                  variant="ghost"
                  class="touch-target"
                  :label="uploading ? __('Uploading…') : __('Attach')"
                  iconLeft="paperclip"
                  @click="openFileSelector"
                />
              </template>
            </FileUploader>
            <Button
              v-if="entry.template && record.data.assistant?.dictation"
              size="sm"
              variant="ghost"
              class="touch-target"
              :label="__('Fill from dictation')"
              iconLeft="mic"
              @click="dictating = { show: true, record: entry.name }"
            />
            <Button
              size="sm"
              variant="ghost"
              class="touch-target"
              :label="__('Edit')"
              @click="startEdit(entry)"
            />
            <Button
              size="sm"
              variant="ghost"
              theme="red"
              class="touch-target"
              :label="__('Delete')"
              @click="remove(entry)"
            />
          </template>
          <Button
            v-else
            size="sm"
            variant="ghost"
            class="touch-target"
            :label="__('Add to it')"
            iconLeft="plus"
            @click="startAddendum(entry)"
          />
          <!-- the assistant drafts from one's own signed note; the practitioner signs -->
          <Dropdown
            v-if="entry.docstatus === 1 && record.data.assistant?.drafts"
            :options="draftOptions(entry)"
            placement="right"
          >
            <!-- a verb, not the state: in Italian «Bozza» read as the badge of
                 the drafts just below -->
            <Button
              size="sm"
              variant="ghost"
              class="touch-target"
              :label="__('Draft', null, 'Assistant action')"
              iconLeft="feather"
            />
          </Dropdown>
        </div>
      </header>
      <!-- a visit on a clinical sheet: its answers, in words once signed -->
      <FormRenderer
        v-if="entry.template"
        :model-value="entry.answers"
        :schema="entry.schema"
        :readonly="true"
      />
      <!-- written in the Desk: sanitised before it is shown -->
      <!-- eslint-disable vue/no-v-html -->
      <div
        v-if="isHtml(entry.content)"
        class="prose prose-sm max-w-none text-ink-gray-8"
        v-html="sanitizeHTML(entry.content)"
      />
      <!-- eslint-enable vue/no-v-html -->
      <div
        v-else
        class="whitespace-pre-line text-p-base text-ink-gray-8 [overflow-wrap:anywhere]"
      >
        {{ entry.content }}
      </div>
      <div v-if="entry.attachments.length" class="flex flex-wrap gap-2">
        <a
          v-for="file in entry.attachments"
          :key="file.name"
          :href="file.file_url"
          target="_blank"
          rel="noopener"
          class="inline-flex max-w-full items-center gap-1 rounded-md bg-surface-gray-2 px-2 py-1 text-p-sm text-ink-gray-7 hover:bg-surface-gray-3"
        >
          <span class="lucide-paperclip size-3.5 shrink-0" aria-hidden="true" />
          <span class="truncate">{{ file.file_name }}</span>
        </a>
      </div>
      <footer
        v-if="entry.docstatus === 1 && entry.signed_on"
        class="flex flex-wrap items-center gap-2 text-p-xs text-ink-gray-5"
      >
        {{ __('Signed on {0}', [formatDate(entry.signed_on, '')]) }}
        <a
          v-if="entry.pdf_file"
          :href="entry.pdf_file"
          target="_blank"
          rel="noopener"
          class="inline-flex items-center gap-1 rounded-md bg-surface-gray-2 px-2 py-0.5 text-ink-gray-7 hover:bg-surface-gray-3"
        >
          <span class="lucide-file-text size-3.5" aria-hidden="true" />
          {{ __('Report') }}
        </a>
      </footer>
    </article>
  </div>

  <ObscureDialog
    v-model="obscuring.show"
    :doctype="obscuring.doctype"
    :name="obscuring.name"
    :title="obscuring.title"
    :about="obscuring.about"
    :obscured="obscuring.obscured"
    @done="afterObscure"
  />
  <DictationDialog
    v-model="dictating.show"
    :record="dictating.record"
    @filled="record.reload()"
  />
  <SummaryDialog v-model="summarising" :lead="lead" />
  <AssistantDraftDialog
    v-model="drafting.show"
    :record="drafting.record"
    :kind="drafting.kind"
    :can-post="Boolean(record.data?.can_message)"
    @kept="record.reload()"
  />

  <Dialog
    v-model="log.show"
    :options="{ title: __('Who opened it'), size: 'lg' }"
  >
    <template #body-content>
      <p class="mb-3 text-p-sm text-ink-gray-6">
        {{
          __(
            'Every reading from {brand} of this record, and of the documents and plans with health data, and every file downloaded: who and when, not what they read. Kept two years.',
          )
        }}
      </p>
      <div
        v-if="!log.rows.length"
        class="py-6 text-center text-p-base text-ink-gray-5"
      >
        {{ __('Nobody has opened it yet.') }}
      </div>
      <div v-else class="flex max-h-[60vh] flex-col overflow-y-auto">
        <!-- who and when on the first line, what under it as wide as the
             row: beside the date it went on two lines on a phone -->
        <div
          v-for="(row, i) in log.rows"
          :key="i"
          class="flex flex-col border-b border-outline-gray-1 py-2 text-p-sm last:border-0"
        >
          <span class="flex items-baseline justify-between gap-3">
            <span class="min-w-0 truncate text-ink-gray-8">
              {{ row.viewed_by_name || row.viewed_by }}
            </span>
            <span class="shrink-0 tabular-nums text-p-xs text-ink-gray-5">
              {{ formatDate(row.creation, '') }}
            </span>
          </span>
          <span class="text-p-xs text-ink-gray-5">
            {{ openedWhat(row) }}
          </span>
        </div>
      </div>
    </template>
  </Dialog>
</template>

<script setup>
import AssistantDraftDialog from '@/components/Clinic/AssistantDraftDialog.vue'
import DictationDialog from '@/components/Clinic/DictationDialog.vue'
import SummaryDialog from '@/components/Clinic/SummaryDialog.vue'
import DentalCard from '@/components/Clinic/DentalCard.vue'
import ClinicSummary from '@/components/Clinic/ClinicSummary.vue'
import ObscureDialog from '@/components/Clinic/ObscureDialog.vue'
import FormRenderer from '@/components/Moduli/FormRenderer.vue'
import { formatDate, sanitizeHTML } from '@/utils'
import { isMobileView } from '@/composables/breakpoints'
import {
  Badge,
  Dialog,
  Dropdown,
  ErrorMessage,
  FileUploader,
  FormControl,
  call,
  createResource,
  toast,
} from 'frappe-ui'
import { computed, nextTick, reactive, ref, watch } from 'vue'

const props = defineProps({
  lead: { type: String, required: true },
})

const record = createResource({
  url: 'crm.clinica.cartella.get_record',
  makeParams: () => ({ lead: props.lead }),
})

watch(
  () => props.lead,
  (lead) => lead && record.reload(),
  { immediate: true },
)

const kindOptions = [
  { label: __('Visit'), value: 'Visit' },
  { label: __('Note'), value: 'Note' },
]
// "my discipline" for who has one: the colleagues of the same qualification
const visibilityOptions = computed(() => [
  { label: __('The care team'), value: 'Care team' },
  ...(record.data?.discipline
    ? [{ label: __('My discipline'), value: 'My discipline' }]
    : []),
  { label: __('Only me'), value: 'Only me' },
])

const summaryRef = ref(null)

// the draft being written is above, in the composer: not twice
const shownRecords = computed(() =>
  (record.data?.records || []).filter(
    (entry) => !(composer.open && entry.name === composer.name),
  ),
)

// a free visit, then the sheets one writes on (the server puts them first and
// marks them), then the others: a sheet's specialty is tied to no
// qualification, and the dietitian was offered the dental visit beside her own
const newOptions = computed(() => {
  const sheets = record.data?.sheets || []
  const asOption = (sheet) => ({
    label: sheet.title,
    icon: 'lucide-clipboard-list',
    onClick: () => startSheet(sheet.name),
  })
  const free = {
    label: __('Free visit'),
    icon: 'lucide-file-text',
    onClick: () => startNew(),
  }
  if (!sheets.some((sheet) => sheet.mine))
    return [free, ...sheets.map(asOption)]
  return [
    free,
    {
      group: __('Your sheets'),
      items: sheets.filter((sheet) => sheet.mine).map(asOption),
    },
    {
      group: __('Other sheets'),
      items: sheets.filter((sheet) => !sheet.mine).map(asOption),
    },
  ]
})

const composer = reactive({
  open: false,
  sheet: null,
  answers: {},
  tried: false,
  name: null,
  addendumTo: null,
  addendumLabel: '',
  kind: 'Visit',
  visibility: 'Care team',
  content: '',
  error: '',
  saving: '',
})

const composerRef = ref(null)

function reset(values = {}) {
  Object.assign(composer, {
    open: true,
    sheet: null,
    answers: {},
    tried: false,
    name: null,
    addendumTo: null,
    addendumLabel: '',
    kind: 'Visit',
    visibility: 'Care team',
    content: '',
    error: '',
    saving: '',
    ...values,
  })
  // after the change, so the tick waits for the composer to be drawn
  nextTick(() =>
    composerRef.value?.scrollIntoView({ behavior: 'smooth', block: 'start' }),
  )
}

function startNew() {
  reset()
}

function startEdit(entry) {
  reset({
    name: entry.name,
    kind: entry.kind,
    visibility: entry.visibility,
    content: entry.content || '',
    sheet: entry.template ? { title: entry.title, schema: entry.schema } : null,
    answers: { ...(entry.answers || {}) },
  })
}

async function startSheet(template) {
  try {
    const entry = await call('crm.clinica.cartella.start_sheet', {
      lead: props.lead,
      template,
    })
    startEdit(entry)
    record.reload()
  } catch (err) {
    toast.error(err.messages?.[0] || err.message)
  }
}

const drafting = reactive({ show: false, record: null, kind: 'letter' })
const dictating = ref({ show: false, record: null })
const summarising = ref(false)

// the record's actions beside «New visit»
const altreAzioni = computed(() =>
  [
    record.data?.assistant?.summary && {
      label: __('Summary before the visit'),
      icon: 'book-open',
      onClick: () => (summarising.value = true),
    },
    record.data?.can_see_log && {
      label: __('Who opened it'),
      icon: 'eye',
      onClick: openLog,
    },
  ].filter(Boolean),
)
const sottoAltro = computed(
  () => isMobileView.value && altreAzioni.value.length > 1,
)

function draftOptions(entry) {
  const open = (kind) =>
    Object.assign(drafting, { show: true, record: entry.name, kind })
  return [
    {
      label: __('A letter to the family doctor'),
      onClick: () => open('letter'),
    },
    {
      label: __('Instructions after the visit'),
      onClick: () => open('instructions'),
    },
  ]
}

function startAddendum(entry) {
  reset({
    addendumTo: entry.name,
    addendumLabel: formatDate(entry.record_date, ''),
    kind: entry.kind,
    visibility: entry.visibility,
  })
}

function closeComposer() {
  composer.open = false
}

function isHtml(text) {
  return /<[a-z][\s\S]*>/i.test(text || '')
}

async function save(sign) {
  composer.tried = sign
  composer.saving = sign ? 'sign' : 'draft'
  composer.error = ''
  try {
    await call('crm.clinica.cartella.save_record', {
      lead: props.lead,
      name: composer.name,
      kind: composer.kind,
      visibility: composer.visibility,
      content: composer.content,
      addendum_to: composer.addendumTo,
      sign: sign ? 1 : 0,
      answers: composer.sheet ? JSON.stringify(composer.answers) : undefined,
    })
    composer.open = false
    toast.success(sign ? __('Signed') : __('Draft saved'))
    record.reload()
    // a signed sheet may propose lines of the summary; a signed visit files
    // its report among the person's documents (the Documents tab)
    if (sign && composer.sheet) summaryRef.value?.reload()
  } catch (err) {
    composer.error = err.messages?.[0] || err.message
  } finally {
    composer.saving = ''
  }
}

async function remove(entry) {
  try {
    await call('crm.clinica.cartella.delete_draft', { name: entry.name })
    record.reload()
  } catch (err) {
    toast.error(err.messages?.[0] || __('Could not delete the draft'))
  }
}

const log = reactive({ show: false, rows: [] })

// what was opened, never what it said; an opening out of the care team says why
function openedWhat(row) {
  if (row.kind === 'out_of_care') {
    return __('Opened out of their care: {0}', [row.reason])
  }
  const what =
    row.kind === 'record'
      ? __('Opened the record')
      : row.kind === 'documents'
        ? __('Opened the documents')
        : row.kind === 'plan'
          ? __('Opened a plan')
          : row.kind === 'programme'
            ? __('Opened a programme')
            : row.kind === 'dental chart'
              ? __('Opened the dental chart')
              : row.kind === 'quote'
                ? __('Opened a quote')
                : __('Downloaded a file')
  return row.count > 1 ? __('{0} · {1} entries', [what, row.count]) : what
}

const obscuring = reactive({
  show: false,
  doctype: 'Clinic Record',
  name: null,
  title: '',
  about: '',
  obscured: false,
})

function askObscure(doctype, entry) {
  Object.assign(obscuring, {
    show: true,
    doctype,
    name: entry.name,
    title: entry.title || (entry.kind === 'Note' ? __('Note') : __('Visit')),
    about: [formatDate(entry.record_date, ''), entry.practitioner_name]
      .filter(Boolean)
      .join(' · '),
    obscured: Boolean(entry.obscured),
  })
}

function afterObscure() {
  record.reload()
}

async function openLog() {
  log.rows = await call('crm.clinica.cartella.access_log', { lead: props.lead })
  log.show = true
}
</script>
