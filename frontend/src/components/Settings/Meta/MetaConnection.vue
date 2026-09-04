<template>
  <div class="flex h-full flex-col gap-6 overflow-y-auto py-8 px-6 text-ink-gray-8">
    <div class="flex flex-col gap-1 px-2">
      <h2 class="flex gap-2 text-2xl-semibold leading-none h-5">
        {{ __('Meta connection') }}
      </h2>
      <p class="text-p-base text-ink-gray-6">
        {{
          __(
            'One connection to Facebook and Instagram. It powers lead forms, the Social Planner and WhatsApp.',
          )
        }}
      </p>
    </div>

    <div class="flex flex-col gap-4 px-2">
      <div
        v-if="managed"
        class="flex items-center gap-2 rounded-lg bg-surface-gray-1 p-3 text-p-sm text-ink-gray-6"
      >
        <FeatherIcon name="shield-check" class="size-4 shrink-0 text-ink-gray-5" />
        {{
          isHub
            ? __('The Meta app is provided centrally; this site owns its webhook.')
            : __('The Meta app and its webhook are managed for you — just connect your account.')
        }}
      </div>

      <!-- App ID/secret only when this site owns its own Meta app; when the app
           is provided centrally there is nothing to type here -->
      <div v-if="!managed" class="rounded-lg border border-outline-gray-2 p-4">
        <div class="mb-2 text-p-base-medium text-ink-gray-7">
          {{ __('Meta App (developers.facebook.com)') }}
        </div>
        <div class="grid grid-cols-2 gap-3">
          <FormControl v-model="appForm.app_id" type="text" :label="__('App ID')" />
          <FormControl
            v-model="appForm.app_secret"
            type="password"
            :label="__('App Secret')"
            :placeholder="status.data?.has_app_secret ? __('•••••• (saved — type to replace)') : ''"
          />
        </div>
        <div class="mt-3 flex items-center gap-2">
          <Button :label="__('Save app')" variant="solid" @click="saveApp" />
        </div>
      </div>

      <!-- The webhook configures itself and belongs to the plumbing, not to the
           screen: it appears only when it is broken, with the button that fixes
           it. Nothing to copy by hand. -->
      <div
        v-if="webhookBroken"
        class="flex items-center justify-between gap-3 rounded-lg border border-outline-amber-2 bg-surface-amber-1 p-4"
      >
        <div class="flex flex-col">
          <span class="text-p-base-medium text-ink-gray-7">
            {{ __('Real-time leads are off') }}
          </span>
          <span class="text-p-sm text-ink-gray-6">
            {{ __('Meta is not notifying this site yet, so leads arrive with the hourly check instead of instantly.') }}
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
      <div class="flex items-center justify-between rounded-lg border border-outline-gray-2 p-4">
        <div class="flex flex-col">
          <span class="text-p-base-medium text-ink-gray-7">
            {{
              status.data?.connected
                ? __('Connected as {0}', [status.data.connected_user_name])
                : __('Connect Facebook')
            }}
          </span>
          <span
            v-if="status.data?.connected && status.data.user_token_expires_at"
            class="text-p-sm text-ink-gray-5"
          >
            {{ __('Token valid until') }}: {{ status.data.user_token_expires_at }}
          </span>
          <span v-if="metaError" class="text-p-sm text-ink-red-5">{{ metaError }}</span>
        </div>
        <div class="flex gap-2">
          <Button
            v-if="status.data?.connected"
            :label="__('Refresh pages')"
            :loading="refreshing"
            @click="refreshPages"
          />
          <Button
            :variant="status.data?.connected ? 'outline' : 'solid'"
            :label="status.data?.connected ? __('Reconnect') : __('Connect with Facebook')"
            @click="connect()"
          />
          <Button
            v-if="status.data?.connected"
            variant="ghost"
            :label="__('Disconnect')"
            @click="disconnect"
          />
        </div>
      </div>

      <!-- which Pages Facebook actually shared: the dialog, not the CRM,
           decides this, and granting none still reports a successful login -->
      <div
        v-if="status.data?.connected"
        class="flex flex-col gap-3 rounded-lg border border-outline-gray-2 p-4"
      >
        <div class="flex items-center justify-between gap-3">
          <span class="text-p-base-medium text-ink-gray-7">
            {{ __('Pages shared with the CRM') }}
          </span>
          <Button
            :label="__('Choose pages')"
            :loading="choosing"
            @click="connect(true)"
          />
        </div>

        <div v-if="syncing" class="flex items-center gap-2 text-p-sm text-ink-gray-6">
          <LoadingIndicator class="size-4" />
          {{ __('Reading your Pages from Facebook — this can take a minute on an account with many.') }}
        </div>

        <div v-else-if="pages.length" class="flex flex-col gap-1">
          <p class="mb-1 text-p-sm text-ink-gray-5">
            {{ __('Turn on the Pages whose leads should reach this CRM.') }}
          </p>
          <div
            v-for="page in pages"
            :key="page.name"
            class="flex items-center gap-3 rounded-md px-2 py-1.5 hover:bg-surface-gray-1"
          >
            <Switch
              size="sm"
              :modelValue="Boolean(page.sync_enabled)"
              :disabled="busyPage === page.name || page.can_sync_leads === false"
              @update:modelValue="(value) => togglePage(page, value)"
            />
            <div class="flex min-w-0 flex-1 flex-col">
              <span class="truncate text-p-sm text-ink-gray-8">
                {{ page.page_name || page.name }}
              </span>
              <span v-if="page.instagram_username" class="text-p-xs text-ink-gray-5">
                {{ __('Instagram') }}: @{{ page.instagram_username }}
              </span>
              <span v-if="page.can_sync_leads === false" class="text-p-xs text-ink-amber-6">
                {{ __('Not authorised for leads — reconnect and tick this Page') }}
              </span>
            </div>
          </div>
          <span class="mt-2 text-p-sm text-ink-gray-5">
            {{
              __(
                'Missing one? "Choose pages" reopens the Facebook window: without it Facebook skips the picker and keeps the earlier choice.',
              )
            }}
          </span>
        </div>

        <div v-else-if="!syncing" class="flex flex-col gap-1 text-p-sm">
          <span class="text-ink-red-5">
            {{ __('Facebook shared no Page with the CRM.') }}
          </span>
          <span class="text-ink-gray-5">
            {{
              __(
                'The login worked but no Page was selected. Press "Choose pages" and tick the Pages you want in the Facebook window — you must be an administrator of them.',
              )
            }}
          </span>
        </div>
      </div>

      <!-- where the connection is used -->
      <div v-if="status.data?.connected" class="flex flex-wrap gap-2">
        <Button :label="__('Lead forms')" @click="go('Lead forms')" />
        <Button :label="__('Social profiles')" @click="go('Social profiles')" />
        <Button :label="__('WhatsApp')" @click="go('WhatsApp')" />
      </div>
    </div>
  </div>
</template>

<script setup>
import { activeSettingsPage } from '@/composables/settings'
import {
  createResource,
  FeatherIcon,
  FormControl,
  LoadingIndicator,
  Switch,
  toast,
} from 'frappe-ui'
import { ref, computed, watch, onUnmounted } from 'vue'
import { openOAuthPopup, onOAuthResult } from '@/composables/oauthPopup'

const metaError = ref(new URLSearchParams(window.location.search).get('meta_error') || '')
const appForm = ref({ app_id: '', app_secret: '' })

const status = createResource({
  url: 'crm.integrations.meta.api.get_status',
  auto: true,
  onSuccess: (data) => {
    appForm.value.app_id = data.app_id
  },
})

// the app (and its single webhook) is provided centrally: hide developer setup
const managed = computed(() => Boolean(status.data?.managed))
// only the site that owns the app's callbacks configures the webhook
const isHub = computed(() => Boolean(status.data?.is_hub))

const webhook = createResource({
  url: 'crm.integrations.meta.api.get_webhook_subscription',
  auto: true,
})

const configuringWebhook = ref(false)
const refreshing = ref(false)
const choosing = ref(false)
const busyPage = ref('')

const pages = computed(() => status.data?.pages || [])
// only the site that owns the app's callbacks can do anything about it
const webhookBroken = computed(
  () =>
    isHub.value &&
    webhook.data &&
    !(webhook.data.configured && webhook.data.matches_site),
)
const syncing = computed(() => Boolean(status.data?.syncing))

// The sync runs in a background job, so the screen has to keep coming back for
// it. `watch` alone fires only when the flag CHANGES: after one reload with the
// job still running the value stayed true, nothing rescheduled, and the screen
// sat on "reading your Pages" until someone reloaded by hand.
let pollTimer = null
function pollWhileSyncing() {
  clearTimeout(pollTimer)
  if (!syncing.value) return
  pollTimer = setTimeout(() => {
    status.reload()
    pollWhileSyncing()
  }, 3000)
}
watch(syncing, pollWhileSyncing, { immediate: true })
onUnmounted(() => clearTimeout(pollTimer))

function togglePage(page, enabled) {
  busyPage.value = page.name
  createResource({
    url: 'crm.integrations.meta.api.set_page_sync',
    params: { page_id: page.name, enabled: enabled ? 1 : 0 },
    auto: true,
    onSuccess: () => {
      busyPage.value = ''
      toast.success(enabled ? __('Leads enabled') : __('Leads disabled'))
      status.reload()
    },
    onError: (e) => {
      busyPage.value = ''
      toast.error(e.messages?.[0] || __('Could not change the page'))
      status.reload()
    },
  })
}

function go(page) {
  activeSettingsPage.value = page
}

function saveApp() {
  createResource({
    url: 'crm.integrations.meta.api.save_app_settings',
    params: { app_id: appForm.value.app_id, app_secret: appForm.value.app_secret },
    auto: true,
    onSuccess: (data) => {
      appForm.value.app_secret = ''
      if (data?.webhook?.configured) {
        toast.success(__('Saved — webhook configured on the Meta app automatically'))
        webhook.data = data.webhook
      } else {
        toast.success(__('Saved'))
        webhook.reload()
      }
      status.reload()
    },
    onError: (e) => toast.error(e.messages?.[0] || __('Failed to save')),
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
      data.configured
        ? toast.success(__('Webhook configured on the Meta app'))
        : toast.error(data.error || __('Webhook not configured'))
    },
    onError: (e) => {
      configuringWebhook.value = false
      toast.error(e.messages?.[0] || __('Could not configure the webhook'))
    },
  })
}

onOAuthResult('meta', ({ error }) => {
  choosing.value = false
  metaError.value = error
  error ? toast.error(error) : toast.success(__('Facebook connected'))
  status.reload()
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
  createResource({
    url: 'crm.integrations.meta.api.disconnect',
    auto: true,
    onSuccess: () => {
      toast.success(__('Disconnected'))
      status.reload()
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
      status.reload()
    },
    onError: (e) => {
      refreshing.value = false
      toast.error(e.messages?.[0] || __('Failed to refresh'))
    },
  })
}
</script>
