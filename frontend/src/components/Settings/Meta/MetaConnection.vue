<!--
  The Meta connection: the Facebook account the CRM reads with, and the Pages it
  uses.

  Two readers. A manager connects the account, chooses the Pages and reconnects
  when asked — that is the page. The plumbing underneath (the app, its webhook,
  the permissions Facebook granted, the last call Meta made) belongs to whoever
  can repair it, so it sits in "Technical details", shown to administrators
  only; the server does not even send it to anybody else.
-->
<template>
  <div class="flex flex-col gap-4 px-2">
    <!-- the app itself, when this site owns one: developer credentials, so an
         administrator's to type. Provided centrally, there is nothing here. -->
    <div
      v-if="isAdmin && !managed"
      class="flex flex-col gap-3 rounded-lg border border-outline-gray-2 p-4"
    >
      <div class="flex flex-col">
        <span class="text-p-base-medium text-ink-gray-7">
          {{ __('Meta app') }}
        </span>
        <span class="text-p-sm text-ink-gray-5">
          {{
            __(
              'The app on developers.facebook.com this CRM connects through. Once it is saved, anyone who manages the CRM can connect their account.',
            )
          }}
        </span>
      </div>
      <div class="grid grid-cols-1 sm:grid-cols-2 gap-3">
        <FormControl
          v-model="appForm.app_id"
          type="text"
          :label="__('App ID')"
        />
        <FormControl
          v-model="appForm.app_secret"
          type="password"
          :label="__('App Secret')"
          :placeholder="
            status.data?.has_app_secret
              ? __('•••••• (saved — type to replace)')
              : ''
          "
        />
      </div>
      <div>
        <Button
          :label="__('Save app')"
          variant="solid"
          :loading="savingApp"
          @click="saveApp"
        />
      </div>
    </div>

    <!-- nothing to connect to, and nothing a manager can do about it -->
    <div
      v-else-if="status.data && !appReady"
      class="flex items-start gap-2 rounded-lg bg-surface-gray-2 px-3 py-2.5 text-p-sm text-ink-gray-7"
    >
      <FeatherIcon name="info" class="mt-0.5 size-4 shrink-0" />
      {{
        __(
          'Meta is not set up on this CRM yet. An administrator has to add it before an account can be connected.',
        )
      }}
    </div>

    <!-- The webhook configures itself and belongs to the plumbing: it appears
         only when it is broken, to whoever can fix it, with the button that
         does. Nothing to copy by hand. -->
    <div
      v-if="webhookBroken"
      class="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between rounded-lg border border-outline-amber-2 bg-surface-amber-1 p-4"
    >
      <div class="flex flex-col">
        <span class="text-p-base-medium text-ink-gray-7">
          {{ __('Real-time leads are off') }}
        </span>
        <span class="text-p-sm text-ink-gray-6">
          {{
            __(
              'Meta is not notifying this site yet, so leads arrive with the hourly check instead of instantly.',
            )
          }}
        </span>
        <span v-if="webhook.data?.error" class="text-p-sm text-ink-red-5">
          {{ webhook.data.error }}
        </span>
      </div>
      <Button
        :label="__('Fix it')"
        :loading="configuringWebhook"
        @click="configureWebhook"
      />
    </div>

    <!-- the account -->
    <div
      class="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between rounded-lg border border-outline-gray-2 p-4"
    >
      <div class="flex min-w-0 flex-1 items-center gap-3">
        <FacebookIcon class="size-8 shrink-0" />
        <div class="flex min-w-0 flex-col">
          <span class="truncate text-p-base-medium text-ink-gray-8">
            {{
              connected
                ? __('Connected as {0}', [status.data.connected_user_name])
                : __('Facebook account')
            }}
          </span>
          <span class="text-p-sm text-ink-gray-5">
            {{
              connected
                ? __('Pages, lead forms and ad accounts are read with it.')
                : __(
                    'Sign in with the Facebook account that manages your Pages and ad accounts.',
                  )
            }}
          </span>
          <!-- nothing renews the token: say so while reconnecting is a click -->
          <span
            v-if="connected && expiry?.expired"
            class="text-p-sm text-ink-red-5"
          >
            {{
              __(
                'The connection to Facebook has expired. Reconnect to go on reading ad spend and sending lead quality.',
              )
            }}
          </span>
          <span
            v-else-if="connected && expiry?.soon"
            class="text-p-sm text-ink-amber-6"
          >
            {{
              __(
                'The connection to Facebook expires on {0}. Reconnect to renew it.',
                [expiryDate],
              )
            }}
          </span>
          <span v-if="metaError" class="text-p-sm text-ink-red-5">
            {{ metaError }}
          </span>
        </div>
      </div>
      <div class="flex shrink-0 gap-2">
        <Button
          v-if="!connected"
          variant="solid"
          :label="__('Connect with Facebook')"
          :disabled="!appReady"
          @click="connect()"
        />
        <template v-else>
          <Button
            :variant="expiry?.soon || expiry?.expired ? 'solid' : 'outline'"
            :label="__('Reconnect')"
            @click="connect()"
          />
          <Button
            variant="ghost"
            :label="__('Disconnect')"
            @click="confirmingDisconnect = true"
          />
        </template>
      </div>
    </div>

    <!--
      A permission the dialog did not grant. The token stays valid, so nothing
      looks broken until a Page refuses with Meta's own message, which names
      six permissions without saying which one is missing. Facebook never asks
      again on a normal login, so the way out is the rerequest dialog. Which
      permissions they are is for an administrator; what to do is for everyone.
    -->
    <div
      v-if="connected && missingScopes.length"
      class="flex flex-col gap-2 rounded-lg border border-outline-red-1 bg-surface-red-1 p-4"
    >
      <div class="text-p-base-medium text-ink-red-5">
        {{ __('Facebook did not grant everything this CRM needs') }}
      </div>
      <div class="text-p-sm text-ink-gray-6">
        {{
          __(
            'Pages will refuse to subscribe and leads will not arrive. Facebook does not ask again by itself: press the button, and tick every box and every Page in the dialog.',
          )
        }}
      </div>
      <div v-if="isAdmin" class="font-mono text-p-sm text-ink-gray-7">
        {{ missingScopes.join(' · ') }}
      </div>
      <div>
        <Button
          variant="solid"
          theme="red"
          :label="__('Ask Facebook again')"
          @click="connect(true)"
        />
      </div>
    </div>

    <!-- which Pages Facebook actually shared: the dialog, not the CRM,
         decides this, and granting none still reports a successful login -->
    <div
      v-if="connected"
      class="flex flex-col gap-3 rounded-lg border border-outline-gray-2 p-4"
    >
      <div class="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <div class="flex min-w-0 flex-col">
          <span class="text-p-base-medium text-ink-gray-7">{{
            __('Your Pages')
          }}</span>
          <span class="text-p-sm text-ink-gray-5">
            {{
              __(
                'Give Facebook access once, then decide here which Pages send their leads to the CRM.',
              )
            }}
          </span>
        </div>
        <div class="flex flex-wrap gap-2 sm:shrink-0">
          <Button
            icon="refresh-cw"
            :tooltip="__('Read the Pages again from Facebook')"
            :loading="refreshing || syncing"
            @click="refreshPages"
          />
          <Button
            :label="__('Add Pages from Facebook')"
            :loading="choosing"
            @click="connect(true)"
          />
        </div>
      </div>

      <div
        v-if="syncing && !pageCount"
        class="flex items-center gap-2 text-p-sm text-ink-gray-6"
      >
        <LoadingIndicator class="size-4" />
        {{
          __(
            'Reading your Pages from Facebook — this can take a minute on an account with many.',
          )
        }}
      </div>

      <template v-else-if="pageCount">
        <FormControl
          v-if="showSearch"
          v-model="search"
          type="text"
          :placeholder="__('Search a Page')"
        />

        <div class="flex flex-col">
          <div
            class="flex items-center justify-between px-2 pb-1 text-p-xs text-ink-gray-5"
          >
            <span>{{ __('Page') }}</span>
            <span>{{ __('Leads to the CRM') }}</span>
          </div>
          <div
            v-for="page in pages"
            :key="page.name"
            class="flex items-center gap-3 rounded-md px-2 py-1.5 hover:bg-surface-gray-1"
          >
            <div class="flex min-w-0 flex-1 flex-col">
              <span class="truncate text-p-sm text-ink-gray-8">
                {{ page.page_name || page.name }}
              </span>
              <span
                v-if="page.instagram_username"
                class="text-p-xs text-ink-gray-5"
              >
                {{ __('Instagram') }}: @{{ page.instagram_username }}
              </span>
            </div>
            <Switch
              size="sm"
              :modelValue="Boolean(page.sync_enabled)"
              :disabled="busyPage === page.name"
              @update:modelValue="(value) => togglePage(page, value)"
            />
          </div>
        </div>

        <div v-if="pages.length < total" class="flex items-center gap-3">
          <Button
            :label="__('Show more')"
            :loading="pageList.loading"
            @click="loadMore"
          />
          <span class="text-p-sm text-ink-gray-5">
            {{ __('{0} of {1}', [pages.length, total]) }}
          </span>
        </div>

        <div v-if="!pages.length" class="text-p-sm text-ink-gray-5">
          {{ __('No Page matches this search.') }}
        </div>

        <!-- counted, not listed: a switch that can only fail is noise, but a
             Page disappearing without a word is a mystery of its own -->
        <span v-if="hidden" class="text-p-sm text-ink-gray-5">
          {{
            __(
              '{0} Page(s) are not shown: Facebook did not give the CRM the advertising role on them, so their leads cannot be read. Grant them again to use them.',
              [hidden],
            )
          }}
        </span>

        <!-- the same Pages publish, with a switch of their own elsewhere -->
        <div
          class="flex flex-wrap items-center justify-between gap-2 border-t border-outline-gray-1 pt-3 text-p-sm text-ink-gray-5"
        >
          <span>
            {{
              __(
                'The Social Planner can publish on these Pages and their Instagram accounts.',
              )
            }}
          </span>
          <Button
            variant="ghost"
            iconRight="arrow-right"
            :label="__('Social Planner profiles')"
            @click="emit('navigate', 'Social profiles')"
          />
        </div>
      </template>

      <div v-else class="flex flex-col gap-1 text-p-sm">
        <span class="text-ink-red-5">
          {{ __('Facebook granted the CRM no Page.') }}
        </span>
        <span class="text-ink-gray-5">
          {{
            __(
              'The login worked but no Page came with it. Press "Add Pages from Facebook" and tick the Pages you administer — granting them all is fine, you choose here which ones the CRM actually uses.',
            )
          }}
        </span>
      </div>
    </div>

    <!-- the plumbing, for whoever can repair it -->
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
      <div class="mt-3 flex flex-col divide-y divide-outline-gray-1 text-p-sm">
        <div class="flex justify-between gap-4 py-2">
          <span class="text-ink-gray-5">{{ __('Meta app') }}</span>
          <span class="text-right text-ink-gray-8">
            {{ status.data?.app_id || __('not set') }}
            <span v-if="managed" class="block text-ink-gray-5">
              {{
                status.data?.is_hub
                  ? __('provided centrally; this site owns its webhook')
                  : __('provided centrally, webhook included')
              }}
            </span>
          </span>
        </div>
        <div class="flex justify-between gap-4 py-2">
          <span class="text-ink-gray-5">{{ __('Real-time leads') }}</span>
          <span class="text-right text-ink-gray-8">
            <template v-if="!status.data?.is_hub">
              {{ __('through the hub') }}
              <span class="block text-ink-gray-5">{{ status.data?.hub }}</span>
            </template>
            <template v-else-if="webhook.data?.configured">
              {{ __('webhook registered on the app') }}
            </template>
            <template v-else>{{ __('webhook not registered') }}</template>
          </span>
        </div>
        <!--
          Whether Meta has ever called the webhook, and what happened to the
          call. Without it, "Facebook is not sending" and "we refused it" look
          identical from here — and leads arriving late through the hourly
          reconciliation look exactly like leads arriving in real time.
        -->
        <div v-if="connected" class="flex justify-between gap-4 py-2">
          <span class="text-ink-gray-5">{{ __('Last call from Meta') }}</span>
          <span
            class="text-right"
            :class="
              status.data?.last_webhook_seen
                ? 'text-ink-gray-8'
                : 'text-ink-amber-6'
            "
          >
            <template v-if="status.data?.last_webhook_seen">
              {{ status.data.last_webhook_seen }}
              <span
                v-if="status.data.last_webhook_outcome"
                class="block text-ink-gray-5"
              >
                {{ status.data.last_webhook_outcome }}
              </span>
            </template>
            <template v-else>
              {{
                __(
                  'never — leads arrive only through the hourly check, not in real time',
                )
              }}
            </template>
          </span>
        </div>
        <div
          v-if="connected && status.data?.user_token_expires_at"
          class="flex justify-between gap-4 py-2"
        >
          <span class="text-ink-gray-5">{{ __('Token valid until') }}</span>
          <span class="text-ink-gray-8">
            {{ status.data.user_token_expires_at }}
          </span>
        </div>
        <div
          v-if="connected && status.data?.granted_scopes?.length"
          class="flex flex-col gap-1 py-2"
        >
          <span class="text-ink-gray-5">{{ __('Permissions granted') }}</span>
          <span class="font-mono text-p-xs text-ink-gray-7">
            {{ status.data.granted_scopes.join(' · ') }}
          </span>
        </div>
      </div>
    </details>

    <!-- disconnecting stops the leads and the publishing: say so before doing
         it, because reconnecting means going through Facebook again -->
    <Dialog
      v-model="confirmingDisconnect"
      :options="{
        title: __('Disconnect Facebook?'),
        actions: [
          {
            label: __('Disconnect'),
            theme: 'red',
            variant: 'solid',
            loading: disconnecting,
            onClick: disconnect,
          },
        ],
      }"
    >
      <template #body-content>
        <p class="text-p-base text-ink-gray-6">
          {{
            __(
              'The CRM stops importing leads from every Page, unsubscribes them from Facebook and forgets their tokens. The Social Planner cannot publish either until you connect again.',
            )
          }}
        </p>
      </template>
    </Dialog>
  </div>
</template>

<script setup>
import FacebookIcon from '@/components/Icons/FacebookIcon.vue'
import { openOAuthPopup, onOAuthResult } from '@/composables/oauthPopup'
import { formatDate } from '@/utils'
import { tokenExpiry } from '@/utils/metaConnection'
import { createResource, LoadingIndicator, Switch, toast } from 'frappe-ui'
import { ref, computed, watch, onUnmounted } from 'vue'

// loaded once by the page around the tabs, which also shows its state
const props = defineProps({
  status: { type: Object, required: true },
})

const emit = defineEmits(['navigate'])

const metaError = ref(
  new URLSearchParams(window.location.search).get('meta_error') || '',
)
const appForm = ref({ app_id: '', app_secret: '' })

const connected = computed(() => Boolean(props.status.data?.connected))
// what the server decided to send: the technical half only goes to
// administrators, so this is also what the screen shows
const isAdmin = computed(() => Boolean(props.status.data?.is_admin))
// the app (and its single webhook) is provided centrally: no developer setup
const managed = computed(() => Boolean(props.status.data?.managed))
const appReady = computed(() => Boolean(props.status.data?.app_ready))
const missingScopes = computed(() => props.status.data?.missing_scopes || [])
const pageCount = computed(() => props.status.data?.page_count || 0)
const syncing = computed(() => Boolean(props.status.data?.syncing))

const expiry = computed(() =>
  tokenExpiry(props.status.data?.user_token_expires_at),
)
// written in the site's time zone, like every date the server sends
const expiryDate = computed(() =>
  expiry.value
    ? formatDate(props.status.data.user_token_expires_at, 'D MMM YYYY')
    : '',
)

watch(
  () => props.status.data?.app_id,
  (appId) => {
    if (appId && !appForm.value.app_id) appForm.value.app_id = appId
  },
  { immediate: true },
)

// Only an administrator can read the webhook, and only an administrator can do
// anything about it — so for anybody else it is never asked for.
const webhook = createResource({
  url: 'crm.integrations.meta.api.get_webhook_subscription',
})
watch(
  isAdmin,
  (admin) => {
    if (admin && !webhook.fetched && !webhook.loading) webhook.fetch()
  },
  { immediate: true },
)
// broken only where it can be fixed: on a client site the hub owns it
const webhookBroken = computed(
  () =>
    isAdmin.value &&
    Boolean(props.status.data?.is_hub) &&
    appReady.value &&
    webhook.data &&
    !webhook.data.configured,
)

const confirmingDisconnect = ref(false)
const disconnecting = ref(false)
const configuringWebhook = ref(false)
const savingApp = ref(false)
const refreshing = ref(false)
const choosing = ref(false)
const busyPage = ref('')

const PAGE_SIZE = 20

const search = ref('')
const limit = ref(PAGE_SIZE)

// the Pages live in their own paginated call: an agency account can hold
// hundreds, and none of them belong in the status payload
const pageList = createResource({
  url: 'crm.integrations.meta.api.list_pages',
  makeParams: () => ({ start: 0, limit: limit.value, search: search.value }),
  auto: true,
})

const pages = computed(() => pageList.data?.pages || [])
const total = computed(() => pageList.data?.total || 0)
const hidden = computed(() => pageList.data?.hidden || 0)
// searching a handful of Pages is worse than reading them
const showSearch = computed(
  () => total.value > PAGE_SIZE || Boolean(search.value),
)

function loadMore() {
  limit.value += PAGE_SIZE
  pageList.reload()
}

let searchTimer = null
watch(search, () => {
  clearTimeout(searchTimer)
  limit.value = PAGE_SIZE
  searchTimer = setTimeout(() => pageList.reload(), 250)
})

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
    pageList.reload()
    pollWhileSyncing()
  }, 3000)
}
watch(syncing, (now, before) => {
  pollWhileSyncing()
  // the last poll came back with the job done: show what it found
  if (before && !now) pageList.reload()
})
pollWhileSyncing()
onUnmounted(() => {
  clearTimeout(pollTimer)
  clearTimeout(searchTimer)
})

function togglePage(page, enabled) {
  busyPage.value = page.name
  createResource({
    url: 'crm.integrations.meta.api.set_page_sync',
    params: { page_id: page.name, enabled: enabled ? 1 : 0 },
    auto: true,
    onSuccess: () => {
      busyPage.value = ''
      toast.success(enabled ? __('Leads enabled') : __('Leads disabled'))
      pageList.reload()
    },
    onError: (e) => {
      busyPage.value = ''
      toast.error(e.messages?.[0] || __('Could not change the page'))
      pageList.reload()
    },
  })
}

function saveApp() {
  savingApp.value = true
  createResource({
    url: 'crm.integrations.meta.api.save_app_settings',
    params: {
      app_id: appForm.value.app_id,
      app_secret: appForm.value.app_secret,
    },
    auto: true,
    onSuccess: (data) => {
      savingApp.value = false
      appForm.value.app_secret = ''
      if (data?.webhook?.configured) {
        toast.success(
          __('Saved — webhook configured on the Meta app automatically'),
        )
        webhook.data = data.webhook
      } else {
        toast.success(__('Saved'))
        webhook.reload()
      }
      props.status.reload()
    },
    onError: (e) => {
      savingApp.value = false
      toast.error(e.messages?.[0] || __('Failed to save'))
    },
  })
}

function configureWebhook() {
  configuringWebhook.value = true
  createResource({
    url: 'crm.integrations.meta.api.configure_webhook',
    auto: true,
    onSuccess: (data) => {
      configuringWebhook.value = false
      webhook.data = data
      if (data.configured)
        toast.success(__('Webhook configured on the Meta app'))
      else toast.error(data.error || __('Webhook not configured'))
    },
    onError: (e) => {
      configuringWebhook.value = false
      toast.error(e.messages?.[0] || __('Could not configure the webhook'))
    },
  })
}

// the page around the tabs reloads the connection's state; this tab says how
// it went and reads its Pages again
onOAuthResult('meta', ({ error }) => {
  choosing.value = false
  metaError.value = error
  if (error) toast.error(error)
  else toast.success(__('Facebook connected'))
  pageList.reload()
})

function connect(rerequest = false) {
  if (rerequest) choosing.value = true
  createResource({
    url: 'crm.integrations.meta.oauth.get_login_url',
    params: { rerequest: rerequest ? 1 : 0 },
    auto: true,
    onSuccess: (data) => openOAuthPopup(data.login_url, 'crm-meta-oauth'),
    onError: (e) => {
      choosing.value = false
      toast.error(e.messages?.[0] || __('Failed to start login'))
    },
  })
}

function disconnect() {
  disconnecting.value = true
  createResource({
    url: 'crm.integrations.meta.api.disconnect',
    auto: true,
    onSuccess: () => {
      disconnecting.value = false
      confirmingDisconnect.value = false
      toast.success(__('Disconnected'))
      props.status.reload()
      pageList.reload()
    },
    onError: (e) => {
      disconnecting.value = false
      toast.error(e.messages?.[0] || __('Could not disconnect'))
    },
  })
}

function refreshPages() {
  refreshing.value = true
  createResource({
    url: 'crm.integrations.meta.api.refresh_pages',
    auto: true,
    onSuccess: () => {
      refreshing.value = false
      toast.success(__('Reading your Pages from Facebook…'))
      props.status.reload()
    },
    onError: (e) => {
      refreshing.value = false
      toast.error(e.messages?.[0] || __('Failed to refresh'))
    },
  })
}
</script>
