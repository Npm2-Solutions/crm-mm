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

      <!-- the app itself: hidden when it is provided centrally and this site
           does not own its callbacks -->
      <div v-if="!managed || isHub" class="rounded-lg border border-outline-gray-2 p-4">
        <div v-if="!managed" class="mb-2 text-p-base-medium text-ink-gray-7">
          {{ __('Meta App (developers.facebook.com)') }}
        </div>
        <div v-else class="mb-2 text-p-base-medium text-ink-gray-7">
          {{ __('Webhook (this site receives the leads of every connected site)') }}
        </div>
        <div v-if="!managed" class="grid grid-cols-2 gap-3">
          <FormControl v-model="appForm.app_id" type="text" :label="__('App ID')" />
          <FormControl
            v-model="appForm.app_secret"
            type="password"
            :label="__('App Secret')"
            :placeholder="status.data?.has_app_secret ? __('•••••• (saved — type to replace)') : ''"
          />
        </div>
        <div v-if="!managed" class="mt-3 flex items-center gap-2">
          <Button :label="__('Save app')" variant="solid" @click="saveApp" />
        </div>
        <div
          v-if="status.data?.webhook_url"
          class="mt-3 flex flex-col gap-2 text-p-sm text-ink-gray-6"
        >
          <div class="flex items-center gap-2">
            <span class="shrink-0 font-medium">{{ __('Webhook') }}:</span>
            <Badge
              v-if="webhook.data?.configured && webhook.data?.matches_site"
              :label="__('Configured automatically')"
              theme="green"
              size="sm"
            />
            <template v-else>
              <Badge :label="__('Not configured')" theme="orange" size="sm" />
              <Button
                size="sm"
                :label="__('Configure automatically')"
                :loading="configuringWebhook"
                @click="configureWebhook"
              />
            </template>
          </div>
          <span v-if="webhook.data?.error" class="text-ink-red-5">{{ webhook.data.error }}</span>
          <details>
            <summary class="cursor-pointer text-ink-gray-5">
              {{ __('Manual configuration (fallback)') }}
            </summary>
            <div class="mt-1 flex flex-col gap-1">
              <div class="flex items-center gap-2">
                <span class="shrink-0 font-medium">{{ __('Webhook URL') }}:</span>
                <span class="truncate">{{ status.data.webhook_url }}</span>
                <Button variant="ghost" icon="lucide-copy" @click="copy(status.data.webhook_url)" />
              </div>
              <div class="flex items-center gap-2">
                <span class="shrink-0 font-medium">{{ __('Verify token') }}:</span>
                <span class="truncate">{{ status.data.webhook_verify_token }}</span>
                <Button
                  variant="ghost"
                  icon="lucide-copy"
                  @click="copy(status.data.webhook_verify_token)"
                />
              </div>
              <span class="text-ink-gray-5">
                {{ __('In the app: Webhooks → Page → subscribe to "leadgen".') }}
              </span>
            </div>
          </details>
        </div>
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
          <span v-if="status.data?.connected" class="text-p-sm text-ink-gray-5">
            {{ __('Token valid until') }}: {{ status.data.user_token_expires_at || '—' }}
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

        <div v-if="pages.length" class="flex flex-col gap-1">
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
              :disabled="busyPage === page.name"
              @update:modelValue="(value) => togglePage(page, value)"
            />
            <div class="flex min-w-0 flex-1 flex-col">
              <span class="truncate text-p-sm text-ink-gray-8">
                {{ page.page_name || page.name }}
              </span>
              <span v-if="page.instagram_username" class="text-p-xs text-ink-gray-5">
                {{ __('Instagram') }}: @{{ page.instagram_username }}
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

        <div v-else class="flex flex-col gap-1 text-p-sm">
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
import { Badge, createResource, FeatherIcon, FormControl, Switch, toast } from 'frappe-ui'
import { ref, computed, onMounted, onUnmounted } from 'vue'

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

function copy(text) {
  navigator.clipboard?.writeText(text)
  toast.success(__('Copied'))
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

// The login runs in a popup so this page keeps its state: navigating the whole
// CRM to facebook.com and back reloads the app, and a failure on the way had
// nowhere to be shown. The popup posts its outcome back and closes.
function openLoginPopup(url) {
  const width = 620
  const height = 720
  const left = window.screenX + (window.outerWidth - width) / 2
  const top = window.screenY + (window.outerHeight - height) / 2
  const popup = window.open(
    url,
    'crm-meta-oauth',
    `popup=1,width=${width},height=${height},left=${left},top=${top}`,
  )
  if (!popup) {
    // popup blocked: fall back to navigating, the callback page handles it
    window.location.href = url
    return
  }
  popup.focus()
}

function onOAuthMessage(event) {
  if (event.origin !== window.location.origin) return
  if (event.data?.source !== 'crm-meta-oauth') return
  choosing.value = false
  if (event.data.error) {
    metaError.value = event.data.error
    toast.error(event.data.error)
  } else {
    metaError.value = ''
    toast.success(__('Facebook connected'))
  }
  status.reload()
}

onMounted(() => window.addEventListener('message', onOAuthMessage))
onUnmounted(() => window.removeEventListener('message', onOAuthMessage))

function connect(rerequest = false) {
  if (rerequest) choosing.value = true
  createResource({
    url: 'crm.integrations.meta.oauth.get_login_url',
    params: { rerequest: rerequest ? 1 : 0 },
    auto: true,
    onSuccess: (data) => openLoginPopup(data.login_url),
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
      toast.success(__('Pages refreshed'))
    },
    onError: (e) => {
      refreshing.value = false
      toast.error(e.messages?.[0] || __('Failed to refresh'))
    },
  })
}
</script>
