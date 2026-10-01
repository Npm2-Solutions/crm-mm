<template>
  <div
    class="flex h-full flex-col gap-6 py-8 px-6 text-ink-gray-8 max-md:px-3 max-md:py-5"
  >
    <div
      class="flex items-start justify-between gap-4 px-2 max-md:flex-col max-md:items-start max-md:gap-3"
    >
      <div class="flex min-w-0 flex-col gap-1">
        <h2
          class="flex gap-2 text-2xl-semibold leading-tight md:h-5 md:leading-none"
        >
          {{ __('Consents') }}
        </h2>
        <p class="text-p-base text-ink-gray-6">
          {{
            __(
              'What you ask people to agree to, and the words they read. Have the texts checked by whoever answers for privacy: each change is a new version, and the answers already given keep the words they were given on.',
            )
          }}
        </p>
      </div>
      <Button
        class="shrink-0"
        :label="__('New consent')"
        icon-left="plus"
        @click="startNew"
      />
    </div>

    <div class="flex flex-1 flex-col gap-4 overflow-y-auto px-2">
      <!-- a consent of the centre's own: photos for the social pages, a newsletter -->
      <section
        v-if="draft"
        class="flex flex-col gap-3 rounded-lg border border-outline-gray-3 p-4"
      >
        <div class="grid grid-cols-2 gap-3 max-md:grid-cols-1">
          <FormControl
            v-model="draft.label"
            :label="__('Name')"
            :placeholder="__('Photos on social media')"
          />
          <FormControl
            v-model="draft.kind"
            type="select"
            :label="__('Kind')"
            :options="kindOptions"
          />
        </div>
        <FormControl
          v-model="draft.text"
          type="textarea"
          :rows="4"
          :label="__('What the person reads')"
        />
        <ErrorMessage :message="draft.error" />
        <div class="flex justify-end gap-2">
          <Button :label="__('Cancel')" @click="draft = null" />
          <Button
            variant="solid"
            :label="__('Create')"
            :loading="draft.saving"
            :disabled="!draft.label?.trim() || !draft.text?.trim()"
            @click="create"
          />
        </div>
      </section>

      <section
        v-for="type in types"
        :key="type.name"
        class="flex flex-col gap-3 rounded-lg border border-outline-gray-2 p-4"
      >
        <div class="flex items-start justify-between gap-3">
          <div class="flex min-w-0 flex-col gap-0.5">
            <div class="flex flex-wrap items-center gap-2">
              <!-- the standard kinds are written in English when they are
                   created: the translator gives them the user's words, a kind
                   the centre wrote stays as it is -->
              <span class="text-base-semibold text-ink-gray-8">
                {{ __(type.label) }}
              </span>
              <Badge
                variant="subtle"
                theme="gray"
                :label="
                  type.kind === 'Consent'
                    ? __('Consent')
                    : __('Acknowledgement')
                "
              />
            </div>
            <span class="text-p-sm text-ink-gray-5">
              {{
                __('Version {0}, since {1}', [
                  type.text_version,
                  formatDate(type.text_updated_on, '', true),
                ])
              }}
            </span>
          </div>
          <Switch
            v-model="type.enabled"
            class="shrink-0"
            :disabled="!!type.saving"
            @update:modelValue="(v) => save(type, { enabled: v ? 1 : 0 })"
          />
        </div>
        <p v-if="type.description" class="text-p-sm text-ink-gray-6">
          {{ __(type.description) }}
        </p>
        <FormControl
          v-model="type.draftText"
          type="textarea"
          :rows="3"
          :label="__('What the person reads')"
        />
        <div
          v-if="type.draftText !== type.text"
          class="flex items-center justify-end gap-2 max-md:flex-col max-md:items-stretch"
        >
          <span class="text-p-sm text-ink-gray-5 max-md:text-center">
            {{
              __('Saving makes it version {0}', [(type.text_version || 1) + 1])
            }}
          </span>
          <Button :label="__('Discard')" @click="type.draftText = type.text" />
          <Button
            variant="solid"
            :label="__('Save text')"
            :loading="type.saving === 'text'"
            @click="save(type, { text: type.draftText }, 'text')"
          />
        </div>
      </section>
    </div>
  </div>
</template>

<script setup>
import { formatDate } from '@/utils'
import {
  Badge,
  Button,
  ErrorMessage,
  FormControl,
  Switch,
  call,
  createResource,
  toast,
} from 'frappe-ui'
import { ref } from 'vue'

const types = ref([])

const load = createResource({
  url: 'crm.moduli.consensi.consent_types',
  auto: true,
  onSuccess: (data) => {
    types.value = (data || []).map((t) => ({
      ...t,
      enabled: Boolean(t.enabled),
      draftText: t.text,
      saving: '',
    }))
  },
})

const kindOptions = [
  { label: __('Consent: can be withdrawn'), value: 'Consent' },
  { label: __('Acknowledgement: read once'), value: 'Acknowledgement' },
]

async function save(type, values, saving = 'enabled') {
  type.saving = saving
  try {
    const data = await call('crm.moduli.consensi.save_consent_type', {
      key: type.name,
      ...values,
    })
    Object.assign(type, data, {
      enabled: Boolean(data.enabled),
      draftText: data.text,
    })
    toast.success(__('Saved'))
  } catch (err) {
    toast.error(err.messages?.[0] || __('Could not save'))
    load.reload()
  } finally {
    type.saving = ''
  }
}

const draft = ref(null)

function startNew() {
  draft.value = {
    label: '',
    kind: 'Consent',
    text: '',
    error: '',
    saving: false,
  }
}

async function create() {
  draft.value.saving = true
  draft.value.error = ''
  try {
    await call('crm.moduli.consensi.new_consent_type', {
      label: draft.value.label.trim(),
      text: draft.value.text.trim(),
      kind: draft.value.kind,
    })
    draft.value = null
    load.reload()
  } catch (err) {
    draft.value.error = err.messages?.[0] || err.message
    draft.value.saving = false
  }
}
</script>
