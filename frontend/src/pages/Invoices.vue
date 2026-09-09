<template>
  <LayoutHeader>
    <template #left-header>
      <Breadcrumbs
        :items="[{ label: __('Invoices'), route: { name: 'Invoices' } }]"
      />
      <Dropdown v-if="companies.data?.length > 1" :options="companyOptions">
        <Button variant="ghost" iconRight="chevron-down">
          <span class="truncate">{{ company || __('All companies') }}</span>
        </Button>
      </Dropdown>
    </template>
    <template #right-header>
      <Button
        variant="ghost"
        :label="__('Register')"
        iconLeft="book-open"
        @click="openDesk('crm-professional-qualification')"
      />
      <Button
        variant="solid"
        :label="__('New invoice')"
        iconLeft="plus"
        @click="openDesk('crm-invoice/new')"
      />
    </template>
  </LayoutHeader>

  <div class="flex-1 overflow-y-auto px-3 py-4 sm:px-5">
    <div class="mx-auto flex w-full max-w-6xl flex-col gap-4">
      <!-- Nothing configured yet: say what to do, not that the list is empty. -->
      <div
        v-if="companies.fetched && !companies.data?.length"
        class="flex flex-col gap-3 rounded-xl border border-outline-gray-2 bg-surface-gray-1 px-5 py-4"
      >
        <span class="text-p-base-medium text-ink-gray-8">
          {{ __('No issuing company yet') }}
        </span>
        <span class="text-p-sm text-ink-gray-5">
          {{
            __(
              'An invoice needs somebody to issue it: VAT number, registered office, tax regime and a numbering format. Create the company once and the rest follows.',
            )
          }}
        </span>
        <div>
          <Button
            variant="solid"
            :label="__('Create the company')"
            @click="openDesk('crm-invoicing-company/new')"
          />
        </div>
      </div>

      <template v-else>
        <Tabs v-model="tab" :tabs="tabs" />

        <!-- ------------------------------------------------------- to do -->
        <div v-if="tab === 0" class="flex flex-col gap-3">
          <!-- A button not pressed produces no error: it produces absence, and
               absence is found in January. This list is what makes yesterday's
               absences visible today. -->
          <div
            v-if="!pending.loading && !pending.data?.length"
            class="rounded-xl border border-outline-gray-2 bg-surface-gray-1 px-5 py-4 text-p-sm text-ink-gray-5"
          >
            {{ __('Nothing waiting. Every issued document has been routed.') }}
          </div>
          <div
            v-for="row in pending.data || []"
            :key="row.action + row.name"
            class="flex items-center justify-between gap-3 rounded-xl border border-outline-gray-2 px-4 py-3"
          >
            <div class="flex min-w-0 flex-col">
              <span class="truncate text-p-base-medium text-ink-gray-8">
                {{ row.document_number }} · {{ row.billing_name }}
              </span>
              <span class="text-p-sm text-ink-gray-5">
                {{ row.label }} ·
                {{ dayjs(row.posting_date).format('DD/MM/YYYY') }}
              </span>
            </div>
            <div class="flex shrink-0 items-center gap-2">
              <Badge
                :theme="row.state.startsWith('scart') ? 'red' : 'orange'"
                :label="row.state"
              />
              <Button
                variant="subtle"
                :label="__('Open')"
                @click="openDesk('crm-invoice/' + row.name)"
              />
            </div>
          </div>
        </div>

        <!-- ---------------------------------------------------- invoices -->
        <div v-else-if="tab === 1" class="flex flex-col gap-2">
          <div
            v-for="row in invoices.data || []"
            :key="row.name"
            class="flex items-center justify-between gap-3 rounded-xl border border-outline-gray-2 px-4 py-3"
          >
            <div class="flex min-w-0 flex-col">
              <span class="truncate text-p-base-medium text-ink-gray-8">
                {{ row.document_number || __('Draft') }} ·
                {{ row.billing_name }}
              </span>
              <span class="text-p-sm text-ink-gray-5">
                {{ dayjs(row.posting_date).format('DD/MM/YYYY') }} ·
                {{ formatCurrency(row.grand_total) }}
                <template v-if="row.channel">
                  · {{ channelLabel(row.channel) }}
                </template>
              </span>
            </div>
            <div class="flex shrink-0 items-center gap-2">
              <Badge
                v-if="row.sdi_status && row.sdi_status !== 'non_applicabile'"
                :theme="statusTheme(row.sdi_status)"
                :label="'SdI: ' + row.sdi_status"
              />
              <Badge
                v-if="row.ts_status && row.ts_status !== 'non_applicabile'"
                :theme="statusTheme(row.ts_status)"
                :label="'TS: ' + row.ts_status"
              />
              <!-- The transmit action does not exist on a document that cannot
                   take that channel. A greyed-out button invites somebody to go
                   looking for how to turn it on. -->
              <Button
                v-if="row.channel === 'sdi' && row.docstatus === 1"
                variant="subtle"
                :loading="sending === row.name"
                :label="__('Transmit')"
                @click="transmit(row)"
              />
              <Button
                variant="ghost"
                icon="external-link"
                @click="openDesk('crm-invoice/' + row.name)"
              />
            </div>
          </div>
          <div
            v-if="invoices.fetched && !invoices.data?.length"
            class="rounded-xl border border-outline-gray-2 bg-surface-gray-1 px-5 py-4 text-p-sm text-ink-gray-5"
          >
            {{ __('No invoices yet.') }}
          </div>
        </div>

        <!-- -------------------------------------------------- sistema ts -->
        <div v-else class="flex flex-col gap-4">
          <div
            v-if="!healthcareCompany"
            class="rounded-xl border border-outline-gray-2 bg-surface-gray-1 px-5 py-4 text-p-sm text-ink-gray-5"
          >
            {{
              __(
                'This company does not report to the Sistema TS. That channel only carries healthcare expenses of natural persons.',
              )
            }}
          </div>
          <template v-else>
            <div
              class="flex flex-col gap-3 rounded-xl border border-outline-gray-2 px-5 py-4"
            >
              <div class="flex items-center justify-between gap-3">
                <span class="text-p-base-medium text-ink-gray-8">
                  {{ __('Year {0}', [year]) }}
                </span>
                <FormControl
                  type="select"
                  :modelValue="String(year)"
                  :options="yearOptions"
                  @update:modelValue="(v) => (year = Number(v))"
                />
              </div>
              <div
                v-if="tsStatus.data"
                class="grid grid-cols-2 gap-3 sm:grid-cols-4"
              >
                <div
                  v-for="(count, key) in tsStatus.data.counts"
                  :key="key"
                  class="rounded-lg bg-surface-gray-2 px-3 py-2"
                >
                  <div class="text-p-sm text-ink-gray-5">{{ key }}</div>
                  <div class="text-lg font-semibold text-ink-gray-8">
                    {{ count }}
                  </div>
                </div>
              </div>
              <div v-if="tsStatus.data" class="text-p-sm text-ink-gray-5">
                {{
                  __('Deadline {0}, {1} days left.', [
                    dayjs(tsStatus.data.deadline).format('DD/MM/YYYY'),
                    tsStatus.data.days_left,
                  ])
                }}
                {{
                  tsStatus.data.last_accepted
                    ? __('Last accepted submission: {0}.', [
                        dayjs(tsStatus.data.last_accepted).format('DD/MM/YYYY'),
                      ])
                    : __('Nothing has been accepted yet.')
                }}
              </div>
              <div>
                <Button
                  variant="solid"
                  :loading="preparing"
                  :label="__('Prepare the submission file')"
                  @click="prepareTs"
                />
              </div>
            </div>

            <div
              v-if="lastPrepared?.skipped?.length"
              class="flex flex-col gap-2 rounded-xl border border-outline-red-2 bg-surface-red-1 px-5 py-4"
            >
              <span class="text-p-base-medium text-ink-gray-8">
                {{
                  __('{0} documents were left out', [
                    lastPrepared.skipped.length,
                  ])
                }}
              </span>
              <!-- Left out, not blocking: one broken row must not cost the
                   deadline for the whole year. -->
              <div
                v-for="row in lastPrepared.skipped"
                :key="row.invoice"
                class="text-p-sm text-ink-gray-6"
              >
                <span class="font-medium">{{ row.number }}</span> —
                {{ row.errors.join('; ') }}
              </div>
            </div>

            <div class="flex flex-col gap-2">
              <div
                v-for="row in submissions.data || []"
                :key="row.name"
                class="flex items-center justify-between gap-3 rounded-xl border border-outline-gray-2 px-4 py-3"
              >
                <div class="flex min-w-0 flex-col">
                  <span class="truncate text-p-base-medium text-ink-gray-8">
                    {{ row.file_name }}
                  </span>
                  <span class="text-p-sm text-ink-gray-5">
                    {{
                      __('{0} documents · part {1} of {2}', [
                        row.document_count,
                        row.part,
                        row.total_parts,
                      ])
                    }}
                  </span>
                </div>
                <div class="flex shrink-0 items-center gap-2">
                  <Badge :theme="statusTheme(row.status)" :label="row.status" />
                  <Button
                    v-if="row.file"
                    variant="subtle"
                    :label="__('Download')"
                    @click="openExternal(row.file)"
                  />
                </div>
              </div>
            </div>
          </template>
        </div>
      </template>
    </div>
  </div>
</template>

<script setup>
import LayoutHeader from '@/components/LayoutHeader.vue'
import {
  createListResource,
  createResource,
  Badge,
  Breadcrumbs,
  Dropdown,
  FormControl,
  Tabs,
  call,
  dayjs,
  toast,
} from 'frappe-ui'
import { computed, ref, watch } from 'vue'

const tab = ref(0)
const company = ref('')
const year = ref(new Date().getFullYear())
const sending = ref('')
const preparing = ref(false)
const lastPrepared = ref(null)

const tabs = computed(() => [
  { label: __('To do') },
  { label: __('Invoices') },
  { label: __('Sistema TS') },
])

const companies = createListResource({
  doctype: 'CRM Invoicing Company',
  fields: ['name', 'company_name', 'sender_category', 'is_default'],
  filters: { enabled: 1 },
  pageLength: 50,
  auto: true,
  onSuccess(rows) {
    if (!company.value && rows.length) {
      company.value = (rows.find((r) => r.is_default) || rows[0]).name
    }
  },
})

const companyOptions = computed(() =>
  (companies.data || []).map((row) => ({
    label: row.company_name,
    onClick: () => (company.value = row.name),
  })),
)

const healthcareCompany = computed(() => {
  const row = (companies.data || []).find((r) => r.name === company.value)
  return row && row.sender_category && row.sender_category !== 'non_sanitario'
})

const yearOptions = computed(() => {
  const now = new Date().getFullYear()
  return [now, now - 1, now - 2].map((y) => ({
    label: String(y),
    value: String(y),
  }))
})

const invoices = createListResource({
  doctype: 'CRM Invoice',
  fields: [
    'name',
    'document_number',
    'posting_date',
    'billing_name',
    'grand_total',
    'channel',
    'sdi_status',
    'ts_status',
    'docstatus',
  ],
  orderBy: 'creation desc',
  pageLength: 50,
})

const pending = createResource({ url: 'crm.invoicing.api.pending_actions' })
const tsStatus = createResource({ url: 'crm.invoicing.api.ts_status' })
const submissions = createListResource({
  doctype: 'CRM TS Submission',
  fields: [
    'name',
    'file_name',
    'file',
    'status',
    'document_count',
    'part',
    'total_parts',
  ],
  orderBy: 'creation desc',
  pageLength: 20,
})

watch(
  [company, year, tab],
  () => {
    if (!company.value) return
    invoices.update({ filters: { company: company.value } })
    invoices.reload()
    pending.fetch({ company: company.value })
    if (healthcareCompany.value) {
      tsStatus.fetch({ company: company.value, year: year.value })
      submissions.update({
        filters: { company: company.value, fiscal_year: year.value },
      })
      submissions.reload()
    }
  },
  { immediate: true },
)

function channelLabel(channel) {
  return {
    sdi: __('Electronic invoice'),
    pdf_ts: __('PDF + Sistema TS'),
    pdf_solo: __('PDF only'),
  }[channel]
}

function statusTheme(status) {
  if (['accolto', 'consegnata', 'scaricato'].includes(status)) return 'green'
  if (['scartato', 'scartata', 'errore', 'mancata_consegna'].includes(status))
    return 'red'
  if (['inviato', 'pronto', 'pronto_export'].includes(status)) return 'blue'
  return 'orange'
}

function formatCurrency(value) {
  return new Intl.NumberFormat('it-IT', {
    style: 'currency',
    currency: 'EUR',
  }).format(value || 0)
}

function openDesk(route) {
  window.open(`/app/${route}`, '_blank')
}

function openExternal(url) {
  window.open(url, '_blank')
}

async function transmit(row) {
  sending.value = row.name
  try {
    const result = await call('crm.invoicing.api.send_to_sdi', {
      invoice: row.name,
    })
    if (result?.file) openExternal(result.file)
    toast.success(__('The file is ready to be transmitted'))
    invoices.reload()
  } catch (error) {
    // A 403 here is the guard, not a glitch: healthcare services towards a
    // natural person have been barred from the SdI since 2026, and the message
    // says which lines and why.
    toast.error(stripHtml(error.messages?.[0] || error.message))
  } finally {
    sending.value = ''
  }
}

async function prepareTs() {
  preparing.value = true
  try {
    lastPrepared.value = await call('crm.invoicing.api.prepare_ts_submission', {
      company: company.value,
      year: year.value,
    })
    toast.success(
      __('{0} documents packaged', [lastPrepared.value?.count || 0]),
    )
    submissions.reload()
    tsStatus.fetch({ company: company.value, year: year.value })
  } catch (error) {
    toast.error(stripHtml(error.messages?.[0] || error.message))
  } finally {
    preparing.value = false
  }
}

function stripHtml(text) {
  return String(text || '')
    .replace(/<br\s*\/?>/gi, ' ')
    .replace(/<[^>]*>/g, '')
}
</script>
