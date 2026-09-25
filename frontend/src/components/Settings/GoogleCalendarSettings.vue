<template>
  <div class="flex h-full flex-col gap-6 py-8 px-6 text-ink-gray-8">
    <div class="flex flex-col gap-1 px-2">
      <h2 class="flex gap-2 text-2xl-semibold leading-none h-5">
        {{ __('Google Calendar') }}
      </h2>
      <p class="text-p-base text-ink-gray-6">
        {{
          __(
            'Connect your Google account to see your CRM appointments in Google Calendar, on your phone too. It only goes one way: the CRM writes, Google shows.',
          )
        }}
      </p>
    </div>

    <div class="flex flex-1 flex-col gap-4 overflow-y-auto px-2">
      <div
        class="flex items-center justify-between gap-3 rounded-lg border border-outline-gray-2 p-4"
      >
        <div class="flex flex-col">
          <span class="text-p-base-medium text-ink-gray-7">
            {{
              status.data?.connected
                ? __('Your calendar is connected')
                : __('Calendar not connected')
            }}
          </span>
          <span class="text-p-sm text-ink-gray-5">
            {{
              status.data?.can_connect
                ? __(
                    'A Google window will ask you to choose the account and allow access.',
                  )
                : __('Google is not configured yet — ask your provider.')
            }}
          </span>
          <span v-if="googleError" class="text-p-sm text-ink-red-5">{{
            googleError
          }}</span>
        </div>
        <div class="flex gap-2">
          <Button
            :variant="status.data?.connected ? 'outline' : 'solid'"
            :disabled="!status.data?.can_connect"
            :loading="connecting"
            :label="
              status.data?.connected
                ? __('Reconnect')
                : __('Connect Google Calendar')
            "
            @click="connect"
          />
          <Button
            v-if="status.data?.connected"
            variant="ghost"
            :label="__('Disconnect')"
            @click="disconnect"
          />
        </div>
      </div>

      <div
        v-if="sync"
        class="flex flex-col gap-3 rounded-lg border border-outline-gray-2 p-4"
      >
        <div class="flex items-start justify-between gap-3">
          <div class="flex flex-col">
            <span class="text-p-base-medium text-ink-gray-7">
              {{ __('Your appointments in Google') }}
            </span>
            <span class="text-p-sm text-ink-gray-5">{{ syncState }}</span>
          </div>
          <div class="flex shrink-0 gap-2">
            <Button
              variant="ghost"
              icon="lucide-external-link"
              :tooltip="__('Open Google Calendar')"
              @click="openGoogle"
            />
            <Button
              variant="subtle"
              icon-left="lucide-refresh-cw"
              :label="__('Sync now')"
              :disabled="!sync.active"
              :loading="syncing"
              @click="syncNow"
            />
          </div>
        </div>
        <p v-if="sync.error" class="text-p-sm text-ink-red-5">
          {{ sync.error }}
        </p>
        <ul
          class="flex list-disc flex-col gap-1 pl-4 text-p-sm text-ink-gray-6"
        >
          <li>
            {{
              __(
                'They go into a calendar of their own in your Google account, "{0}": you can colour it, hide it or share it.',
                [sync.calendar],
              )
            }}
          </li>
          <li>
            {{
              __(
                'Only the appointments you are on. New, moved and cancelled ones follow within a minute.',
              )
            }}
          </li>
          <li>
            {{
              __(
                'Changes made in Google do not come back to the CRM, and are overwritten at the next update.',
              )
            }}
          </li>
          <li>
            {{ __('Clients are not invited: Google sends them nothing.') }}
          </li>
        </ul>
      </div>

      <p v-if="status.data?.connected" class="text-p-sm text-ink-gray-5">
        {{
          __(
            'Disconnecting only stops the sync: the appointments already created in Google stay where they are.',
          )
        }}
      </p>
    </div>
  </div>
</template>

<script setup>
import { createResource, toast } from 'frappe-ui'
import { computed, onUnmounted, ref } from 'vue'
import { openOAuthPopup, onOAuthResult } from '@/composables/oauthPopup'
import { timeAgo } from '@/utils'

const googleError = ref(
  new URLSearchParams(window.location.search).get('google_error') || '',
)
const connecting = ref(false)
const syncing = ref(false)

const status = createResource({
  url: 'crm.integrations.google.api.get_status',
  auto: true,
})

const sync = computed(() => status.data?.sync || null)

const syncState = computed(() => {
  const state = sync.value
  if (!state) return ''
  if (!state.active) return __('Paused: connect again to start it again.')
  if (!state.last_sync) {
    return state.error
      ? __('The first copy did not go through.')
      : __('Getting the calendar ready: the first copy starts within a minute.')
  }
  return __('{0} appointments in the coming months · updated {1}', [
    state.events,
    timeAgo(state.last_sync),
  ])
})

// The copy runs in the background: after asking for one, look again every few
// seconds for a minute, until it reports back.
let watching = null

function watchTheCopy() {
  clearInterval(watching)
  const before = { last: sync.value?.last_sync, error: sync.value?.error }
  let looks = 0
  watching = setInterval(async () => {
    looks += 1
    await status.reload()
    const state = sync.value
    const reported =
      state &&
      ((state.last_sync && state.last_sync !== before.last) ||
        (state.error && state.error !== before.error))
    if (reported || looks >= 12) clearInterval(watching)
  }, 5000)
}

onUnmounted(() => clearInterval(watching))

onOAuthResult('google', async ({ error }) => {
  connecting.value = false
  googleError.value = error
  if (error) toast.error(error)
  else toast.success(__('Calendar connected'))
  await status.reload()
  if (!error) watchTheCopy()
})

function connect() {
  connecting.value = true
  createResource({
    url: 'crm.integrations.google.oauth.get_login_url',
    auto: true,
    onSuccess: (data) => openOAuthPopup(data.login_url, 'crm-google-oauth'),
    onError: (e) => {
      connecting.value = false
      toast.error(e.messages?.[0] || __('Could not start the connection'))
    },
  })
}

function syncNow() {
  syncing.value = true
  createResource({
    url: 'crm.integrations.google.api.sync_now',
    auto: true,
    onSuccess: () => {
      syncing.value = false
      toast.success(__('Sync started: your appointments are on their way'))
      watchTheCopy()
    },
    onError: (e) => {
      syncing.value = false
      toast.error(e.messages?.[0] || __('Could not start the sync'))
    },
  })
}

function openGoogle() {
  window.open('https://calendar.google.com/calendar/r', '_blank', 'noopener')
}

function disconnect() {
  createResource({
    url: 'crm.integrations.google.api.disconnect',
    auto: true,
    onSuccess: () => {
      toast.success(__('Calendar disconnected'))
      status.reload()
    },
    onError: (e) => toast.error(e.messages?.[0] || __('Failed to disconnect')),
  })
}
</script>
