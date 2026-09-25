<!--
  The Social Planner's own settings: where its profiles come from, and which of
  them it offers.

  It used to be a copy of the Meta connection with a list underneath — its own
  "Connect with Facebook" (a full-page redirect, where the real one opens a
  popup), and an "App ID and secret" message shown to clients whose app is
  provided centrally. The connection lives in Integrations now; this page
  starts from the sources, so a second one is a new row here and not a new
  page.
-->
<template>
  <div
    class="flex h-full flex-col gap-6 overflow-y-auto px-4 py-6 sm:px-6 sm:py-8 text-ink-gray-8"
  >
    <div
      class="flex flex-col items-stretch gap-3 px-2 sm:flex-row sm:items-start sm:justify-between sm:gap-3"
    >
      <div class="flex min-w-0 flex-1 flex-col gap-1">
        <h2 class="flex gap-2 text-2xl-semibold leading-none h-5">
          {{ __('Social Planner') }}
        </h2>
        <p class="text-p-base text-ink-gray-6">
          {{
            __(
              'The pages and accounts the planner publishes to. They come from the sources connected to the CRM: switch off the ones it should not offer.',
            )
          }}
        </p>
      </div>
      <Button
        v-if="anyConnected"
        class="shrink-0"
        :label="__('Refresh profiles')"
        iconLeft="refresh-cw"
        :loading="refreshing || syncing"
        @click="refreshProfiles"
      />
    </div>

    <!-- sources -->
    <section class="flex flex-col gap-2 px-2">
      <h3 class="text-p-base-medium text-ink-gray-8">{{ __('Sources') }}</h3>
      <div
        v-for="source in sources.data || []"
        :key="source.key"
        class="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between rounded-lg border border-outline-gray-2 p-4"
      >
        <div class="flex min-w-0 flex-1 items-center gap-3">
          <span class="flex shrink-0 -space-x-1.5">
            <span
              v-for="platform in source.platforms"
              :key="platform"
              class="flex size-7 items-center justify-center rounded-full text-xs font-semibold text-white ring-2 ring-surface-white"
              :style="{ backgroundColor: platformColor(platform) }"
            >
              {{ platformInitial(platform) }}
            </span>
          </span>
          <div class="flex min-w-0 flex-col">
            <div class="flex items-center gap-2">
              <span class="text-p-base-medium text-ink-gray-8">
                {{ source.label }}
              </span>
              <Badge
                :label="
                  source.connected ? __('Connected') : __('Not connected')
                "
                :theme="source.connected ? 'green' : 'gray'"
                size="sm"
              />
            </div>
            <span class="text-p-sm text-ink-gray-5">
              {{ source.description }}
            </span>
            <span v-if="source.connected" class="text-p-sm text-ink-gray-5">
              {{
                __('{0} · {1} of {2} profiles in the planner', [
                  source.account,
                  source.enabled_profiles,
                  source.profiles,
                ])
              }}
            </span>
          </div>
        </div>
        <Button
          :variant="source.connected ? 'outline' : 'solid'"
          :label="source.connected ? __('Manage') : __('Connect')"
          @click="openSource(source)"
        />
      </div>
      <p class="text-p-sm text-ink-gray-5">
        {{
          __(
            'More sources will appear here as new integrations are connected to the CRM.',
          )
        }}
      </p>
    </section>

    <!-- profiles -->
    <section class="flex flex-col gap-2 px-2">
      <div class="flex items-center justify-between gap-2">
        <h3 class="text-p-base-medium text-ink-gray-8">{{ __('Profiles') }}</h3>
        <span v-if="accounts.data?.length" class="text-p-sm text-ink-gray-5">
          {{ __('In the planner') }}
        </span>
      </div>
      <div
        v-if="accounts.data?.length"
        class="divide-y divide-outline-gray-1 rounded-lg border border-outline-gray-2"
      >
        <div
          v-for="account in accounts.data"
          :key="account.name"
          class="flex items-center gap-3 px-3 py-2.5"
        >
          <span
            class="flex size-6 shrink-0 items-center justify-center rounded-full text-xs font-semibold text-white"
            :style="{ backgroundColor: platformColor(account.platform) }"
          >
            {{ platformInitial(account.platform) }}
          </span>
          <div class="min-w-0 flex-1">
            <div
              class="truncate text-p-base"
              :class="account.enabled ? 'text-ink-gray-8' : 'text-ink-gray-5'"
            >
              {{ account.account_name }}
            </div>
            <div class="truncate text-p-sm text-ink-gray-5">
              {{ account.platform }}
            </div>
          </div>
          <Switch
            :modelValue="Boolean(account.enabled)"
            size="sm"
            :disabled="busyAccount === account.name"
            @update:modelValue="(v) => toggleAccount(account, v)"
          />
        </div>
      </div>
      <div
        v-else-if="syncing"
        class="flex items-center gap-2 rounded-lg border border-dashed border-outline-gray-2 p-6 text-p-base text-ink-gray-5"
      >
        <LoadingIndicator class="size-4" />
        {{ __('Reading your Pages from Facebook…') }}
      </div>
      <div
        v-else-if="sources.data"
        class="rounded-lg border border-dashed border-outline-gray-2 p-6 text-center text-p-base text-ink-gray-5"
      >
        {{
          anyConnected
            ? __(
                'No profiles yet. The connected account shared no Page with the CRM: add them from the source, then refresh.',
              )
            : __('Connect a source above and its profiles appear here.')
        }}
      </div>
    </section>
  </div>
</template>

<script setup>
import { activeSettingsPage } from '@/composables/settings'
import { platformColor, platformInitial } from '@/utils/social'
import { createResource, LoadingIndicator, Switch, toast } from 'frappe-ui'
import { computed, onUnmounted, ref, watch } from 'vue'

const refreshing = ref(false)
const busyAccount = ref('')

const sources = createResource({
  url: 'crm.api.social.get_sources',
  auto: true,
})

const accounts = createResource({
  url: 'crm.api.social.list_accounts_admin',
  auto: true,
})

const anyConnected = computed(() =>
  (sources.data || []).some((source) => source.connected),
)
// a source is reading its accounts again, in the background
const syncing = computed(() =>
  (sources.data || []).some((source) => source.syncing),
)

// The profiles follow the source's own sync, which runs in the background: come
// back until it is done, then show what it found.
let pollTimer = null
function pollWhileSyncing() {
  clearTimeout(pollTimer)
  if (!syncing.value) return
  pollTimer = setTimeout(() => {
    sources.reload()
    pollWhileSyncing()
  }, 3000)
}
watch(syncing, (now, before) => {
  pollWhileSyncing()
  if (before && !now) accounts.reload()
})
onUnmounted(() => clearTimeout(pollTimer))

// the connection belongs to the integration: this page only points at it
function openSource(source) {
  activeSettingsPage.value = source.settings_page
}

function refreshProfiles() {
  refreshing.value = true
  createResource({
    url: 'crm.api.social.sync_profiles',
    auto: true,
    onSuccess: (data) => {
      refreshing.value = false
      accounts.data = data.accounts
      sources.reload()
      // what was already known is in the list now; what Facebook may have
      // added since is being read, and joins the list when that is done
      toast.success(
        data.refreshing
          ? __('Profiles updated — checking Facebook for new Pages…')
          : __('Profiles updated'),
      )
    },
    onError: (e) => {
      refreshing.value = false
      toast.error(e.messages?.[0] || __('Could not refresh the profiles'))
    },
  })
}

function toggleAccount(account, enabled) {
  busyAccount.value = account.name
  createResource({
    url: 'crm.api.social.set_account_enabled',
    params: { name: account.name, enabled },
    auto: true,
    onSuccess: () => {
      busyAccount.value = ''
      accounts.reload()
      sources.reload()
    },
    onError: (e) => {
      busyAccount.value = ''
      toast.error(e.messages?.[0] || __('Failed to update'))
      accounts.reload()
    },
  })
}
</script>
