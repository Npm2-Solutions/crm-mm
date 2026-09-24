<template>
  <div
    class="flex h-full flex-col gap-6 px-4 py-6 sm:px-6 sm:py-8 text-ink-gray-8"
  >
    <div
      class="flex flex-col items-start gap-3 px-2 sm:flex-row sm:items-center sm:justify-between"
    >
      <div class="flex flex-col gap-1">
        <h2 class="flex gap-2 text-2xl-semibold leading-none h-5">
          {{ __('Booking platforms') }}
        </h2>
        <p class="text-p-base text-ink-gray-6">
          {{
            __(
              'Bookings taken on MioDottore, Treatwell, Fresha, Calendly… land on your calendar, and your calendar blocks their slots.',
            )
          }}
        </p>
      </div>
      <Button
        variant="solid"
        :label="__('Connect a platform')"
        iconLeft="plus"
        @click="showPicker = true"
      />
    </div>

    <div class="flex-1 overflow-y-auto px-2">
      <div
        v-if="connections.data?.length"
        class="divide-y divide-outline-gray-1 rounded-lg border border-outline-gray-2"
      >
        <div
          v-for="conn in connections.data"
          :key="conn.name"
          class="flex cursor-pointer items-center gap-3 px-3 py-2.5 hover:bg-surface-gray-1"
          @click="openEditor(conn.name)"
        >
          <span
            class="flex size-8 shrink-0 items-center justify-center rounded-md bg-surface-gray-2 text-p-sm-medium text-ink-gray-7"
          >
            {{ initials(conn.platform) }}
          </span>
          <div class="min-w-0 flex-1">
            <div class="truncate text-p-base-medium text-ink-gray-8">
              {{ conn.connection_name }}
            </div>
            <div class="truncate text-p-sm text-ink-gray-5">
              {{ conn.platform }}
              <span v-if="conn.last_sync || conn.last_webhook">
                · {{ __('last activity') }}
                {{ timeAgo(latest(conn.last_sync, conn.last_webhook)) }}
              </span>
              <span v-if="conn.status === 'Error' && conn.last_error">
                · {{ conn.last_error }}
              </span>
            </div>
          </div>
          <span class="shrink-0 text-p-sm text-ink-gray-5">
            {{ conn.upcoming }} {{ __('upcoming') }}
          </span>
          <Badge
            v-if="conn.platform_info?.stability === 'beta'"
            :label="__('Beta')"
            theme="gray"
            size="sm"
          />
          <Badge
            :label="statusLabel(conn)"
            :theme="statusTheme(conn)"
            size="sm"
          />
          <Button
            v-if="conn.platform_info?.capabilities?.includes('pull')"
            variant="ghost"
            icon="lucide-refresh-cw"
            :tooltip="__('Sync now')"
            :loading="syncing === conn.name"
            @click.stop="syncNow(conn.name)"
          />
          <Button
            variant="ghost"
            icon="lucide-trash-2"
            @click.stop="remove(conn)"
          />
        </div>
      </div>
      <div
        v-else-if="!connections.loading"
        class="flex flex-col items-start gap-2 px-2 text-p-base text-ink-gray-5"
      >
        {{
          __(
            'No platform connected yet. Connect the ones where your clients already book.',
          )
        }}
      </div>
    </div>
  </div>

  <!-- platform picker -->
  <Dialog
    v-model="showPicker"
    :options="{ title: __('Connect a platform'), size: '4xl' }"
  >
    <template #body-content>
      <div class="flex flex-col gap-5">
        <FormControl
          v-model="pickerQuery"
          type="text"
          :placeholder="__('Search a platform…')"
        />
        <div v-for="group in pickerGroups" :key="group.sector">
          <div class="mb-2 text-p-sm-medium uppercase text-ink-gray-5">
            {{ sectorLabel(group.sector) }}
          </div>
          <div class="grid grid-cols-3 gap-2">
            <button
              v-for="platform in group.platforms"
              :key="platform.key"
              class="flex flex-col items-start gap-1.5 rounded-lg border border-outline-gray-2 p-3 text-left hover:border-outline-gray-4 hover:bg-surface-gray-1"
              @click="startNew(platform)"
            >
              <div class="flex w-full items-center justify-between gap-2">
                <span class="text-p-base-medium text-ink-gray-8">
                  {{ platform.label }}
                </span>
                <div class="flex gap-1">
                  <Badge
                    v-if="platform.stability !== 'stable'"
                    :label="__('Beta')"
                    theme="gray"
                    size="sm"
                  />
                  <Badge
                    v-if="platform.api_access === 'partner'"
                    :label="__('partner')"
                    theme="orange"
                    size="sm"
                  />
                </div>
              </div>
              <div class="flex flex-wrap gap-1">
                <span
                  v-for="chip in capabilityChips(platform)"
                  :key="chip"
                  class="rounded bg-surface-gray-2 px-1.5 py-0.5 text-p-xs text-ink-gray-6"
                >
                  {{ chipLabel(chip) }}
                </span>
              </div>
            </button>
          </div>
        </div>
      </div>
    </template>
  </Dialog>

  <!-- editor -->
  <Dialog v-model="showEditor" :options="{ title: editorTitle, size: '4xl' }">
    <template #body-content>
      <div v-if="info" class="flex flex-col gap-4">
        <div
          v-if="info.stability !== 'stable'"
          class="rounded-lg bg-surface-amber-1 px-3 py-2 text-p-sm text-ink-amber-8"
        >
          {{
            __(
              'Beta: built from the official documentation but not yet proven on a real account. Visible to administrators only — the team sees it once it is verified.',
            )
          }}
        </div>
        <div
          class="rounded-lg bg-surface-gray-1 px-3 py-2 text-p-sm text-ink-gray-7"
        >
          <div class="whitespace-pre-line">{{ __(info.setup_help) }}</div>
          <a
            v-if="info.docs_url"
            :href="info.docs_url"
            target="_blank"
            rel="noopener"
            class="mt-1 inline-block text-ink-blue-link underline"
          >
            {{ __('Platform documentation') }}
          </a>
        </div>

        <div class="grid grid-cols-3 items-end gap-3">
          <FormControl
            v-model="form.connection_name"
            type="text"
            :label="__('Name')"
            class="col-span-2"
            required
          />
          <label class="flex h-7 items-center gap-2 text-sm text-ink-gray-7">
            <Switch v-model="form.enabled" size="sm" /> {{ __('Enabled') }}
          </label>
        </div>

        <!-- credentials -->
        <div
          v-if="fields.length"
          class="grid grid-cols-2 gap-3 rounded-lg border border-outline-gray-2 p-3"
        >
          <template v-for="field in fields" :key="field">
            <div v-if="field === 'inbound_email_account'">
              <div class="mb-1.5 text-xs text-ink-gray-5">
                {{ fieldLabel(field) }}
              </div>
              <Link
                doctype="Email Account"
                :modelValue="form.inbound_email_account"
                @update:modelValue="(v) => (form.inbound_email_account = v)"
              />
            </div>
            <FormControl
              v-else-if="field === 'field_map'"
              v-model="form.field_map"
              class="col-span-2"
              type="textarea"
              :rows="4"
              :label="fieldLabel(field)"
              :placeholder="fieldMapExample"
            />
            <FormControl
              v-else-if="field === 'ical_url'"
              v-model="form.ical_url"
              class="col-span-2"
              type="text"
              :label="fieldLabel(field)"
              placeholder="https://…/calendar.ics"
            />
            <FormControl
              v-else-if="SECRETS.includes(field)"
              v-model="form[field]"
              type="password"
              :label="fieldLabel(field) + (isRequired(field) ? ' *' : '')"
              :placeholder="
                hasSecret[field] ? __('Saved — type to replace') : ''
              "
            />
            <FormControl
              v-else
              v-model="form[field]"
              type="text"
              :label="fieldLabel(field) + (isRequired(field) ? ' *' : '')"
            />
          </template>
        </div>

        <!-- addresses the platform needs -->
        <div v-if="editingName" class="flex flex-col gap-2">
          <CopyRow
            v-if="usesWebhook"
            :label="__('Webhook address (give it to the platform)')"
            :value="details.webhook_url"
          />
          <CopyRow
            v-if="info.capabilities.includes('block') || usesEmail"
            :label="__('Busy feed of the whole team (.ics)')"
            :value="details.busy_feed_url"
          />
        </div>

        <!-- sync options -->
        <div class="grid grid-cols-4 gap-3">
          <FormControl
            v-model.number="form.sync_window_days"
            type="number"
            min="1"
            :label="__('Days ahead')"
          />
          <FormControl
            v-model.number="form.lookback_days"
            type="number"
            min="0"
            :label="__('Days back')"
          />
          <FormControl
            v-model="form.imported_status"
            type="select"
            :label="__('Imported as')"
            :options="[
              { label: __('Confirmed'), value: 'Confirmed' },
              { label: __('To confirm'), value: 'Scheduled' },
            ]"
          />
          <div>
            <div class="mb-1.5 text-xs text-ink-gray-5">
              {{ __('Default service') }}
            </div>
            <Link
              doctype="CRM Service"
              :modelValue="form.default_service"
              @update:modelValue="(v) => (form.default_service = v)"
            />
          </div>
        </div>
        <div class="flex flex-wrap gap-4">
          <label class="flex items-center gap-2 text-sm text-ink-gray-7">
            <Switch v-model="form.import_bookings" size="sm" />
            {{ __('Import bookings') }}
          </label>
          <label class="flex items-center gap-2 text-sm text-ink-gray-7">
            <Switch v-model="form.create_leads" size="sm" />
            {{ __('Link clients as leads') }}
          </label>
          <label
            v-if="
              info.capabilities.includes('block') ||
              info.capabilities.includes('busy_feed')
            "
            class="flex items-center gap-2 text-sm text-ink-gray-7"
          >
            <Switch v-model="form.push_blocks" size="sm" />
            {{ __('Block CRM appointments on the platform') }}
          </label>
          <label
            v-if="info.capabilities.includes('cancel')"
            class="flex items-center gap-2 text-sm text-ink-gray-7"
          >
            <Switch v-model="form.push_cancellations" size="sm" />
            {{ __('Cancel on the platform too') }}
          </label>
        </div>

        <!-- mapping -->
        <div class="rounded-lg border border-outline-gray-2 p-3">
          <div class="mb-2 flex items-center justify-between">
            <div class="flex flex-col">
              <span class="text-p-base-medium text-ink-gray-8">
                {{ __('Mapping') }}
              </span>
              <span class="text-p-sm text-ink-gray-5">
                {{
                  __(
                    'Which CRM service and professional each platform service and staff member is. Unmapped services use the default; same-named services match on their own.',
                  )
                }}
              </span>
            </div>
            <Button
              v-if="editingName && info.capabilities.includes('catalog')"
              size="sm"
              :label="__('Load from platform')"
              iconLeft="download"
              :loading="loadingCatalog"
              @click="loadCatalog"
            />
          </div>
          <div class="flex flex-col gap-2">
            <div
              v-for="(row, i) in form.mappings"
              :key="i"
              class="grid grid-cols-[110px_1fr_1fr_1.3fr_32px_32px] items-center gap-2"
            >
              <FormControl
                v-model="row.map_type"
                type="select"
                :options="[
                  { label: __('Service'), value: 'Service' },
                  { label: __('Staff'), value: 'Staff' },
                  { label: __('Room'), value: 'Resource' },
                ]"
              />
              <FormControl
                v-model="row.external_id"
                type="text"
                :placeholder="__('Platform ID')"
              />
              <FormControl
                v-model="row.external_name"
                type="text"
                :placeholder="__('Name on the platform')"
              />
              <Link
                :doctype="TARGET[row.map_type].doctype"
                :modelValue="row[TARGET[row.map_type].field]"
                :placeholder="__('In the CRM')"
                @update:modelValue="
                  (v) => (row[TARGET[row.map_type].field] = v)
                "
              />
              <Button
                v-if="row.busy_feed_url"
                variant="ghost"
                icon="lucide-calendar-x"
                :tooltip="__('Copy this professional\'s busy feed')"
                @click="copy(row.busy_feed_url)"
              />
              <span v-else />
              <Button
                variant="ghost"
                icon="lucide-trash-2"
                @click="form.mappings.splice(i, 1)"
              />
            </div>
            <Button
              variant="ghost"
              size="sm"
              class="self-start"
              iconLeft="plus"
              :label="__('Add mapping')"
              @click="
                form.mappings.push({
                  map_type: 'Service',
                  external_id: '',
                  external_name: '',
                })
              "
            />
          </div>
        </div>

        <!-- recent imports -->
        <div v-if="details.recent?.length" class="flex flex-col gap-1">
          <div class="text-p-sm-medium text-ink-gray-6">
            {{ __('Latest bookings from this platform') }}
          </div>
          <div
            v-for="row in details.recent"
            :key="row.name"
            class="flex items-center gap-2 text-p-sm text-ink-gray-7"
          >
            <span class="w-32 shrink-0 text-ink-gray-5">
              {{ formatDate(row.starts_on) }}
            </span>
            <span class="truncate">{{ row.title }}</span>
            <Badge :label="__(row.status)" size="sm" />
            <Badge
              v-if="row.conflict_note"
              :label="__('clash')"
              theme="red"
              size="sm"
            />
          </div>
        </div>

        <div
          v-if="testResult"
          class="rounded px-3 py-2 text-p-sm"
          :class="
            testResult.ok
              ? 'bg-surface-green-1 text-ink-green-8'
              : 'bg-surface-red-1 text-ink-red-8'
          "
        >
          {{ testResult.message }}
        </div>
      </div>
    </template>
    <template #actions>
      <div class="flex gap-2">
        <Button
          v-if="editingName"
          :label="__('Test connection')"
          :loading="testing"
          @click="test"
        />
        <Button
          class="flex-1"
          variant="solid"
          :label="__('Save')"
          :loading="saving"
          @click="save"
        />
      </div>
    </template>
  </Dialog>
</template>

<script setup>
import Link from '@/components/Controls/Link.vue'
import CopyRow from '@/components/Settings/Booking/CopyRow.vue'
import {
  capabilityChips,
  connectionFields,
  groupPlatforms,
} from '@/utils/onlineBooking'
import { formatDate, timeAgo } from '@/utils'
import {
  call,
  createResource,
  Dialog,
  FormControl,
  Switch,
  toast,
} from 'frappe-ui'
import { computed, reactive, ref } from 'vue'

const SECRETS = ['client_secret', 'api_key', 'refresh_token', 'webhook_secret']
const TARGET = {
  Service: { doctype: 'CRM Service', field: 'service' },
  Staff: { doctype: 'User', field: 'staff' },
  Resource: { doctype: 'CRM Resource', field: 'resource' },
}
const fieldMapExample =
  '{"id": "booking.id", "start": "booking.start", "end": "booking.end", "status": "booking.status", "customer_name": "client.name", "email": "client.email"}'

const connections = createResource({
  url: 'crm.api.booking_platforms.list_connections',
  auto: true,
})
const platforms = createResource({
  url: 'crm.api.booking_platforms.list_platforms',
  cache: 'crm-booking-platforms',
  auto: true,
})

// -- list ---------------------------------------------------------------------

function initials(label) {
  return (label || '?')
    .replace(/[^\p{L}\p{N} ]/gu, ' ')
    .split(/\s+/)
    .filter(Boolean)
    .map((w) => w[0])
    .slice(0, 2)
    .join('')
    .toUpperCase()
}

function latest(a, b) {
  if (!a) return b
  if (!b) return a
  return a > b ? a : b
}

function statusLabel(conn) {
  if (!conn.enabled) return __('Off')
  return (
    {
      Connected: __('Connected'),
      Error: __('Error'),
      'Not configured': __('To configure'),
    }[conn.status] || conn.status
  )
}

function statusTheme(conn) {
  if (!conn.enabled) return 'gray'
  return { Connected: 'green', Error: 'red' }[conn.status] || 'orange'
}

const syncing = ref(null)

async function syncNow(name) {
  syncing.value = name
  try {
    const result = await call('crm.api.booking_platforms.sync_now', { name })
    if (result?.error) toast.error(result.error)
    else if (result?.skipped)
      toast.warning(__('Nothing to sync for this connection'))
    else
      toast.success(
        __('{0} new, {1} updated, {2} cancelled', [
          result.created || 0,
          result.updated || 0,
          result.cancelled || 0,
        ]),
      )
  } catch (error) {
    toast.error(error.messages?.[0] || __('Sync failed'))
  }
  syncing.value = null
  connections.reload()
}

async function remove(conn) {
  try {
    await call('crm.api.booking_platforms.delete_connection', {
      name: conn.name,
    })
    connections.reload()
  } catch (error) {
    toast.error(error.messages?.[0] || __('Failed to delete'))
  }
}

async function copy(value) {
  try {
    await navigator.clipboard.writeText(value)
    toast.success(__('Copied'))
  } catch {
    toast.error(value)
  }
}

// -- picker ----------------------------------------------------------------------

const showPicker = ref(false)
const pickerQuery = ref('')
const pickerGroups = computed(() => {
  const q = pickerQuery.value.trim().toLowerCase()
  return groupPlatforms(
    (platforms.data || []).filter(
      (p) => !q || p.label.toLowerCase().includes(q),
    ),
  )
})

function sectorLabel(sector) {
  return (
    {
      medical: __('Medical'),
      beauty: __('Beauty & wellness'),
      wellness: __('Wellness & fitness'),
      general: __('General schedulers and universal connectors'),
    }[sector] || sector
  )
}

function chipLabel(chip) {
  return (
    {
      api: __('API'),
      webhook: __('real time'),
      ical: __('iCal'),
      email: __('email'),
      cancel: __('cancels'),
      block: __('blocks slots'),
    }[chip] || chip
  )
}

// -- editor ------------------------------------------------------------------------

const showEditor = ref(false)
const editingName = ref(null)
const saving = ref(false)
const testing = ref(false)
const loadingCatalog = ref(false)
const testResult = ref(null)
const details = reactive({})
const hasSecret = reactive({})

const emptyForm = () => ({
  connection_name: '',
  platform: '',
  enabled: true,
  api_base_url: '',
  account_id: '',
  client_id: '',
  tenant_id: '',
  extra_param: '',
  client_secret: '',
  api_key: '',
  refresh_token: '',
  webhook_secret: '',
  ical_url: '',
  inbound_email_account: '',
  sender_filter: '',
  field_map: '',
  import_bookings: true,
  sync_window_days: 60,
  lookback_days: 1,
  push_blocks: false,
  push_cancellations: false,
  create_leads: true,
  imported_status: 'Confirmed',
  default_service: '',
  default_staff: '',
  mappings: [],
})
const form = reactive(emptyForm())

const info = computed(
  () =>
    details.platform_info ||
    (platforms.data || []).find((p) => p.label === form.platform),
)
const fields = computed(() => connectionFields(info.value))
const usesWebhook = computed(() =>
  info.value?.capabilities?.includes('webhook'),
)
const usesEmail = computed(() => info.value?.capabilities?.includes('email'))
const editorTitle = computed(() => form.platform || __('Booking platform'))

function isRequired(field) {
  return (info.value?.required_fields || []).includes(field)
}

function fieldLabel(field) {
  return (
    {
      api_base_url: __('API base URL'),
      account_id: __('Account / business ID'),
      client_id: __('Client ID / username'),
      client_secret: __('Client secret / password'),
      api_key: __('API key / token'),
      refresh_token: __('Refresh token'),
      tenant_id: __('Tenant / country'),
      extra_param: __('Additional parameter'),
      webhook_secret: __('Webhook signing secret'),
      ical_url: __('Calendar feed address (.ics)'),
      inbound_email_account: __('Mailbox receiving the notifications'),
      sender_filter: __('Sender domains (optional)'),
      field_map: __('Payload field map (JSON, optional)'),
    }[field] || field
  )
}

function reset() {
  Object.assign(form, emptyForm())
  for (const key of Object.keys(details)) delete details[key]
  for (const key of Object.keys(hasSecret)) delete hasSecret[key]
  testResult.value = null
}

function startNew(platform) {
  reset()
  editingName.value = null
  form.platform = platform.label
  form.connection_name = platform.label
  showPicker.value = false
  showEditor.value = true
}

async function openEditor(name) {
  reset()
  editingName.value = name
  try {
    load(await call('crm.api.booking_platforms.get_connection', { name }))
    showEditor.value = true
  } catch (error) {
    toast.error(error.messages?.[0] || __('Failed to load'))
  }
}

function load(data) {
  Object.assign(details, data)
  Object.assign(hasSecret, data.has_secret || {})
  const next = emptyForm()
  for (const key of Object.keys(next)) {
    if (key in data && !SECRETS.includes(key))
      next[key] = data[key] ?? next[key]
  }
  for (const key of [
    'enabled',
    'import_bookings',
    'push_blocks',
    'push_cancellations',
    'create_leads',
  ]) {
    next[key] = Boolean(data[key])
  }
  next.mappings = (data.mappings || []).map((row) => ({ ...row }))
  Object.assign(form, next)
}

async function save() {
  saving.value = true
  try {
    const data = await call('crm.api.booking_platforms.save_connection', {
      name: editingName.value,
      connection: { ...form },
    })
    const isNew = !editingName.value
    editingName.value = data.name
    load(data)
    toast.success(__('Saved'))
    connections.reload()
    // a new connection shows its webhook/feed addresses only once saved: stay open
    if (!isNew) showEditor.value = false
  } catch (error) {
    toast.error(error.messages?.[0] || __('Failed to save'))
  }
  saving.value = false
}

async function test() {
  testing.value = true
  try {
    testResult.value = await call('crm.api.booking_platforms.test_connection', {
      name: editingName.value,
    })
  } catch (error) {
    testResult.value = {
      ok: false,
      message: error.messages?.[0] || __('Test failed'),
    }
  }
  testing.value = false
  connections.reload()
}

async function loadCatalog() {
  loadingCatalog.value = true
  try {
    const items = await call('crm.api.booking_platforms.fetch_catalog', {
      name: editingName.value,
    })
    const known = new Set(
      form.mappings.map((row) => `${row.map_type}:${row.external_id}`),
    )
    let added = 0
    for (const item of items || []) {
      if (known.has(`${item.kind}:${item.id}`)) continue
      form.mappings.push({
        map_type: item.kind,
        external_id: item.id,
        external_name: item.name,
      })
      added++
    }
    toast.success(__('{0} items added: pick their CRM match', [added]))
  } catch (error) {
    toast.error(error.messages?.[0] || __('Could not read the platform'))
  }
  loadingCatalog.value = false
}
</script>
