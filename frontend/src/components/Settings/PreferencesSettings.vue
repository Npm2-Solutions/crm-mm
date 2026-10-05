<!--
  Modifications copyright (c) 2026, NPM2 Solutions Srl

  On a phone a setting's words come first and its field under them, as wide
  as the screen. The language is the centre's, or Italian or English for the
  user alone (crm/lingue.py: the two DottorCloud speaks); the clock one of
  Europe's.
-->
<template>
  <SettingsLayoutBase
    v-if="user.doc"
    :title="__('Preferences')"
    :description="
      __(
        'Choose how you want to use the application by setting your preferences.',
      )
    "
  >
    <template #content>
      <div>
        <div class="flex items-center justify-between">
          <div class="flex gap-2 items-center">
            <div class="text-base-semibold text-ink-gray-9">
              {{ __('Appearance') }}
            </div>
          </div>
        </div>
        <div class="flex flex-col gap-4 my-6">
          <div class="flex flex-col gap-1">
            <span class="text-base-medium text-ink-gray-8">
              {{ __('Theme') }}
            </span>
            <span class="text-p-sm text-ink-gray-6">
              {{ __('Switch between light, dark, or system theme') }}
            </span>
          </div>
          <ThemeSwitcher :logo="CRMLogo" :name="platform.name" />
        </div>
        <div class="flex items-center justify-between">
          <div class="flex gap-2 items-center h-7">
            <div class="text-base-semibold text-ink-gray-9">
              {{ __('Language & Time') }}
            </div>
            <Badge
              v-if="isDirty"
              :variant="'subtle'"
              :theme="'orange'"
              size="sm"
              :label="__('Not Saved')"
            />
          </div>
          <AzioneImpostazioni
            v-if="isDirty"
            :label="__('Save')"
            :loading="user.save.loading"
            @click="save()"
          />
        </div>
        <div
          class="mt-6 flex items-center justify-between gap-3 max-md:flex-col max-md:items-stretch max-md:gap-2"
        >
          <div class="flex min-w-0 flex-col gap-1">
            <span class="text-base-medium text-ink-gray-8">
              {{ __('Language') }}
            </span>
            <span class="text-p-sm text-ink-gray-6">
              {{
                __(
                  'The language you read {brand} in: the centre’s, or your own.',
                )
              }}
            </span>
          </div>
          <!-- empty is the centre's, and follows it when it changes; the
               select fills the box it is given, so the box is its width -->
          <div class="w-48 shrink-0 max-md:w-full">
            <FormControl
              v-model="lingua"
              type="select"
              :options="lingue"
              :aria-label="__('Language')"
            />
          </div>
        </div>
        <div
          class="mt-6 flex items-center justify-between gap-3 max-md:flex-col max-md:items-stretch max-md:gap-2"
        >
          <div class="flex min-w-0 flex-col gap-1">
            <span class="text-base-medium text-ink-gray-8">
              {{ __('Timezone') }}
            </span>
            <span class="text-p-sm text-ink-gray-6">
              {{
                __(
                  'The clock you read the hours on. The agenda keeps the centre’s.',
                )
              }}
            </span>
          </div>
          <div class="w-80 shrink-0 max-md:w-full">
            <FormControl
              v-model="user.doc.time_zone"
              type="select"
              :options="fusi"
              :aria-label="__('Timezone')"
            />
          </div>
        </div>
      </div>
    </template>
  </SettingsLayoutBase>
</template>

<script setup>
import AzioneImpostazioni from '@/components/Settings/AzioneImpostazioni.vue'
import CRMLogo from '@/components/Icons/CRMLogo.vue'
import { marchio } from '@/utils/marchio'
import ThemeSwitcher from '@/components/Settings/ThemeSwitcher.vue'
import SettingsLayoutBase from '@/components/Layouts/SettingsLayoutBase.vue'
import { useKeyboardShortcuts } from '@/composables/useKeyboardShortcuts'
import { europei, fusiOrari } from '@/utils/fusiOrari'
import { appLocale } from '@/utils/locale'
import {
  FormControl,
  Badge,
  toast,
  createResource,
  createDocumentResource,
} from 'frappe-ui'
import { ref, computed, inject } from 'vue'

const refreshRequired = ref(false)

const { user: sessionUser } = inject('session')

const platform = marchio()
const user = createDocumentResource({ doctype: 'User', name: sessionUser })

function save() {
  refreshRequired.value =
    user.doc.language !== user.originalDoc?.language ||
    user.doc.time_zone !== user.originalDoc?.time_zone

  user.save.submit(null, {
    onSuccess: () => {
      toast.success(__('Preferences updated successfully'))
      if (refreshRequired.value) {
        window.location.reload()
      }
    },
    // the server's words, never its code («PermissionError: …»)
    onError: (err) => {
      toast.error(err.messages?.join(' ') || __('The choice was not saved'))
    },
  })
}

// the two this page writes, an empty language the same as none
const isDirty = computed(
  () =>
    Boolean(user.doc) &&
    ((user.doc.language || '') !== (user.originalDoc?.language || '') ||
      (user.doc.time_zone || '') !== (user.originalDoc?.time_zone || '')),
)

// each language in its own words, as a choice of language names it
const NOMI = { it: 'Italiano', en: 'English' }
const lingue = computed(() => [
  {
    label: __('As the centre ({0})', [
      NOMI[window.centre_language] || window.centre_language || '—',
    ]),
    value: '',
  },
  { label: NOMI.it, value: 'it' },
  { label: NOMI.en, value: 'en' },
])
const lingua = computed({
  get: () => user.doc?.language || '',
  set: (valore) => (user.doc.language = valore),
})

const timeZones = createResource({
  url: 'frappe.core.doctype.user.user.get_timezones',
  cache: 'TimeZones',
  auto: true,
})

// Europe's, each by its name in the reader's language, the device's and
// Italy's first; the one kept stays a choice wherever it is
const fusi = computed(() =>
  fusiOrari({
    zone: europei(timeZones.data?.timezones || []),
    scelto: user.doc?.time_zone || '',
    dispositivo: Intl.DateTimeFormat().resolvedOptions().timeZone,
    lingua: appLocale() || 'it',
  }),
)

useKeyboardShortcuts({
  ignoreTyping: false,
  shortcuts: [
    {
      match: (e) => (e.metaKey || e.ctrlKey) && e.key.toLowerCase() === 's',
      action: () => {
        if (isDirty.value) {
          save()
        }
      },
    },
  ],
})
</script>
