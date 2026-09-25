<!--
  What the ads cost, next to what they brought.

  Meta can show the cost per lead; only this table can show the cost per
  customer, because only the CRM knows which of those leads bought. The two are
  routinely in disagreement — the ad with the cheapest leads is very often the
  one with the worst ones — which is the whole reason this screen exists.
-->
<template>
  <div class="flex flex-col gap-4 px-2">
    <p class="text-p-sm text-ink-gray-5">
      {{
        __(
          'Spend read from Meta, results read from this CRM. The cost per customer is the number Ads Manager cannot show you.',
        )
      }}
    </p>

    <div class="flex flex-col gap-4">
      <div
        v-if="status.data && !connected"
        class="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between rounded-lg border border-dashed border-outline-gray-2 p-6"
      >
        <span class="text-p-base text-ink-gray-5">
          {{
            __(
              'Connect your Meta account first, then your ad accounts appear here.',
            )
          }}
        </span>
        <Button
          :label="__('Go to connection')"
          @click="emit('navigate', 'connection')"
        />
      </div>

      <template v-else-if="connected">
        <!-- which accounts' money we are allowed to look at -->
        <div class="rounded-lg border border-outline-gray-2 p-4">
          <div class="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
            <div class="text-p-base-medium text-ink-gray-7">
              {{ __('Ad accounts') }}
            </div>
            <div class="flex flex-wrap gap-2">
              <Button
                size="sm"
                :label="__('Find my ad accounts')"
                :loading="finding"
                @click="findAccounts"
              />
              <Button
                v-if="enabledCount"
                size="sm"
                :label="__('Read spend now')"
                :loading="accounts.data?.syncing"
                @click="syncNow(7)"
              />
              <!-- the first read of an account has no history: this gives it one -->
              <Button
                v-if="enabledCount"
                size="sm"
                variant="ghost"
                :label="__('Read 90 days')"
                :loading="accounts.data?.syncing"
                @click="syncNow(90)"
              />
            </div>
          </div>

          <div v-if="accountList.length" class="mt-3 flex flex-col gap-2">
            <div
              v-for="account in accountList"
              :key="account.account_id"
              class="flex items-center justify-between gap-3 rounded-md border border-outline-gray-1 p-3"
            >
              <div class="min-w-0">
                <div class="flex items-center gap-2">
                  <span class="truncate text-p-base-medium text-ink-gray-8">
                    {{ account.account_name }}
                  </span>
                  <Badge
                    v-if="account.account_status !== 1"
                    :label="__('Not active on Meta')"
                    theme="orange"
                    size="sm"
                  />
                </div>
                <div class="text-p-sm text-ink-gray-5">
                  {{ account.account_id }}
                  <template v-if="account.business_name">
                    · {{ account.business_name }}
                  </template>
                  <template v-if="account.currency">
                    · {{ account.currency }}</template
                  >
                  <template v-if="account.last_synced_on">
                    · {{ __('read') }} {{ account.last_synced_on }}
                  </template>
                </div>
                <div
                  v-if="account.sync_enabled && account.last_error"
                  class="mt-1 text-p-sm text-ink-red-5"
                >
                  {{ account.last_error }}
                </div>
              </div>
              <div
                class="flex flex-wrap items-center gap-2 sm:shrink-0 sm:flex-nowrap"
              >
                <span class="text-p-sm text-ink-gray-5">{{
                  __('Read spend')
                }}</span>
                <Switch
                  :modelValue="Boolean(account.sync_enabled)"
                  @update:modelValue="(v) => toggleAccount(account, v)"
                />
              </div>
            </div>
          </div>
          <div v-else class="mt-3 text-p-base text-ink-gray-5">
            {{
              __(
                'No ad account yet. Press "Find my ad accounts": the CRM asks Facebook which ones the connected user can read.',
              )
            }}
          </div>
          <div
            v-if="!enabledCount && accountList.length"
            class="mt-3 rounded-md bg-surface-gray-1 p-3 text-p-sm text-ink-gray-5"
          >
            {{
              __(
                'Switch on only the accounts that pay for this client. Nothing is read from the others.',
              )
            }}
          </div>
        </div>

        <!-- an ad that was bringing leads and is now stopped is not a log line -->
        <div
          v-if="stopped.length"
          class="rounded-lg border border-outline-red-1 bg-surface-red-1 p-4"
        >
          <div class="text-p-base-medium text-ink-red-5">
            {{
              __('{0} ads that were bringing leads are not running', [
                stopped.length,
              ])
            }}
          </div>
          <div
            v-for="ad in stopped"
            :key="ad.ad_id"
            class="mt-1 text-p-sm text-ink-gray-7"
          >
            {{ ad.ad_name || ad.ad_id }} —
            {{ __(humanStatus(ad.effective_status)) }}
            <span class="text-ink-gray-5">
              ({{ __('{0} leads', [ad.leads]) }})
            </span>
          </div>
        </div>

        <!-- the table itself -->
        <div class="rounded-lg border border-outline-gray-2 p-4">
          <div class="flex items-center justify-between gap-3">
            <div class="text-p-base-medium text-ink-gray-7">
              {{ __('Last {0} days', [days]) }}
            </div>
            <div class="flex gap-1">
              <Button
                v-for="option in [7, 30, 90]"
                :key="option"
                size="sm"
                :variant="option === days ? 'subtle' : 'ghost'"
                :label="__('{0}d', [option])"
                @click="setDays(option)"
              />
            </div>
          </div>

          <div v-if="rows.length" class="mt-3 overflow-x-auto">
            <table class="w-full text-p-sm">
              <thead class="text-ink-gray-5">
                <tr class="border-b border-outline-gray-1 text-left">
                  <th class="py-2 pr-3 font-medium">{{ __('Ad') }}</th>
                  <th class="py-2 px-2 text-right font-medium">
                    {{ __('Spend') }}
                  </th>
                  <th class="py-2 px-2 text-right font-medium">
                    {{ __('Leads') }}
                  </th>
                  <th class="py-2 px-2 text-right font-medium">
                    {{ __('Per lead') }}
                  </th>
                  <th class="py-2 px-2 text-right font-medium">
                    {{ __('Won') }}
                  </th>
                  <th class="py-2 px-2 text-right font-medium">
                    {{ __('Revenue') }}
                  </th>
                  <th class="py-2 px-2 text-right font-medium">
                    {{ __('Per customer') }}
                  </th>
                  <th class="py-2 pl-2 text-right font-medium">
                    {{ __('ROAS') }}
                  </th>
                </tr>
              </thead>
              <tbody class="divide-y divide-outline-gray-1">
                <tr v-for="row in rows" :key="row.ad_id">
                  <td class="py-2 pr-3">
                    <div class="flex items-center gap-2">
                      <span class="max-w-sm truncate text-ink-gray-8">
                        {{ row.ad_name || row.ad_id }}
                      </span>
                      <Badge
                        v-if="
                          row.effective_status &&
                          row.effective_status !== 'ACTIVE'
                        "
                        :label="__(humanStatus(row.effective_status))"
                        theme="orange"
                        size="sm"
                      />
                    </div>
                    <div class="max-w-sm truncate text-ink-gray-4">
                      {{
                        [row.campaign_name, row.adset_name]
                          .filter(Boolean)
                          .join(' · ')
                      }}
                    </div>
                  </td>
                  <td class="px-2 text-right text-ink-gray-7">
                    {{ money(row.spend, row.currency) }}
                  </td>
                  <td class="px-2 text-right text-ink-gray-7">
                    {{ row.leads }}
                  </td>
                  <td class="px-2 text-right text-ink-gray-7">
                    {{ money(row.cost_per_lead, row.currency) }}
                  </td>
                  <td class="px-2 text-right text-ink-gray-7">{{ row.won }}</td>
                  <td class="px-2 text-right text-ink-gray-7">
                    {{ money(row.revenue, row.currency) }}
                  </td>
                  <td class="px-2 text-right text-ink-gray-7">
                    {{ money(row.cost_per_won, row.currency) }}
                  </td>
                  <td class="pl-2 text-right" :class="roasClass(row.roas)">
                    {{ row.roas === null ? '—' : row.roas.toFixed(2) + '×' }}
                  </td>
                </tr>
              </tbody>
              <tfoot
                v-if="totals"
                class="border-t border-outline-gray-2 text-ink-gray-8"
              >
                <tr>
                  <td class="py-2 pr-3 text-p-sm-medium">{{ __('Total') }}</td>
                  <td class="px-2 text-right text-p-sm-medium">
                    {{ money(totals.spend, totals.currency) }}
                  </td>
                  <td class="px-2 text-right text-p-sm-medium">
                    {{ totals.leads }}
                  </td>
                  <td class="px-2 text-right text-p-sm-medium">
                    {{ money(totals.cost_per_lead, totals.currency) }}
                  </td>
                  <td class="px-2 text-right text-p-sm-medium">
                    {{ totals.won }}
                  </td>
                  <td class="px-2 text-right text-p-sm-medium">
                    {{ money(totals.revenue, totals.currency) }}
                  </td>
                  <td class="px-2 text-right text-p-sm-medium">
                    {{ money(totals.cost_per_won, totals.currency) }}
                  </td>
                  <td class="pl-2 text-right text-p-sm-medium">
                    {{
                      totals.roas === null ? '—' : totals.roas.toFixed(2) + '×'
                    }}
                  </td>
                </tr>
              </tfoot>
            </table>
            <div
              v-if="totals?.mixed_currencies"
              class="mt-2 text-p-sm text-ink-orange-5"
            >
              {{
                __(
                  'These accounts bill in different currencies, so the total is a sum of unlike numbers. Read the rows, not the total.',
                )
              }}
            </div>
            <div class="mt-2 text-p-sm text-ink-gray-5">
              {{
                __(
                  'A lead counts for the ad that first brought that person. Revenue is the value of deals marked won.',
                )
              }}
            </div>
          </div>
          <div
            v-else-if="performance.loading"
            class="mt-3 flex items-center gap-2 text-ink-gray-6"
          >
            <LoadingIndicator class="size-4" />
            {{ __('Reading…') }}
          </div>
          <div v-else class="mt-3 text-p-base text-ink-gray-5">
            {{
              enabledCount
                ? __(
                    'Nothing spent in this period, or the spend has not been read yet.',
                  )
                : __('Switch on an ad account above to see this table fill up.')
            }}
          </div>
        </div>
      </template>
    </div>
  </div>
</template>

<script setup>
import { createResource, LoadingIndicator, Switch, toast } from 'frappe-ui'
import { computed, ref } from 'vue'

// loaded once by the page around the tabs
const props = defineProps({
  status: { type: Object, required: true },
})

const emit = defineEmits(['navigate'])

const connected = computed(() => Boolean(props.status.data?.connected))

const accounts = createResource({
  url: 'crm.integrations.meta.api.get_ad_accounts',
  auto: true,
})
const accountList = computed(() => accounts.data?.accounts || [])
const enabledCount = computed(
  () => accountList.value.filter((a) => a.sync_enabled).length,
)

const days = ref(30)
const performance = createResource({
  url: 'crm.integrations.meta.api.get_ad_performance',
  params: { days: days.value },
  auto: true,
})
const rows = computed(() => performance.data?.rows || [])
const stopped = computed(() => performance.data?.stopped || [])

// Meta's own vocabulary, in words somebody can act on
const WORDS = {
  DISAPPROVED: 'Rejected by Meta',
  WITH_ISSUES: 'Has issues',
  PENDING_REVIEW: 'Waiting for review',
  PAUSED: 'Paused',
  ADSET_PAUSED: 'Ad set paused',
  CAMPAIGN_PAUSED: 'Campaign paused',
}
function humanStatus(status) {
  return WORDS[status] || status || ''
}
const totals = computed(() => performance.data?.totals || null)

function setDays(value) {
  days.value = value
  performance.update({ params: { days: value } })
  performance.reload()
}

const finding = ref(false)
function findAccounts() {
  finding.value = true
  createResource({
    url: 'crm.integrations.meta.api.refresh_ad_accounts',
    auto: true,
    onSuccess: (data) => {
      finding.value = false
      toast.success(__('{0} ad accounts found', [data.found]))
      accounts.reload()
    },
    onError: (e) => {
      finding.value = false
      toast.error(e.messages?.[0] || e.message || __('Unknown error'))
    },
  })
}

function toggleAccount(account, enabled) {
  createResource({
    url: 'crm.integrations.meta.api.set_account_sync',
    params: { account_id: account.account_id, enabled },
    auto: true,
    onSuccess: () => {
      accounts.reload()
      performance.reload()
    },
    onError: (e) => {
      accounts.reload()
      toast.error(e.messages?.[0] || e.message || __('Unknown error'))
    },
  })
}

function syncNow(days) {
  createResource({
    url: 'crm.integrations.meta.api.sync_ad_spend_now',
    params: { days },
    auto: true,
    onSuccess: () => {
      toast.success(
        __('Reading the spend in the background. This takes a moment.'),
      )
      // the job runs outside this request: come back for the numbers
      setTimeout(() => {
        accounts.reload()
        performance.reload()
      }, 8000)
    },
    onError: (e) =>
      toast.error(e.messages?.[0] || e.message || __('Unknown error')),
  })
}

function money(value, currency) {
  if (value === null || value === undefined) return '—'
  const amount = Number(value).toLocaleString(undefined, {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  })
  return currency ? `${amount} ${currency}` : amount
}

// green pays for itself, red does not; no colour when there is nothing to judge
function roasClass(roas) {
  if (roas === null || roas === undefined) return 'text-ink-gray-4'
  return roas >= 1 ? 'text-ink-green-6' : 'text-ink-red-5'
}
</script>
