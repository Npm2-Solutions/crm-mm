<template>
  <div
    class="flex h-full flex-col gap-6 py-8 px-6 text-ink-gray-8 max-md:px-3 max-md:py-5"
  >
    <div
      class="flex justify-between px-2 max-md:flex-col max-md:items-start max-md:gap-3"
    >
      <div class="flex flex-col gap-1">
        <h2
          class="flex gap-2 text-2xl-semibold leading-tight md:h-5 md:leading-none"
        >
          {{ __('Lead Tracking') }}
        </h2>
        <p class="text-p-base text-ink-gray-6">
          {{
            __(
              'Record where every lead came from — the campaign, the pages they read, the links they clicked — on your own sites as well as inside {brand}.',
            )
          }}
        </p>
      </div>
      <div class="flex items-center space-x-2 justify-end">
        <Button
          v-if="isDirty"
          :label="__('Update')"
          variant="solid"
          :loading="settings.save.loading"
          @click="updateSettings"
        />
      </div>
    </div>

    <div class="flex-1 flex flex-col gap-6 overflow-y-auto px-2">
      <!-- the snippet: the one thing a new install actually has to do. Putting
           it on the site is the agency's job (doc 30), with which sites may
           send data, which addresses are left out and how long history is
           kept; the centre gets the numbers and the rest of the switches -->
      <p v-if="!tecnico" class="text-p-sm text-ink-gray-6">
        {{
          __(
            'The agency puts the tracking script on your website, and decides which sites may send data and how long anonymous browsing is kept.',
          )
        }}
      </p>
      <div v-if="tecnico">
        <div class="flex flex-col gap-1">
          <span class="text-lg-semibold text-ink-gray-8">
            {{ __('Tracking script') }}
          </span>
          <span class="text-p-sm text-ink-gray-6">
            {{ __('Paste this in the head of every page you want tracked.') }}
          </span>
        </div>
        <div class="relative mt-3.5">
          <textarea
            readonly
            rows="2"
            class="w-full resize-none rounded-md border border-outline-gray-2 bg-surface-gray-1 py-2 pl-3 pr-10 font-mono text-xs text-ink-gray-7 focus:border-outline-gray-4 focus:outline-none focus:ring-0 focus-visible:outline-none"
            :value="snippet.data?.snippet || ''"
          />
          <button
            class="touch-target absolute right-2 top-2 flex text-ink-gray-5 transition-colors hover:text-ink-gray-8"
            :title="__('Copy')"
            @click="copySnippet"
          >
            <LucideCopy class="h-4 w-4" />
          </button>
        </div>
      </div>

      <div v-if="stats">
        <hr class="mb-8 border-outline-gray-2" />
        <div class="grid grid-cols-2 gap-3 sm:grid-cols-4">
          <div
            v-for="stat in stats"
            :key="stat.label"
            class="rounded-md border border-outline-gray-2 bg-surface-gray-1 px-3 py-2.5"
          >
            <div class="text-2xl-semibold text-ink-gray-8">
              {{ stat.value }}
            </div>
            <div class="text-p-sm text-ink-gray-5">{{ stat.label }}</div>
          </div>
        </div>
      </div>

      <div v-if="settings.doc" class="flex flex-col">
        <hr class="mb-4 border-outline-gray-2" />
        <SettingsRow
          :label="__('Enable lead tracking')"
          :description="
            __(
              'The master switch. With this off nothing is collected and the script goes quiet.',
            )
          "
        >
          <Switch v-model="settings.doc.enabled" />
        </SettingsRow>

        <SettingsRow
          :label="__('Track anonymous visitors')"
          :description="
            __(
              'Record sessions and page views before a visitor identifies. Off means only the submission itself is attributed, with no browsing history.',
            )
          "
        >
          <Switch v-model="settings.doc.track_anonymous" />
        </SettingsRow>

        <SettingsRow
          :label="__('Session timeout')"
          :description="
            __(
              'Minutes of inactivity after which the next page view starts a new session. A new campaign always starts one regardless.',
            )
          "
        >
          <FormControl
            v-model.number="settings.doc.session_timeout_minutes"
            type="number"
            class="w-24"
          />
        </SettingsRow>

        <SettingsRow
          v-if="tecnico"
          :label="__('Allowed origins')"
          :description="
            __(
              'One origin per line (https://www.example.com). Leave empty while testing — an empty list accepts any site.',
            )
          "
        >
          <FormControl
            v-model="settings.doc.allowed_origins"
            type="textarea"
            :rows="3"
            class="w-64"
            placeholder="https://www.example.com"
          />
        </SettingsRow>

        <hr class="my-4 border-outline-gray-2" />
        <span class="px-2 py-1 text-lg-semibold text-ink-gray-8">
          {{ __('Privacy') }}
        </span>

        <SettingsRow
          :label="__('Require consent')"
          :description="
            __(
              'Collect nothing until your cookie banner calls CRMTracker.consent(true).',
            )
          "
        >
          <Switch v-model="settings.doc.require_consent" />
        </SettingsRow>

        <SettingsRow :label="__('Respect Do Not Track')" description="">
          <Switch v-model="settings.doc.respect_do_not_track" />
        </SettingsRow>

        <SettingsRow
          :label="__('Exclude bots')"
          :description="
            __('Ignore crawlers, uptime monitors and headless browsers.')
          "
        >
          <Switch v-model="settings.doc.exclude_bots" />
        </SettingsRow>

        <SettingsRow
          :label="__('Store IP address')"
          :description="
            __(
              'Anonymised by default: the last octet is dropped before storing.',
            )
          "
        >
          <div class="flex items-center gap-3">
            <Switch v-model="settings.doc.store_ip_address" />
            <span
              v-if="settings.doc.store_ip_address"
              class="flex items-center gap-2"
            >
              <span class="text-p-sm text-ink-gray-5">{{
                __('Anonymize')
              }}</span>
              <Switch v-model="settings.doc.anonymize_ip" />
            </span>
          </div>
        </SettingsRow>

        <SettingsRow
          v-if="tecnico"
          :label="__('Excluded IPs')"
          :description="
            __(
              'One per line. Put your own office here so internal browsing stays out of the reports.',
            )
          "
        >
          <FormControl
            v-model="settings.doc.excluded_ips"
            type="textarea"
            :rows="2"
            class="w-64"
          />
        </SettingsRow>

        <SettingsRow
          v-if="tecnico"
          :label="__('Retention')"
          :description="
            __(
              'Days after which anonymous browsing history is deleted. History attached to a lead or deal is always kept. 0 disables the cleanup.',
            )
          "
        >
          <FormControl
            v-model.number="settings.doc.retention_days"
            type="number"
            class="w-24"
          />
        </SettingsRow>
      </div>
    </div>
  </div>
</template>

<script setup>
import SettingsRow from '@/components/Settings/SettingsRow.vue'
import LucideCopy from '~icons/lucide/copy'
import { copyToClipboard } from '@/utils'
import { usersStore } from '@/stores/users'
import {
  Button,
  FormControl,
  Switch,
  createDocumentResource,
  createResource,
  toast,
} from 'frappe-ui'
import { useTelemetry } from 'frappe-ui/frappe'
import { computed } from 'vue'

const { capture } = useTelemetry()

// the tag, the origins, the excluded addresses and the retention are the agency's
const tecnico = usersStore().puo('tecnico.integrazioni')

const settings = createDocumentResource({
  doctype: 'CRM Tracking Settings',
  name: 'CRM Tracking Settings',
  auto: true,
})

const snippet = createResource({
  url: 'crm.api.tracking.get_snippet',
  auto: true,
})

const isDirty = computed(
  () => JSON.stringify(settings.doc) !== JSON.stringify(settings.originalDoc),
)

const stats = computed(() => {
  const s = snippet.data?.stats
  if (!s) return null
  return [
    { label: __('Visitors'), value: s.visitors },
    { label: __('Identified'), value: s.identified },
    { label: __('Sessions'), value: s.sessions },
    { label: __('Events'), value: s.events },
  ]
})

function copySnippet() {
  const text = snippet.data?.snippet
  if (!text) return
  // the shared helper, not navigator.clipboard directly: it falls back for a
  // page served over plain http, where the Clipboard API is not available
  copyToClipboard(text)
  capture('tracking_snippet_copied')
}

function updateSettings() {
  settings.save.submit(null, {
    onSuccess: () => {
      toast.success(__('Settings updated successfully'))
      snippet.reload()
    },
    onError: (error) =>
      toast.error(error?.messages?.[0] || __('Failed to save settings')),
  })
}
</script>
