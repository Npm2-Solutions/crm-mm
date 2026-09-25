<!--
  Lead Ads: the forms on the Pages switched on in Connection, and where their
  answers land in the CRM.

  Which Pages bring leads is decided on the Connection tab — this one used to
  have a switch of its own for the same thing, so the two could be read as two
  different settings. What stays here is about forms: mapping them, importing
  what came before, and the submissions that never became a lead.
-->
<template>
  <div class="flex flex-col gap-4 px-2">
    <div
      v-if="status.data && !connected"
      class="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between rounded-lg border border-dashed border-outline-gray-2 p-6"
    >
      <span class="text-p-base text-ink-gray-5">
        {{
          __(
            'Connect your Facebook account first, then the forms of your Pages appear here.',
          )
        }}
      </span>
      <Button
        :label="__('Go to connection')"
        @click="emit('navigate', 'connection')"
      />
    </div>

    <template v-else-if="connected">
      <!-- the leads that asked to be contacted and never reached anybody -->
      <div
        v-if="failureCount"
        class="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between rounded-lg border border-outline-amber-2 bg-surface-amber-1 p-4"
      >
        <div class="flex min-w-0 flex-col">
          <span class="text-p-base-medium text-ink-gray-8">
            {{ __('{0} leads could not be imported', [failureCount]) }}
          </span>
          <span class="text-p-sm text-ink-gray-6">
            {{
              __(
                'They reached the CRM and stopped there. Trying again is safe: a lead already imported is not imported twice.',
              )
            }}
          </span>
        </div>
        <Button
          variant="solid"
          :label="__('Try again')"
          :loading="retrying"
          @click="retryAll"
        />
      </div>

      <div class="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <span class="text-p-sm text-ink-gray-5">
          {{
            __(
              'The Pages switched on in Connection, and how their form answers map to CRM fields.',
            )
          }}
        </span>
        <Button
          variant="ghost"
          :label="__('Choose Pages')"
          @click="emit('navigate', 'connection')"
        />
      </div>

      <div v-if="pages.data?.length" class="flex flex-col gap-3">
        <div
          v-for="page in pages.data"
          :key="page.name"
          class="rounded-lg border border-outline-gray-2 p-4"
        >
          <div class="flex items-start justify-between gap-3">
            <div class="min-w-0">
              <div class="flex flex-wrap items-center gap-2">
                <span class="truncate text-p-base-medium text-ink-gray-8">
                  {{ page.page_name }}
                </span>
                <Badge
                  v-if="page.webhook_subscribed"
                  :label="__('Real-time')"
                  theme="green"
                  size="sm"
                />
                <Badge
                  v-if="!page.granted"
                  :label="__('Not granted')"
                  theme="red"
                  size="sm"
                />
                <Badge
                  v-else-if="!page.token_valid"
                  :label="__('Token expired')"
                  theme="red"
                  size="sm"
                />
              </div>
              <div class="text-p-sm text-ink-gray-5">
                {{
                  [
                    page.category,
                    __('{0} forms', [page.forms.length]),
                    page.last_webhook_at &&
                      __('last lead {0}', [timeAgo(page.last_webhook_at)]),
                  ]
                    .filter(Boolean)
                    .join(' · ')
                }}
              </div>
              <!--
                The Page is still here because somebody switched it on or it
                has leads, but the last login did not include it: every call on
                it fails with "no page token", and reconnecting does not help
                unless the dialog actually offers it.
              -->
              <div v-if="!page.granted" class="mt-1 text-p-sm text-ink-red-5">
                {{
                  __(
                    'Facebook did not include this Page in the last connection, so nothing works on it. Reconnect and tick it in the dialog — if it is not offered there, its owner has to give you a role on the Page first.',
                  )
                }}
              </div>
              <!-- a page can be connected while its forms fail on their own:
                   say so instead of just showing zero forms -->
              <div
                v-if="page.last_form_sync_error"
                class="mt-1 text-p-sm text-ink-red-5"
              >
                {{ __('Meta refused the forms') }}:
                {{ page.last_form_sync_error }}
              </div>
              <div
                v-else-if="!page.forms.length"
                class="mt-1 text-p-sm text-ink-gray-5"
              >
                {{
                  __(
                    'No forms on this Page. If it has some, press "Read forms".',
                  )
                }}
              </div>
            </div>
            <Button
              size="sm"
              class="shrink-0"
              :label="__('Read forms')"
              :loading="syncingForms === page.name"
              @click="readForms(page)"
            />
          </div>

          <div
            v-if="page.forms.length"
            class="mt-3 divide-y divide-outline-gray-1 border-t border-outline-gray-1"
          >
            <div
              v-for="form in page.forms"
              :key="form.name"
              class="flex items-center justify-between gap-3 py-1.5"
            >
              <div class="flex min-w-0 items-center gap-2">
                <span class="truncate text-p-base text-ink-gray-7">{{
                  form.form_name
                }}</span>
                <span class="shrink-0 text-p-sm text-ink-gray-4">
                  {{ __('{0} leads', [form.lead_count]) }}
                  <template v-if="form.form_status">
                    · {{ form.form_status }}</template
                  >
                </span>
                <Badge
                  v-if="form.unmapped_questions"
                  :label="__('{0} to map', [form.unmapped_questions])"
                  theme="orange"
                  size="sm"
                />
              </div>
              <div class="flex shrink-0 items-center gap-1">
                <Button
                  :label="__('Map fields')"
                  size="sm"
                  @click="openMapping(form.name)"
                />
                <Dropdown placement="right" :options="formActions(form)">
                  <Button
                    icon="more-horizontal"
                    size="sm"
                    variant="ghost"
                    :aria-label="__('More')"
                  />
                </Dropdown>
              </div>
            </div>
          </div>
        </div>
      </div>
      <div
        v-else-if="pagesError"
        class="flex flex-col gap-1 rounded-lg border border-outline-gray-2 p-4 text-p-base"
      >
        <span class="text-ink-red-5">{{
          __('The pages could not be read.')
        }}</span>
        <span class="text-p-sm text-ink-gray-5">{{ pagesError }}</span>
      </div>
      <div
        v-else-if="syncing"
        class="flex items-center gap-2 rounded-lg border border-outline-gray-2 p-4 text-p-base text-ink-gray-6"
      >
        <LoadingIndicator class="size-4" />
        {{ __('Reading your Pages from Facebook…') }}
      </div>
      <div
        v-else
        class="rounded-lg border border-dashed border-outline-gray-2 p-6 text-p-base text-ink-gray-5"
      >
        {{
          __(
            'No Page is switched on yet. Choose which ones bring their leads to the CRM on the Connection tab, and their forms appear here.',
          )
        }}
      </div>

      <details class="rounded-lg border border-outline-gray-2 p-4">
        <summary class="cursor-pointer text-p-base-medium text-ink-gray-7">
          {{ __('Leads not arriving?') }}
        </summary>
        <div class="mt-2 flex flex-col gap-1 text-p-sm text-ink-gray-6">
          <p>
            {{
              __(
                'In Meta Business Settings → Integrations → Leads Access the business may restrict who can read its leads: assign this CRM there.',
              )
            }}
          </p>
          <p>
            {{
              __(
                'The person who connected Facebook also needs the Advertise role on each Page.',
              )
            }}
          </p>
        </div>
      </details>

      <!-- what Meta sent and what went wrong, raw: for whoever can read it -->
      <details
        v-if="isAdmin"
        class="group rounded-lg border border-outline-gray-2 p-4"
      >
        <summary
          class="flex cursor-pointer list-none items-center justify-between gap-2 text-p-base-medium text-ink-gray-7"
        >
          <span class="flex items-center gap-1.5">
            <FeatherIcon
              name="chevron-right"
              class="size-4 transition-transform group-open:rotate-90"
            />
            {{ __('Technical details') }}
          </span>
          <Badge :label="__('Administrators only')" theme="gray" size="sm" />
        </summary>
        <div class="mt-3 flex flex-col gap-3">
          <div v-if="failures.data?.length" class="flex flex-col gap-2">
            <div
              v-for="log in failures.data"
              :key="log.name"
              class="rounded bg-surface-gray-1 p-2 text-p-sm text-ink-gray-6"
            >
              <div class="font-medium">{{ log.creation }}</div>
              <div class="truncate font-mono text-p-xs">
                {{ log.lead_data }}
              </div>
            </div>
          </div>
          <div v-else class="text-p-sm text-ink-gray-5">
            {{ __('No failed import.') }}
          </div>
          <div class="flex gap-2">
            <Button
              variant="ghost"
              :label="__('Reload')"
              @click="failures.reload()"
            />
            <!--
              "Real-time" only ever meant "our subscribe call answered success
              once". This asks Meta who is installed on each Page right now.
            -->
            <Button
              variant="ghost"
              :label="__('Check webhook')"
              :loading="verifying"
              @click="verifyWebhook"
            />
          </div>
        </div>
      </details>
    </template>

    <Dialog
      v-model="showMapping"
      :options="{ title: mappingTitle, size: 'xl' }"
    >
      <template #body-content>
        <div class="flex flex-col gap-2">
          <div class="mb-1 text-p-sm text-ink-gray-5">
            {{
              __(
                'Map every form question to a CRM Lead field. First name is required.',
              )
            }}
            {{
              __(
                'Answers you leave unmapped are not lost: they are saved as a note on the lead.',
              )
            }}
          </div>
          <div
            v-for="q in mappingQuestions"
            :key="q.key"
            class="grid grid-cols-1 sm:grid-cols-2 items-center gap-3"
          >
            <div class="min-w-0">
              <div class="flex items-center gap-2">
                <span class="truncate text-p-base text-ink-gray-8">{{
                  q.label || q.key
                }}</span>
                <Badge
                  v-if="!q.mapped_to_crm_field"
                  :label="__('not mapped')"
                  theme="orange"
                  size="sm"
                />
              </div>
              <div class="text-p-sm text-ink-gray-4">{{ q.type }}</div>
            </div>
            <FormControl
              v-model="q.mapped_to_crm_field"
              type="select"
              :options="leadFieldOptions"
            />
          </div>
        </div>
      </template>
      <template #actions>
        <Button
          class="w-full"
          variant="solid"
          :label="__('Save mapping')"
          @click="saveMapping"
        />
      </template>
    </Dialog>
  </div>
</template>

<script setup>
import { timeAgo } from '@/utils'
import { createResource, Dropdown, LoadingIndicator, toast } from 'frappe-ui'
import { ref, computed, watch, onUnmounted } from 'vue'

// loaded once by the page around the tabs
const props = defineProps({
  status: { type: Object, required: true },
})

const emit = defineEmits(['navigate'])

const connected = computed(() => Boolean(props.status.data?.connected))
const isAdmin = computed(() => Boolean(props.status.data?.is_admin))

// a failing call used to look exactly like "you have no pages", which sent
// people back to reconnect instead of showing them what went wrong
const pagesError = ref('')
const pages = createResource({
  url: 'crm.integrations.meta.api.get_pages',
  auto: true,
  onSuccess: () => (pagesError.value = ''),
  onError: (e) =>
    (pagesError.value = e.messages?.[0] || e.message || __('Unknown error')),
})

const syncing = computed(() => Boolean(props.status.data?.syncing))
const syncingForms = ref('')

// only the failures; the payload itself comes along for administrators alone
const failures = createResource({
  url: 'crm.integrations.meta.api.get_failure_logs',
  auto: true,
})
const failureCount = computed(() => failures.data?.length || 0)

// the menu of a form: importing the past is anybody's, a test lead is a
// developer's tool and fires a real webhook
function formActions(form) {
  return [
    {
      label: __('Import the last 90 days'),
      icon: 'download',
      onClick: () => backfill(form.name),
    },
    ...(isAdmin.value
      ? [
          {
            label: __('Send a test lead'),
            icon: 'send',
            onClick: () => testLead(form.name),
          },
        ]
      : []),
  ]
}

const verifying = ref(false)
function verifyWebhook() {
  verifying.value = true
  createResource({
    url: 'crm.integrations.meta.api.verify_webhook_subscriptions',
    auto: true,
    onSuccess: (data) => {
      verifying.value = false
      const report = data.pages || []
      const missing = report.filter((p) => p.installed === false)
      const failed = report.filter((p) => p.installed === null)
      if (!report.length) {
        toast.info(__('No page is switched on.'))
      } else if (missing.length || failed.length) {
        toast.error(
          __('{0} of {1} pages do not have this app installed on Meta', [
            missing.length + failed.length,
            report.length,
          ]),
        )
      } else {
        toast.success(
          __('Meta confirms the app is installed on all {0} pages', [
            report.length,
          ]),
        )
      }
      pages.reload()
    },
    onError: (e) => {
      verifying.value = false
      toast.error(e.messages?.[0] || e.message || __('Unknown error'))
    },
  })
}

const retrying = ref(false)
function retryAll() {
  retrying.value = true
  createResource({
    url: 'crm.integrations.meta.api.retry_failed_leads',
    auto: true,
    onSuccess: (data) => {
      retrying.value = false
      toast.success(
        __('{0} imported, {1} merged, {2} already there, {3} still failing', [
          data.created || 0,
          data.merged || 0,
          data.duplicate || 0,
          data.failed || 0,
        ]),
      )
      failures.reload()
      pages.reload()
    },
    onError: (e) => {
      retrying.value = false
      toast.error(e.messages?.[0] || e.message || __('Unknown error'))
    },
  })
}

function readForms(page) {
  syncingForms.value = page.name
  createResource({
    url: 'crm.integrations.meta.api.sync_forms',
    params: { page_id: page.name },
    auto: true,
    onSuccess: (data) => {
      syncingForms.value = ''
      if (data.error) toast.error(data.error)
      else toast.success(__('{0} forms read', [data.forms]))
      pages.reload()
    },
    onError: (e) => {
      syncingForms.value = ''
      toast.error(e.messages?.[0] || __('Could not read the forms'))
    },
  })
}

// The sync runs in a background job, so the screen has to keep coming back for
// it. `watch` alone fires only when the flag CHANGES: after one reload with the
// job still running the value stayed true, nothing rescheduled, and the screen
// sat on "reading your Pages" until someone reloaded by hand.
let pollTimer = null
function pollWhileSyncing() {
  clearTimeout(pollTimer)
  if (!syncing.value) return
  pollTimer = setTimeout(() => {
    props.status.reload()
    pages.reload()
    pollWhileSyncing()
  }, 3000)
}
watch(syncing, pollWhileSyncing, { immediate: true })
onUnmounted(() => clearTimeout(pollTimer))

function testLead(formId) {
  createResource({
    url: 'crm.integrations.meta.api.create_test_lead',
    params: { form_id: formId },
    auto: true,
    onSuccess: () =>
      toast.success(
        __('Test lead created — it should arrive via webhook in moments'),
      ),
    onError: (e) =>
      toast.error(e.messages?.[0] || __('Failed to create test lead')),
  })
}

function backfill(formId) {
  createResource({
    url: 'crm.integrations.meta.api.backfill',
    params: { form_id: formId },
    auto: true,
    onSuccess: () =>
      toast.success(__('Import started — the leads will appear shortly')),
    onError: (e) =>
      toast.error(e.messages?.[0] || __('Failed to start the import')),
  })
}

// --- field mapping ---
const showMapping = ref(false)
const mappingFormId = ref(null)
const mappingTitle = ref('')
const mappingQuestions = ref([])
const leadFields = ref([])

const leadFieldOptions = computed(() => [
  { label: __('— not synced —'), value: '' },
  ...leadFields.value.map((f) => ({ label: f.label, value: f.fieldname })),
])

function openMapping(formId) {
  createResource({
    url: 'crm.integrations.meta.api.get_form_mapping',
    params: { form_id: formId },
    auto: true,
    onSuccess: (data) => {
      mappingFormId.value = data.name
      mappingTitle.value = data.form_name
      mappingQuestions.value = data.questions
      leadFields.value = data.lead_fields
      showMapping.value = true
    },
    onError: (e) => toast.error(e.messages?.[0] || __('Failed to load form')),
  })
}

function saveMapping() {
  const mapping = {}
  for (const q of mappingQuestions.value) {
    mapping[q.key] = q.mapped_to_crm_field || ''
  }
  createResource({
    url: 'crm.integrations.meta.api.save_form_mapping',
    params: { form_id: mappingFormId.value, mapping },
    auto: true,
    onSuccess: () => {
      showMapping.value = false
      toast.success(__('Mapping saved'))
      pages.reload()
    },
    onError: (e) =>
      toast.error(e.messages?.[0] || __('Failed to save mapping')),
  })
}
</script>
