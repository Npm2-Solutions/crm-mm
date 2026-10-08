<!--
  Copyright (c) 2026, NPM2 Solutions Srl and contributors
  For license information, please see license.txt

  Review requests after a visit (crm/recensioni): where the review is written on
  Google, how often the same person is asked, the services nobody is asked after.
  An automation asks by writing {{ review_link }} in its message (the recipe
  «Ask for a review after the visit», off to start with); the server lets it
  leave only to who agreed to these requests or to marketing. Never whom: Google
  forbids choosing who is asked, and offering anything for a review.
-->
<template>
  <SettingsLayoutBase>
    <template #title>
      <h2 class="text-2xl-semibold text-ink-gray-9">
        {{ __('Review requests') }}
      </h2>
    </template>
    <template #header-actions>
      <AzioneImpostazioni :loading="saving" :disabled="!dirty" @click="save" />
    </template>
    <template #content>
      <div v-if="settings.data" class="flex flex-col gap-4 pb-6">
        <p
          class="rounded-md bg-surface-gray-2 px-3 py-2 text-p-sm text-ink-gray-7"
        >
          {{
            __(
              'Everybody is asked the same way, with nothing in return: Google forbids choosing who is asked and offering anything for a review. Only who agreed to these requests, or to marketing, is asked; the automation «Ask for a review after the visit» sends the link, off until you switch it on.',
            )
          }}
        </p>
        <div class="flex flex-col gap-1.5 px-2">
          <FormControl
            v-model="form.google_review_link"
            type="url"
            :label="__('Google review link')"
            placeholder="https://g.page/r/…/review"
            v-bind="tastiera('url')"
          />
          <span class="text-p-sm text-ink-gray-5">
            {{
              __(
                'In your Google Business Profile, «Ask for reviews» gives the link to copy here.',
              )
            }}
          </span>
        </div>
        <div class="flex flex-col gap-1.5 px-2">
          <FormControl
            v-model="form.google_place_id"
            type="text"
            :label="__('Google Place ID')"
            v-bind="tastiera('codice')"
          />
          <span class="text-p-sm text-ink-gray-5">
            {{ __('Without the link, the centre’s Place ID makes it.') }}
          </span>
        </div>
        <SettingsRow
          :label="__('Months before asking again')"
          :description="
            __(
              'The same person is not asked again before then, whatever automation asks.',
            )
          "
        >
          <FormControl
            v-model="form.months_between"
            type="number"
            class="w-24"
            min="1"
            max="60"
            inputmode="numeric"
            :aria-label="__('Months before asking again')"
          />
        </SettingsRow>
        <div class="flex flex-col gap-2 px-2">
          <div class="flex flex-col gap-0.5">
            <span class="text-p-base-medium text-ink-gray-7">
              {{ __('Services excluded') }}
            </span>
            <span class="text-p-sm text-ink-gray-5">
              {{
                __(
                  'After these services nobody is asked: a certificate, a blood test.',
                )
              }}
            </span>
          </div>
          <div
            v-if="settings.data.services.length"
            class="grid grid-cols-[repeat(auto-fit,minmax(12rem,1fr))] gap-x-4 gap-y-1"
          >
            <FormControl
              v-for="service in settings.data.services"
              :key="service.value"
              type="checkbox"
              :label="service.label"
              :modelValue="form.excluded_services.includes(service.value)"
              @update:modelValue="(on) => toggle(service.value, on)"
            />
          </div>
          <span v-else class="text-p-sm text-ink-gray-5">
            {{ __('No service yet.') }}
          </span>
        </div>
        <ErrorMessage :message="error" />
      </div>
      <div v-else class="mt-[35%] flex items-center justify-center">
        <LoadingIndicator class="size-6" />
      </div>
    </template>
  </SettingsLayoutBase>
</template>

<script setup>
import AzioneImpostazioni from '@/components/Settings/AzioneImpostazioni.vue'
import SettingsLayoutBase from '@/components/Layouts/SettingsLayoutBase.vue'
import SettingsRow from '@/components/Settings/SettingsRow.vue'
import { tastiera } from '@/utils/tastiera'
import {
  ErrorMessage,
  FormControl,
  LoadingIndicator,
  call,
  createResource,
  toast,
} from 'frappe-ui'
import { computed, reactive, ref } from 'vue'

const form = reactive({
  google_review_link: '',
  google_place_id: '',
  months_between: 12,
  excluded_services: [],
})
const saved = ref('')
const saving = ref(false)
const error = ref('')

const snapshot = () => JSON.stringify(form)

function fill(data) {
  form.google_review_link = data.google_review_link || ''
  form.google_place_id = data.google_place_id || ''
  form.months_between = data.months_between || 12
  form.excluded_services = [...(data.excluded_services || [])]
  saved.value = snapshot()
}

const settings = createResource({
  url: 'crm.recensioni.chiedi.get_settings',
  auto: true,
  onSuccess: fill,
})

const dirty = computed(() => saved.value !== snapshot())

function toggle(service, on) {
  const others = form.excluded_services.filter((name) => name !== service)
  form.excluded_services = on ? [...others, service] : others
}

async function save() {
  saving.value = true
  error.value = ''
  try {
    const data = await call('crm.recensioni.chiedi.save_settings', {
      google_review_link: form.google_review_link.trim() || null,
      google_place_id: form.google_place_id.trim() || null,
      months_between: Number(form.months_between) || 12,
      excluded_services: JSON.stringify(form.excluded_services),
    })
    settings.data = data
    fill(data)
    toast.success(__('Saved'))
  } catch (e) {
    error.value = e.messages?.join(' ') || e.message
  } finally {
    saving.value = false
  }
}
</script>
