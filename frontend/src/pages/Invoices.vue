<!--
  Copyright (c) 2026, NPM2 Solutions Srl and contributors
  For license information, please see license.txt
-->
<template>
  <LayoutHeader>
    <template #left-header>
      <Breadcrumbs
        :items="[{ label: __('Invoices'), route: { name: 'Invoices' } }]"
      />
      <!-- the company's name gives way on a phone, it does not run under the
           buttons -->
      <Dropdown
        v-if="companies.data?.length > 1"
        class="min-w-0"
        :options="companyOptions"
      >
        <Button variant="ghost" iconRight="chevron-down" class="max-w-full">
          <span class="truncate">{{ company || __('All companies') }}</span>
        </Button>
      </Dropdown>
    </template>
    <template #right-header>
      <Button
        v-if="puo('fatture.configura')"
        variant="ghost"
        :label="isMobileView ? undefined : __('Settings')"
        :iconLeft="isMobileView ? undefined : 'settings'"
        :icon="isMobileView ? 'settings' : undefined"
        :aria-label="__('Settings')"
        @click="openSettings('Issuing company')"
      />
      <Button
        v-if="puo('fatture.emetti')"
        variant="solid"
        :label="__('New invoice')"
        iconLeft="plus"
        @click="nuovaFattura(null, { alCambio: ricarica })"
      />
    </template>
  </LayoutHeader>

  <div ref="contenitore" class="flex-1 overflow-y-auto px-3 py-4 sm:px-5">
    <!-- pulled down from the top on a phone, the invoices reload -->
    <TiraPerAggiornare v-bind="tira" />
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
        <div v-if="puo('fatture.configura')">
          <Button
            variant="solid"
            :label="__('Create the company')"
            @click="openSettings('Issuing company')"
          />
        </div>
      </div>

      <template v-else>
        <!-- invoicing in test: said where invoices are made, every time -->
        <div
          v-if="prova.data?.company && !prova.data.live"
          class="flex items-center justify-between gap-3 rounded-xl border border-outline-amber-2 bg-surface-amber-1 px-4 py-3 max-md:flex-col max-md:items-start"
        >
          <div class="flex min-w-0 flex-col gap-0.5">
            <span class="text-p-base-medium text-ink-gray-8">
              {{ __('Invoicing in test') }}
            </span>
            <span class="text-p-sm text-ink-gray-6">
              {{
                __(
                  'The invoices are numbered PROVA and reach nobody. When everything is right, go live.',
                )
              }}
            </span>
          </div>
          <Button
            v-if="puo('fatture.configura')"
            class="shrink-0"
            :label="__('Test and go live')"
            @click="openSettings('Provider connection')"
          />
        </div>

        <div class="flex items-center gap-1">
          <Button
            v-for="entry in tabs"
            :key="entry.value"
            :variant="tab === entry.value ? 'subtle' : 'ghost'"
            :label="entry.label"
            @click="tab = entry.value"
          />
        </div>

        <!-- ------------------------------------------------------- to do -->
        <div v-if="tab === 'todo'" class="flex flex-col gap-3">
          <!-- The agenda already knows the client, the performer and the service.
               Retyping them is the difference between a system used between
               patients and one abandoned by Thursday. -->
          <div
            v-if="daFatturare.data?.length"
            class="flex flex-col gap-2 rounded-xl border border-outline-blue-2 bg-surface-blue-1 px-4 py-3"
          >
            <div class="flex items-center justify-between">
              <span class="text-p-base-medium text-ink-gray-8">
                {{ __('From the agenda, not yet invoiced') }}
              </span>
              <span class="text-p-sm text-ink-gray-6">
                {{ __('{0} appointments', [daFatturare.data.length]) }}
              </span>
            </div>
            <div
              v-for="incontro in allAppointments
                ? daFatturare.data
                : daFatturare.data.slice(0, 8)"
              :key="incontro.name"
              class="flex items-center justify-between gap-3 border-t border-outline-blue-2 pt-2 first:border-0 first:pt-0"
            >
              <div class="min-w-0">
                <div class="truncate text-p-sm-medium text-ink-gray-7">
                  {{ incontro.title || incontro.name }}
                </div>
                <div class="text-p-xs text-ink-gray-5">
                  {{ formatDate(incontro.starts_on, 'DD/MM/YYYY HH:mm') }}
                </div>
              </div>
              <Button
                variant="subtle"
                :loading="emettendo === incontro.name"
                :label="__('Invoice it')"
                @click="fatturaIncontro(incontro)"
              />
            </div>
            <!-- the count above said sixteen and eight were listed, with no
                 way to reach the other eight -->
            <Button
              v-if="daFatturare.data.length > 8"
              variant="ghost"
              class="self-start"
              :label="
                allAppointments
                  ? __('Show fewer')
                  : __('Show all ({0})', [daFatturare.data.length])
              "
              @click="allAppointments = !allAppointments"
            />
          </div>

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
            class="flex flex-col gap-2 rounded-xl border border-outline-gray-2 px-4 py-3 sm:flex-row sm:items-center sm:justify-between sm:gap-3"
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
            <div class="flex flex-wrap items-center gap-2 sm:shrink-0">
              <Badge
                :theme="row.state.startsWith('scart') ? 'red' : 'orange'"
                :label="statusLabel(row.state)"
              />
              <!-- Reporting is only offered when somebody here can actually do
                   it. On an export company the file is prepared and uploaded
                   from the portal, so there is nothing to press. -->
              <Button
                v-if="
                  row.action === 'ts' &&
                  tsMode !== 'export' &&
                  puo('fatture.invia')
                "
                variant="subtle"
                :loading="sending === row.name"
                :label="__('Report', null, 'Sistema TS')"
                @click="report(row)"
              />
              <Button
                variant="subtle"
                :label="__('Open', null, 'Action')"
                @click="apriFattura(row.name, { alCambio: ricarica })"
              />
            </div>
          </div>
        </div>

        <!-- ---------------------------------------------------- invoices -->
        <div v-else-if="tab === 'invoices'" class="flex flex-col gap-2">
          <div
            v-for="row in invoices.data || []"
            :key="row.name"
            class="flex flex-col gap-2 rounded-xl border border-outline-gray-2 px-4 py-3 sm:flex-row sm:items-center sm:justify-between sm:gap-3"
          >
            <div class="flex min-w-0 flex-col">
              <span class="truncate text-p-base-medium text-ink-gray-8">
                {{ row.document_number || __('Draft') }} ·
                {{ row.billing_name }}
              </span>
              <span class="text-p-sm text-ink-gray-5">
                {{ dayjs(row.posting_date).format('DD/MM/YYYY') }} ·
                {{ formatEuro(row.grand_total) }}
                <template v-if="row.channel">
                  · {{ channelLabel(row.channel) }}
                </template>
              </span>
            </div>
            <div class="flex flex-wrap items-center gap-2 sm:shrink-0">
              <!-- On a draft, where it will go matters more than where it has
                   been: a document that turns out to be un-issuable at submit
                   has already cost the time of whoever typed it, with the client
                   still in the room. -->
              <Badge
                v-if="row.docstatus === 0 && row.channel"
                :theme="row.channel === 'sdi' ? 'blue' : 'green'"
                :label="channelLabel(row.channel)"
              />
              <Badge
                v-if="row.sdi_status && row.sdi_status !== 'non_applicabile'"
                :theme="invoiceStatusTheme(row.sdi_status)"
                :label="'SdI: ' + statusLabel(row.sdi_status)"
              />
              <Badge
                v-if="row.ts_status && row.ts_status !== 'non_applicabile'"
                :theme="invoiceStatusTheme(row.ts_status)"
                :label="'TS: ' + statusLabel(row.ts_status)"
              />
              <!-- The transmit action does not exist on a document that cannot
                   take that channel. A greyed-out button invites somebody to go
                   looking for how to turn it on. -->
              <Button
                v-if="
                  row.channel === 'sdi' &&
                  row.docstatus === 1 &&
                  row.sdi_status === 'da_inviare'
                "
                variant="subtle"
                :loading="sending === row.name"
                :label="__('Transmit')"
                @click="transmit(row)"
              />
              <Button
                variant="subtle"
                :label="__('Open', null, 'Action')"
                @click="apriFattura(row.name, { alCambio: ricarica })"
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
                  <div class="text-p-sm text-ink-gray-5">
                    {{ statusLabel(key) }}
                  </div>
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
              <!-- preparing the year's file is sending it: who transmits -->
              <div v-if="puo('fatture.invia')">
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
                class="flex flex-col gap-2 rounded-xl border border-outline-gray-2 px-4 py-3 sm:flex-row sm:items-center sm:justify-between sm:gap-3"
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
                <div class="flex flex-wrap items-center gap-2 sm:shrink-0">
                  <Badge
                    :theme="invoiceStatusTheme(row.status)"
                    :label="statusLabel(row.status)"
                  />
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
import TiraPerAggiornare from '@/components/Mobile/TiraPerAggiornare.vue'
import { useTiraPerAggiornare } from '@/composables/tiraPerAggiornare'
import { formatDate } from '@/utils'
import { formatEuro, invoiceStatusTheme, statusLabel } from '@/utils/invoicing'
import {
  createListResource,
  createResource,
  Badge,
  Breadcrumbs,
  Dropdown,
  FormControl,
  call,
  dayjs,
  toast,
} from 'frappe-ui'
import { computed, ref, watch } from 'vue'
import { useFattura } from '@/composables/fattura'
import {
  activeSettingsPage,
  isMobileView,
  showSettings,
} from '@/composables/settings'
import { usersStore } from '@/stores/users'

// the front desk issues invoices; configuring invoicing is the manager's
const { puo } = usersStore()
const { apriFattura, nuovaFattura } = useFattura()

const tab = ref('todo')
const company = ref('')
const year = ref(new Date().getFullYear())
const sending = ref('')
const preparing = ref(false)
const lastPrepared = ref(null)

const tabs = computed(() => [
  { value: 'todo', label: __('To do') },
  { value: 'invoices', label: __('Invoices') },
  { value: 'ts', label: __('Sistema TS') },
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

// where the company is (in test or live) and how it reports to the Sistema TS:
// the server says it, the channel being the agency's to read
const prova = createResource({ url: 'crm.invoicing.prova.get_status' })
const tsMode = computed(() => prova.data?.ts_mode || 'export')
watch(company, (nome) => {
  if (nome) prova.fetch({ company: nome })
})

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

// Appointments that happened and produced no document yet. Past only: a list
// showing tomorrow's bookings is a list nobody trusts.
const daFatturare = createResource({
  url: 'crm.invoicing.api.appointments_to_invoice',
  // a queue of invoices to issue, for whoever issues them: Read only reads
  auto: puo('fatture.emetti'),
})

const emettendo = ref('')
const allAppointments = ref(false)

async function fatturaIncontro(incontro) {
  emettendo.value = incontro.name
  try {
    const nome = await call('crm.invoicing.api.issue_from_appointment', {
      appointment: incontro.name,
    })
    ricarica()
    // the draft the agenda filled in, to check and issue here
    apriFattura(nome, { alCambio: ricarica })
  } catch (errore) {
    // The commonest one is a service with no fiscal card, and saying so is more
    // use than a generic failure: it names the thing to go and configure.
    toast.error(errore.messages?.[0] || __('Could not open the invoice'))
  } finally {
    emettendo.value = ''
  }
}
const tsStatus = createResource({ url: 'crm.tessera_sanitaria.api.ts_status' })
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

// whatever the invoice dialog changed shows up in the lists behind it
function ricarica() {
  return Promise.all([
    daFatturare.reload(),
    invoices.reload(),
    company.value && pending.fetch({ company: company.value }),
  ])
}

const contenitore = ref(null)
const tira = useTiraPerAggiornare(contenitore, ricarica)

function openSettings(page) {
  // Everything that configures invoicing lives in the settings modal, so the
  // console never sends anybody to the desk to change a rule.
  activeSettingsPage.value = page
  showSettings.value = true
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

async function report(row) {
  sending.value = row.name
  try {
    const result = await call('crm.tessera_sanitaria.api.send_to_ts', {
      invoice: row.name,
    })
    // A rejection is an answer, not a crash: it says which code came back, and
    // codes 105 and 106 have already moved the company's submission mode.
    if (result.accepted) toast.success(result.summary)
    else toast.error(result.summary)
    pending.fetch({ company: company.value })
  } catch (error) {
    toast.error(stripHtml(error.messages?.[0] || error.message))
  } finally {
    sending.value = ''
  }
}

async function prepareTs() {
  preparing.value = true
  try {
    lastPrepared.value = await call(
      'crm.tessera_sanitaria.api.prepare_ts_submission',
      {
        company: company.value,
        year: year.value,
      },
    )
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
