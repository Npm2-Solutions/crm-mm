<template>
  <div class="flex h-full flex-col gap-6 py-8 px-6 text-ink-gray-8">
    <div class="flex flex-col gap-1 px-2">
      <h2 class="flex gap-2 text-2xl-semibold leading-none h-5">
        {{ __('WhatsApp') }}
      </h2>
      <p class="text-p-base text-ink-gray-6">
        {{
          __(
            'Connect your WhatsApp Business number: chats stay on your phone and appear here too.',
          )
        }}
      </p>
    </div>

    <div class="flex-1 overflow-y-auto px-2">
      <div
        v-if="status.data && !status.data.installed"
        class="rounded-lg border border-dashed border-outline-gray-2 p-6 text-center text-p-base text-ink-gray-5"
      >
        {{ __('The WhatsApp app is not installed on this site yet.') }}
      </div>

      <template v-else>
        <!-- which Meta app signs these calls. A borrowed id is legitimate (one
             app for Facebook and WhatsApp) and also how an agency discovers,
             weeks later, that its WhatsApp calls went out as the Facebook app -->
        <div
          v-if="status.data?.app?.app_id"
          class="mb-4 flex items-center gap-2 rounded-lg bg-surface-gray-1 p-3 text-p-sm text-ink-gray-6"
        >
          <span>{{ __('Meta app in use') }}:</span>
          <span class="text-ink-gray-8">{{ status.data.app.app_id }}</span>
          <span
            v-if="status.data.app.borrowed_from_meta_app"
            class="text-ink-amber-6"
          >
            {{ __('— the Facebook app, because no WhatsApp app is set') }}
          </span>
        </div>

        <!-- and which login configuration it sends. An app can hold several,
             and the choice decides how long the client's token lives and
             whether they are asked for a business portfolio. Meta's dashboard
             shows what is selected there, which is not the same as what this
             CRM sends — so say what this CRM sends. -->
        <div
          v-if="status.data?.signup_config?.config_id"
          class="mb-4 flex flex-wrap items-center gap-2 rounded-lg bg-surface-gray-1 p-3 text-p-sm text-ink-gray-6"
        >
          <span>{{ __('Embedded Signup configuration') }}:</span>
          <span class="text-ink-gray-8">{{
            status.data.signup_config.config_id
          }}</span>
          <span class="text-ink-gray-5">
            {{
              status.data.signup_config.from_bench
                ? __('— from the bench config')
                : __('— set here, in Settings')
            }}
          </span>
        </div>

        <!-- what Meta said, last few attempts. Only the hub has these rows: a
             client site's onboarding is logged where the page lives, not where
             the CRM does. -->
        <div
          v-if="attempts.data?.is_hub && attempts.data?.attempts?.length"
          class="mb-4 rounded-lg border border-outline-gray-2 p-3"
        >
          <div class="mb-2 text-p-sm-medium text-ink-gray-7">
            {{ __('Last connection attempts') }}
          </div>
          <div class="flex flex-col divide-y divide-outline-gray-1">
            <div
              v-for="row in attempts.data.attempts"
              :key="row.creation"
              class="flex flex-col gap-0.5 py-1.5 text-p-sm"
            >
              <div class="flex flex-wrap items-center gap-2">
                <span class="text-ink-gray-5">{{ row.creation }}</span>
                <span
                  :class="
                    row.outcome === 'Error'
                      ? 'text-ink-red-5'
                      : row.outcome === 'Completed'
                        ? 'text-ink-green-5'
                        : 'text-ink-gray-7'
                  "
                >
                  {{ row.event || row.outcome }}
                </span>
                <span v-if="row.current_step" class="text-ink-gray-5">
                  {{ row.current_step }}
                </span>
              </div>
              <div v-if="row.error_message" class="text-ink-red-5">
                {{ row.error_message }}
              </div>
              <!-- the two values Meta asks for when you open a support ticket -->
              <div
                v-if="row.error_id || row.session_id"
                class="text-p-xs text-ink-gray-4"
              >
                {{
                  [
                    row.error_code && `code ${row.error_code}`,
                    row.error_id && `error ${row.error_id}`,
                    row.session_id && `session ${row.session_id}`,
                  ]
                    .filter(Boolean)
                    .join(' · ')
                }}
              </div>
            </div>
          </div>
        </div>

        <!-- connect -->
        <div
          class="mb-6 flex items-center justify-between gap-3 rounded-lg border border-outline-gray-2 p-4"
        >
          <div class="flex flex-col">
            <span class="text-p-base-medium text-ink-gray-7">
              {{
                status.data?.connected
                  ? __('WhatsApp is connected')
                  : __('No number connected yet')
              }}
            </span>
            <span class="text-p-sm text-ink-gray-5">
              {{
                status.data?.can_connect
                  ? __(
                      'You will scan a QR code with the WhatsApp Business app on your phone.',
                    )
                  : __('Two things have to exist first — see below.')
              }}
            </span>
          </div>
          <Button
            :variant="status.data?.connected ? 'outline' : 'solid'"
            :disabled="!status.data?.can_connect"
            :loading="connecting"
            :label="
              status.data?.connected
                ? __('Connect another number')
                : __('Connect WhatsApp')
            "
            @click="connect"
          />
        </div>

        <!-- numbers -->
        <!-- the WhatsApp app is a different Meta app, so its webhook does not come
             along with the Facebook one: it appears here only when it is not set
             or set short of the fields the CRM needs, with the button that fixes it.
             Meta never adds a field to an existing subscription by itself, so
             "configured" alone was a half-truth: the webhook could be registered
             and still never mention an onboarding or a number's own messages. -->
        <div
          v-if="webhook.data?.is_hub && !webhook.data?.complete"
          class="mb-4 flex flex-col gap-3 rounded-lg border border-outline-amber-2 bg-surface-amber-1 p-4"
        >
          <div class="flex items-center justify-between gap-3">
            <div class="flex flex-col">
              <span class="text-p-base-medium text-ink-gray-7">
                {{
                  webhook.data?.configured
                    ? __('Meta is notifying this hub, but not about everything')
                    : __('Meta is not notifying this hub yet')
                }}
              </span>
              <span class="text-p-sm text-ink-gray-6">
                {{
                  webhook.data?.configured
                    ? __('These are missing: {0}', [
                        (webhook.data?.missing_fields || []).join(', '),
                      ])
                    : __(
                        'Without it no message reaches the CRM, in either direction.',
                      )
                }}
              </span>
              <span v-if="webhook.data?.error" class="text-p-sm text-ink-red-5">
                {{ webhook.data.error }}
              </span>
            </div>
            <Button
              :label="
                webhook.data?.configured
                  ? __('Complete it')
                  : __('Configure it')
              "
              :loading="configuringWebhook"
              @click="configureWebhook"
            />
          </div>
        </div>

        <div
          v-if="status.data?.installed && status.data?.missing?.length"
          class="mb-4 flex flex-col gap-3 rounded-lg border border-outline-amber-2 bg-surface-amber-1 p-4"
        >
          <span class="text-p-base-medium text-ink-gray-7">
            {{ __('Still missing before WhatsApp can be connected') }}
          </span>
          <div
            v-for="item in status.data.missing"
            :key="item.key"
            class="flex flex-col gap-0.5"
          >
            <span class="text-p-sm-medium text-ink-gray-7">{{
              item.what
            }}</span>
            <span class="text-p-sm text-ink-gray-6">{{ item.how }}</span>
            <!-- what can be finished here is finished here: the id comes off the
                 Meta app and has nowhere else to go -->
            <div v-if="item.fieldname" class="mt-2 flex items-end gap-2">
              <FormControl
                v-model="appForm[item.fieldname]"
                type="text"
                class="w-72"
                :placeholder="__('Paste the id')"
              />
              <Button
                :label="__('Save')"
                variant="solid"
                :loading="savingApp"
                @click="saveWhatsAppApp()"
              />
            </div>
          </div>
          <span class="text-p-sm text-ink-gray-5">
            {{
              __(
                'The rest lives on the Meta app: it cannot be created from here.',
              )
            }}
          </span>
        </div>

        <!-- The QR stays the one path a client is offered. This is for a number
             Embedded Signup cannot reach — Meta's own test number, which is how
             an agency records the App Review videos before it is a Tech
             Provider, and without which the CRM cannot send a single message. -->
        <details class="mb-4 rounded-lg border border-outline-gray-2 p-4">
          <summary class="cursor-pointer text-p-base-medium text-ink-gray-7">
            {{ __('Add a number with its credentials') }}
          </summary>
          <p class="mt-2 text-p-sm text-ink-gray-6">
            {{
              __(
                'For the test number Meta lends the app, from App Dashboard → WhatsApp → API Setup. Use a permanent System User token, not the temporary one, or it stops working halfway through. Clients connect by scanning the QR instead.',
              )
            }}
          </p>
          <div class="mt-3 grid grid-cols-2 gap-3">
            <FormControl
              v-model="manual.phone_number_id"
              type="text"
              :label="__('Phone number ID')"
            />
            <FormControl
              v-model="manual.waba_id"
              type="text"
              :label="__('WhatsApp Business Account ID')"
            />
            <FormControl
              v-model="manual.token"
              type="password"
              :label="__('Access token')"
            />
            <FormControl
              v-model="manual.account_name"
              type="text"
              :label="__('Name (optional)')"
            />
          </div>
          <Button
            class="mt-3"
            variant="solid"
            :label="__('Add number')"
            :loading="addingAccount"
            @click="addAccount"
          />
        </details>

        <div v-if="status.data?.accounts?.length">
          <div class="mb-2 text-p-base-medium text-ink-gray-7">
            {{ __('Numbers') }}
          </div>
          <div
            class="divide-y divide-outline-gray-1 rounded-lg border border-outline-gray-2"
          >
            <div v-for="account in status.data.accounts" :key="account.name">
              <div class="flex items-center gap-3 px-3 py-2.5">
                <div class="min-w-0 flex-1">
                  <div class="truncate text-p-base text-ink-gray-8">
                    {{ account.name }}
                  </div>
                  <div class="truncate text-p-sm text-ink-gray-5">
                    {{ __('Phone number ID') }}: {{ account.phone_id }}
                  </div>
                </div>
                <Badge
                  v-if="account.name == status.data.default_account"
                  :label="__('Sends messages')"
                  theme="green"
                  size="sm"
                />
                <Button
                  v-else
                  size="sm"
                  :label="__('Use for sending')"
                  @click="setDefault(account.name)"
                />
                <Button
                  size="sm"
                  variant="outline"
                  :label="__('Check incoming')"
                  :loading="checking == account.name"
                  @click="recheckDelivery(account.name)"
                />
                <Button
                  variant="ghost"
                  icon="lucide-trash-2"
                  @click="disconnect(account.name)"
                />
              </div>
              <!-- Sending needs only a token, receiving needs two more things that
                   nothing tells you about until a reply never arrives. -->
              <div
                v-if="delivery[account.name]"
                class="px-3 pb-3"
                :class="
                  delivery[account.name].ok
                    ? 'text-ink-green-5'
                    : 'text-ink-gray-6'
                "
              >
                <div v-if="delivery[account.name].ok" class="text-p-sm">
                  {{
                    __(
                      'Incoming messages can arrive: Meta notifies the app and the hub routes them here.',
                    )
                  }}
                </div>
                <div v-else class="flex flex-col gap-1">
                  <div
                    v-for="problem in delivery[account.name].problems"
                    :key="problem.key"
                    class="flex flex-col"
                  >
                    <span class="text-p-sm-medium text-ink-red-5">{{
                      problem.what
                    }}</span>
                    <span class="text-p-sm text-ink-gray-6">{{
                      problem.detail
                    }}</span>
                  </div>
                </div>
              </div>
            </div>
          </div>
          <p class="mt-2 text-p-sm text-ink-gray-5">
            {{
              __(
                'Removing a number here does not affect the WhatsApp Business app on the phone.',
              )
            }}
          </p>
        </div>
      </template>
    </div>
  </div>
</template>

<script setup>
import { createResource, FormControl, toast } from 'frappe-ui'
import { reactive, ref } from 'vue'

const connecting = ref(false)

const manual = ref({
  phone_number_id: '',
  waba_id: '',
  token: '',
  account_name: '',
})
const addingAccount = ref(false)

function addAccount() {
  addingAccount.value = true
  createResource({
    url: 'crm.integrations.whatsapp.api.add_account',
    params: { ...manual.value },
    auto: true,
    onSuccess: (data) => {
      addingAccount.value = false
      manual.value = {
        phone_number_id: '',
        waba_id: '',
        token: '',
        account_name: '',
      }
      toast.success(__('Number added'))
      if (data?.account)
        delivery[data.account] = {
          ok: !data.problems?.length,
          problems: data.problems || [],
        }
      status.reload()
    },
    onError: (e) => {
      addingAccount.value = false
      toast.error(e.messages?.[0] || __('Could not add the number'))
    },
  })
}

const webhook = createResource({
  url: 'crm.integrations.whatsapp.api.get_webhook',
  auto: true,
})

// The signup flow runs on facebook.com and reports itself back to the hub page.
// These are those reports. Reading them used to mean opening the Desk and
// unfolding a JSON blob — a lot of steps between "it didn't work" and the
// sentence that says why.
const attempts = createResource({
  url: 'crm.integrations.whatsapp.api.recent_signup_attempts',
  auto: true,
})
const configuringWebhook = ref(false)

function configureWebhook() {
  configuringWebhook.value = true
  createResource({
    url: 'crm.integrations.whatsapp.api.configure_webhook',
    auto: true,
    onSuccess: (data) => {
      configuringWebhook.value = false
      webhook.data = data
      data.complete
        ? toast.success(__('Webhook configured on the WhatsApp app'))
        : toast.error(data.error || __('Webhook not configured'))
    },
    onError: (e) => {
      configuringWebhook.value = false
      toast.error(e.messages?.[0] || __('Could not configure the webhook'))
    },
  })
}

const status = createResource({
  url: 'crm.integrations.whatsapp.api.get_status',
  auto: true,
})

// the ids that belong to the WhatsApp app itself. They can also come from the
// bench config, which wins; this is the way in on a host where the bench is not
// somebody's to edit.
const appForm = reactive({ whatsapp_app_id: '', whatsapp_signup_config_id: '' })
const savingApp = ref(false)

function saveWhatsAppApp() {
  savingApp.value = true
  // only what was typed: sending an empty box would clear an id that is there
  const params = Object.fromEntries(
    Object.entries(appForm).filter(([, value]) => value),
  )
  createResource({
    url: 'crm.integrations.whatsapp.api.save_whatsapp_app',
    params,
    auto: true,
    onSuccess: (data) => {
      savingApp.value = false
      status.data = data
      toast.success(__('Saved'))
    },
    onError: (e) => {
      savingApp.value = false
      toast.error(e.messages?.[0] || __('Could not save'))
    },
  })
}

// What the check found, per number. Repairing and checking are the same call:
// everything it does is idempotent, so there is nothing to press twice.
const delivery = reactive({})
const checking = ref('')

function recheckDelivery(name) {
  checking.value = name
  createResource({
    url: 'crm.integrations.whatsapp.api.recheck_delivery',
    params: { name },
    auto: true,
    onSuccess: (data) => {
      checking.value = ''
      delivery[name] = data
      data.ok
        ? toast.success(__('This number can receive messages'))
        : toast.error(__('Something is still missing, see below'))
    },
    onError: (e) => {
      checking.value = ''
      toast.error(e.messages?.[0] || __('Could not check the number'))
    },
  })
}

// The hub page that runs Embedded Signup tells us when it is done, because a
// pop-up cannot navigate the tab that opened it.
let connectedListener = null

function listenForConnection(hubOrigin) {
  if (connectedListener)
    window.removeEventListener('message', connectedListener)
  connectedListener = (event) => {
    if (hubOrigin && event.origin !== hubOrigin) return
    if (event.data?.type !== 'crm-whatsapp-connected') return
    window.removeEventListener('message', connectedListener)
    connectedListener = null
    status.reload()
    attempts.reload()
    toast.success(__('WhatsApp connected'))
  }
  window.addEventListener('message', connectedListener)
}

function connect() {
  connecting.value = true
  createResource({
    url: 'crm.integrations.whatsapp.api.get_connect_url',
    auto: true,
    onSuccess: (data) => {
      connecting.value = false
      listenForConnection(data.hub_origin)
      // A window opened straight from this click is what makes Facebook appear
      // without an intermediate page: the hub page inside it redirects on to
      // Facebook by itself. If the browser refuses the window, this tab goes
      // instead — losing the tab is better than losing the connection.
      const popup = window.open(
        data.url,
        'crm-whatsapp-connect',
        'width=640,height=820,noopener=no',
      )
      if (!popup) window.location.href = data.url
    },
    onError: (e) => {
      connecting.value = false
      toast.error(e.messages?.[0] || __('Could not start the connection'))
    },
  })
}

function setDefault(name) {
  createResource({
    url: 'crm.integrations.whatsapp.api.set_default_account',
    params: { name },
    auto: true,
    onSuccess: () => status.reload(),
    onError: (e) => toast.error(e.messages?.[0] || __('Failed to update')),
  })
}

function disconnect(name) {
  createResource({
    url: 'crm.integrations.whatsapp.api.disconnect',
    params: { name },
    auto: true,
    onSuccess: () => {
      toast.success(__('Number removed'))
      status.reload()
    },
    onError: (e) => toast.error(e.messages?.[0] || __('Failed to remove')),
  })
}
</script>
