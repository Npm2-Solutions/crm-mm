<!--
  A document for the clinical archive: a file uploaded here, or one received in
  a conversation (`message`), or an existing document to put right (`document`:
  what it is, when, where it comes from, whom it is for; the file stays).

  A practitioner files for themselves and may keep it to themselves; the front
  desk says which practitioner it is for, and then sees only what it added.
-->
<template>
  <Dialog v-model="show" :options="{ title: dialogTitle, size: 'lg' }">
    <template #body-content>
      <div class="flex flex-col gap-4">
        <!-- the file: uploaded private, attached to nothing until it is filed -->
        <FileUploader
          v-if="!document && !message"
          :uploadArgs="{ private: true }"
          @success="chosen"
        >
          <template #default="{ openFileSelector, uploading, progress }">
            <div class="flex min-w-0 flex-wrap items-center gap-2">
              <Button
                icon-left="upload"
                :label="
                  uploading
                    ? __('Uploading {0}%', [progress])
                    : file
                      ? __('Choose another file')
                      : __('Choose the file')
                "
                @click="openFileSelector"
              />
              <span
                v-if="file"
                class="min-w-0 truncate text-sm text-ink-gray-7"
              >
                {{ file.file_name }}
              </span>
            </div>
          </template>
        </FileUploader>
        <div
          v-else-if="fileName"
          class="flex min-w-0 items-center gap-2 text-sm text-ink-gray-7"
        >
          <span class="lucide-paperclip size-4 shrink-0" aria-hidden="true" />
          <span class="min-w-0 truncate">{{ fileName }}</span>
        </div>

        <FormControl
          v-model="form.title"
          :label="__('Title')"
          :placeholder="__('Blood tests, chest X-ray, cardiology report…')"
        />
        <div class="grid grid-cols-2 gap-3 max-md:grid-cols-1">
          <FormControl
            v-model="form.document_type"
            type="select"
            :label="__('Kind')"
            :options="choices.data?.types || []"
          />
          <FormControl
            v-model="form.document_date"
            type="date"
            :label="__('Date of the document')"
          />
        </div>
        <FormControl
          v-model="form.source"
          :label="__('Comes from')"
          :placeholder="__('The laboratory, the hospital, the doctor')"
        />
        <div class="grid grid-cols-2 gap-3 max-md:grid-cols-1">
          <FormControl
            v-model="form.practitioner"
            type="select"
            :label="__('For')"
            :options="practitionerOptions"
          />
          <FormControl
            v-if="mine"
            v-model="form.visibility"
            type="select"
            :label="__('Who reads it')"
            :options="visibilityOptions"
          />
        </div>
        <FormControl
          v-model="form.notes"
          type="textarea"
          :rows="2"
          :label="__('Notes')"
        />
        <!-- genetic tests, HIV, or a test the patient left out: by hand only -->
        <label v-if="choices.data?.for_me" class="flex items-start gap-2">
          <Checkbox
            v-model="form.not_online"
            class="touch-target mt-0.5 shrink-0"
          />
          <span class="text-base text-ink-gray-8">
            {{ __('Never online') }}
            <span class="block text-p-sm text-ink-gray-5">
              {{
                __(
                  'Genetic tests, HIV, or a test the patient left out: it is given by hand only.',
                )
              }}
            </span>
          </span>
        </label>
        <p class="text-p-xs text-ink-gray-5">
          {{
            message
              ? __(
                  'The archive keeps a private copy; in the conversation the file stays, private too.',
                )
              : __(
                  'The file is private: whoever reads the archive opens it, and every opening is logged.',
                )
          }}
        </p>
        <ErrorMessage :message="error" />
      </div>
    </template>
    <template #actions>
      <div class="dialog-footer flex justify-end gap-2">
        <Button :label="__('Cancel')" @click="show = false" />
        <Button
          variant="solid"
          :label="document ? __('Save') : __('Add to the archive')"
          :disabled="!ready"
          :loading="saving"
          @click="save"
        />
      </div>
    </template>
  </Dialog>
</template>

<script setup>
import { usersStore } from '@/stores/users'
import {
  Button,
  Checkbox,
  Dialog,
  ErrorMessage,
  FileUploader,
  FormControl,
  call,
  createResource,
} from 'frappe-ui'
import { computed, reactive, ref, watch } from 'vue'

const props = defineProps({
  // the person, for a file uploaded here
  lead: { type: String, default: null },
  // a WhatsApp message whose file goes to the archive
  message: { type: String, default: null },
  messageFileName: { type: String, default: null },
  // what the person wrote with it, a better title than a file's name
  suggestedTitle: { type: String, default: '' },
  // an existing document to put right
  document: { type: Object, default: null },
})
const emit = defineEmits(['saved'])
const show = defineModel({ type: Boolean })

const { getUser } = usersStore()

const choices = createResource({
  url: 'crm.clinica.archivio.get_choices',
  cache: 'clinicArchiveChoices',
})

const file = ref(null)
const error = ref('')
const saving = ref(false)
const form = reactive({
  title: '',
  document_type: 'External report',
  document_date: '',
  source: '',
  practitioner: '',
  visibility: 'Care team',
  notes: '',
  not_online: false,
})

const dialogTitle = computed(() =>
  props.document
    ? __('Document')
    : props.message
      ? __('Add to the clinical archive')
      : __('Add a document'),
)
const fileName = computed(
  () => props.document?.file_name || props.messageFileName || '',
)
const me = computed(() => getUser().name)
// "only me" is a practitioner's choice about their own document
const mine = computed(
  () => choices.data?.for_me && form.practitioner === me.value,
)
const practitionerOptions = computed(() => [
  { label: __('Choose…'), value: '' },
  ...(choices.data?.practitioners || []),
])
const visibilityOptions = computed(() => [
  { label: __('Care team'), value: 'Care team' },
  ...(choices.data?.discipline
    ? [{ label: __('My discipline'), value: 'My discipline' }]
    : []),
  { label: __('Only me'), value: 'Only me' },
])
const ready = computed(
  () =>
    form.title.trim() &&
    form.document_type &&
    form.practitioner &&
    (props.document || props.message || file.value),
)

watch(show, (open) => {
  if (!open) return
  error.value = ''
  file.value = null
  choices.fetch().then(() => fill())
  fill()
})

function fill() {
  const doc = props.document
  Object.assign(form, {
    title:
      doc?.title || props.suggestedTitle || readable(props.messageFileName),
    document_type: doc?.document_type || 'External report',
    document_date: doc?.document_date || '',
    source: doc?.source || '',
    practitioner:
      doc?.practitioner || (choices.data?.for_me ? me.value : '') || '',
    visibility: doc?.visibility || 'Care team',
    notes: doc?.notes || '',
    not_online: Boolean(doc?.not_online),
  })
}

function withoutExtension(name) {
  return (name || '').replace(/\.[^.]+$/, '')
}

// a file received on WhatsApp is named by a random hash: no title in that
function readable(name) {
  const title = withoutExtension(name)
  return /^[0-9a-f]{8,}$/i.test(title) ? '' : title
}

function chosen(uploaded) {
  file.value = uploaded
  if (!form.title.trim()) form.title = withoutExtension(uploaded.file_name)
}

async function save() {
  saving.value = true
  error.value = ''
  const fields = {
    title: form.title,
    document_type: form.document_type,
    document_date: form.document_date || null,
    source: form.source,
    practitioner: form.practitioner,
    visibility: mine.value ? form.visibility : 'Care team',
    notes: form.notes,
    not_online: form.not_online ? 1 : 0,
  }
  try {
    const saved = props.document
      ? await call('crm.clinica.archivio.update_document', {
          name: props.document.name,
          ...fields,
        })
      : props.message
        ? await call('crm.clinica.archivio.archive_from_message', {
            message: props.message,
            ...fields,
          })
        : await call('crm.clinica.archivio.add_document', {
            lead: props.lead,
            file: file.value.name,
            ...fields,
          })
    emit('saved', saved)
    show.value = false
  } catch (e) {
    error.value = e.messages?.join(' ') || e.message
  } finally {
    saving.value = false
  }
}
</script>
