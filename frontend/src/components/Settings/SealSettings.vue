<!--
  Copyright (c) 2026, NPM2 Solutions Srl and contributors
  For license information, please see license.txt

  The centre's seal and the time stamp: the agency installs the centre's
  certificate and the time-stamping authority; from then on the signed forms and
  the reports come out sealed, and stamped. A test page shows whether it works.
-->
<template>
  <SettingsLayoutBase>
    <template #title>
      <div class="flex items-center gap-2">
        <h2 class="text-2xl-semibold text-ink-gray-9">
          {{ __('Seal and time stamp') }}
        </h2>
        <Badge
          v-if="status.data"
          variant="subtle"
          :theme="status.data.enabled ? 'green' : 'gray'"
          :label="status.data.enabled ? __('Sealing') : __('Off')"
        />
      </div>
    </template>
    <template #header-actions>
      <div v-if="settings.doc" class="flex gap-2">
        <Button
          v-if="isDirty"
          :label="__('Discard Changes')"
          variant="subtle"
          @click="settings.reload()"
        />
        <Button
          variant="solid"
          :label="__('Update')"
          :loading="settings.save.loading"
          :disabled="!isDirty"
          @click="update"
        />
      </div>
    </template>
    <template #content>
      <div v-if="settings.doc" class="flex flex-col gap-2 pb-6">
        <div class="rounded-md bg-surface-gray-2 px-3 py-2">
          <p class="text-p-sm text-ink-gray-7">
            {{
              __(
                "With the centre's certificate, the signed forms and the visit reports come out sealed: whoever holds the file can check nothing changed since. With a time-stamping authority, they also carry the time they existed. Without them, the PDFs keep their SHA-256 fingerprint as today.",
              )
            }}
          </p>
        </div>

        <SettingRow
          :label="__('Seal the PDFs')"
          :description="
            __('A PAdES seal on the signed forms and on the visit reports.')
          "
        >
          <Switch v-model="settings.doc.seal_enabled" size="sm" />
        </SettingRow>

        <div class="grid grid-cols-2 gap-4 px-2 py-3 max-md:grid-cols-1">
          <div class="flex flex-col gap-1.5">
            <span class="text-xs text-ink-gray-5">
              {{ __('Certificate (.p12 or .pfx)') }}
            </span>
            <FileUploader
              :file-types="['.p12', '.pfx']"
              :upload-args="{
                doctype: 'CRM Signature Settings',
                docname: 'CRM Signature Settings',
                fieldname: 'seal_certificate',
                private: true,
              }"
              @success="
                (file) => (settings.doc.seal_certificate = file.file_url)
              "
            >
              <template #default="{ openFileSelector, uploading }">
                <div class="flex min-w-0 items-center gap-2">
                  <Button
                    :label="uploading ? __('Uploading…') : __('Upload')"
                    icon-left="upload"
                    @click="openFileSelector()"
                  />
                  <span class="min-w-0 truncate text-p-sm text-ink-gray-6">
                    {{
                      settings.doc.seal_certificate
                        ? settings.doc.seal_certificate.split('/').pop()
                        : __('None yet')
                    }}
                  </span>
                </div>
              </template>
            </FileUploader>
          </div>
          <Password
            v-model="settings.doc.seal_password"
            :label="__('Certificate password')"
            placeholder="************"
          />
          <FormControl
            v-model="settings.doc.seal_location"
            :label="__('Place')"
            :placeholder="__('The centre\'s city')"
          />
        </div>

        <div class="pb-1 pt-4 text-base-semibold text-ink-gray-9">
          {{ __('Time stamp') }}
        </div>
        <div class="grid grid-cols-2 gap-4 px-2 py-3 max-md:grid-cols-1">
          <FormControl
            type="url"
            v-model="settings.doc.tsa_url"
            :label="__('Authority address')"
            placeholder="https://"
            autocomplete="off"
          />
          <FormControl
            v-model="settings.doc.tsa_username"
            :label="__('User')"
            autocomplete="off"
          />
          <Password
            v-model="settings.doc.tsa_password"
            :label="__('Password')"
            placeholder="************"
          />
        </div>
        <ErrorMessage :message="settings.save?.error" />

        <div
          v-if="status.data?.subject || status.data?.error"
          class="mt-2 flex flex-col gap-1 rounded-md border border-outline-gray-2 px-3 py-2 text-p-sm"
        >
          <template v-if="status.data.subject">
            <span class="font-medium text-ink-gray-8">
              {{ __('Certificate of {0}', [status.data.subject]) }}
            </span>
            <span v-if="status.data.self_signed" class="text-ink-amber-8">
              {{
                __(
                  "Self-signed: good for a test, but a PDF reader will not recognise it. The centre's seal comes from a trust service provider.",
                )
              }}
            </span>
            <span v-else class="text-ink-gray-6">
              {{ __('Issued by {0}', [status.data.issuer]) }}
            </span>
            <span
              :class="
                !status.data.valid_now
                  ? 'text-ink-red-7'
                  : status.data.days_left < 30
                    ? 'text-ink-amber-8'
                    : 'text-ink-gray-6'
              "
            >
              {{
                !status.data.valid_now
                  ? __(
                      'Not valid today: the PDFs are not sealed until it is renewed',
                    )
                  : status.data.days_left < 30
                    ? __('Valid until {0}: renew it in time', [
                        formatDate(status.data.valid_until, 'D MMM YYYY'),
                      ])
                    : __('Valid until {0}', [
                        formatDate(status.data.valid_until, 'D MMM YYYY'),
                      ])
              }}
            </span>
          </template>
          <span v-if="status.data.error" class="text-ink-red-7">
            {{ status.data.error }}
          </span>
        </div>

        <div class="mt-2 flex flex-wrap items-center gap-3">
          <Button
            :label="__('Seal a test page')"
            :loading="trying"
            :disabled="!status.data?.enabled || isDirty"
            @click="tryIt"
          />
          <span v-if="tried" class="text-p-sm text-ink-gray-7">
            {{
              tried.sealed
                ? tried.timestamped
                  ? __('Sealed and time-stamped.')
                  : __('Sealed, without a time stamp.')
                : __('Not sealed.')
            }}
            {{ tried.notice || '' }}
          </span>
        </div>
      </div>
      <div v-else class="mt-[35%] flex items-center justify-center">
        <LoadingIndicator class="size-6" />
      </div>
    </template>
  </SettingsLayoutBase>
</template>

<script setup>
import SettingsLayoutBase from '@/components/Layouts/SettingsLayoutBase.vue'
import SettingRow from '@/components/Settings/Telephony/SettingRow.vue'
import { useDocument } from '@/data/document'
import { formatDate } from '@/utils'
import {
  Badge,
  Button,
  ErrorMessage,
  FileUploader,
  FormControl,
  LoadingIndicator,
  Password,
  Switch,
  call,
  createResource,
  toast,
} from 'frappe-ui'
import { computed, ref } from 'vue'

const { document: settings } = useDocument(
  'CRM Signature Settings',
  'CRM Signature Settings',
)
const status = createResource({
  url: 'crm.moduli.sigillo.get_seal_status',
  auto: true,
})

const isDirty = computed(
  () =>
    settings.doc &&
    settings.originalDoc &&
    JSON.stringify(settings.doc) !== JSON.stringify(settings.originalDoc),
)

function update() {
  settings.save.submit(null, {
    onSuccess: () => {
      settings.reload()
      status.reload()
      toast.success(__('Seal updated'))
    },
  })
}

const trying = ref(false)
const tried = ref(null)

async function tryIt() {
  trying.value = true
  try {
    tried.value = await call('crm.moduli.sigillo.try_seal')
  } catch (e) {
    toast.error(e.messages?.[0] || e.message)
  } finally {
    trying.value = false
  }
}
</script>
