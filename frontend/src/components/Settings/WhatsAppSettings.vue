<!--
  WhatsApp numbers: the ones connected, the one that sends, and the button that
  adds another.

  Two readers. A manager connects a number by scanning a QR code with the
  WhatsApp Business app, chooses which one sends, and stops one that is no
  longer used — that is the page. Everything that makes the QR possible (the
  Meta app, its Embedded Signup configuration, the webhook, what Meta answered
  to the last attempts, numbers added with raw credentials) is the provider's
  plumbing, and sits in "Technical details", for administrators only; the
  server does not send it to anybody else.
-->
<template>
  <div
    class="flex h-full flex-col gap-6 px-4 py-6 sm:px-6 sm:py-8 text-ink-gray-8"
  >
    <div
      class="flex flex-col items-stretch gap-3 px-2 sm:flex-row sm:items-start sm:justify-between sm:gap-3"
    >
      <div class="flex min-w-0 flex-1 flex-col gap-1">
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
      <Button
        v-if="status.data?.installed"
        class="shrink-0"
        variant="solid"
        iconLeft="plus"
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

    <div class="flex flex-1 flex-col gap-4 overflow-y-auto px-2">
      <div
        v-if="status.data && !status.data.installed"
        class="rounded-lg border border-dashed border-outline-gray-2 p-6 text-center text-p-base text-ink-gray-5"
      >
        {{ __('The WhatsApp app is not installed on this site yet.') }}
      </div>

      <template v-else-if="status.data">
        <!-- the setup is unfinished: a manager only needs to know it is not
             theirs to finish -->
        <div
          v-if="status.data.setup_incomplete && !isAdmin"
          class="flex items-start gap-2 rounded-lg bg-surface-gray-2 px-3 py-2.5 text-p-sm text-ink-gray-7"
        >
          <FeatherIcon name="info" class="mt-0.5 size-4 shrink-0" />
          {{
            __(
              'WhatsApp is not set up on this CRM yet. An administrator has to finish the setup before a number can be connected.',
            )
          }}
        </div>

        <!-- and an administrator needs to know exactly what is missing -->
        <div
          v-if="isAdmin && status.data.missing?.length"
          class="flex flex-col gap-3 rounded-lg border border-outline-amber-2 bg-surface-amber-1 p-4"
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
            <!-- what can be finished here is finished here: the id comes off
                 the Meta app and has nowhere else to go -->
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

        <!-- the WhatsApp app is a different Meta app, so its webhook does not
             come along with the Facebook one: it appears here only when it is
             not set, or set short of the fields the CRM needs, with the button
             that fixes it. Meta never adds a field to an existing subscription
             by itself, so "configured" alone was a half-truth: the webhook could
             be registered and still never mention an onboarding or a number's
             own messages. -->
        <div
          v-if="isAdmin && webhook.data?.is_hub && !webhook.data?.complete"
          class="flex items-center justify-between gap-3 rounded-lg border border-outline-amber-2 bg-surface-amber-1 p-4"
        >
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
              webhook.data?.configured ? __('Complete it') : __('Configure it')
            "
            :loading="configuringWebhook"
            @click="configureWebhook"
          />
        </div>

        <!-- numbers -->
        <section class="flex flex-col gap-2">
          <h3 class="text-p-base-medium text-ink-gray-8">
            {{ __('Numbers') }}
          </h3>
          <div
            v-if="status.data.accounts?.length"
            class="divide-y divide-outline-gray-1 rounded-lg border border-outline-gray-2"
          >
            <div v-for="account in status.data.accounts" :key="account.name">
              <div class="flex items-center gap-3 px-3 py-2.5">
                <WhatsAppIcon
                  class="size-6 shrink-0"
                  :class="{ 'opacity-40 grayscale': !isActive(account) }"
                />
                <div class="min-w-0 flex-1">
                  <div
                    class="truncate text-p-base"
                    :class="
                      isActive(account) ? 'text-ink-gray-8' : 'text-ink-gray-5'
                    "
                  >
                    {{ account.name }}
                  </div>
                  <div
                    v-if="isAdmin && account.phone_id"
                    class="truncate text-p-sm text-ink-gray-5"
                  >
                    {{ __('Phone number ID') }}: {{ account.phone_id }}
                  </div>
                </div>
                <Badge
                  v-if="!isActive(account)"
                  :label="__('Not in use')"
                  theme="gray"
                  size="sm"
                />
                <Badge
                  v-else-if="account.name == status.data.default_account"
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
                <Dropdown
                  v-if="accountActions(account).length"
                  placement="right"
                  :options="accountActions(account)"
                >
                  <Button
                    icon="more-horizontal"
                    size="sm"
                    variant="ghost"
                    :loading="checking == account.name"
                    :aria-label="__('More')"
                  />
                </Dropdown>
              </div>
              <!-- Sending needs only a token, receiving needs two more things
                   that nothing tells you about until a reply never arrives. -->
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
          <div
            v-else
            class="rounded-lg border border-dashed border-outline-gray-2 p-6 text-center text-p-base text-ink-gray-5"
          >
            {{
              status.data.can_connect
                ? __(
                    'No number connected yet. Press "Connect WhatsApp" and scan the QR code with the WhatsApp Business app on your phone.',
                  )
                : __('No number connected yet.')
            }}
          </div>
          <p
            v-if="status.data.accounts?.length"
            class="text-p-sm text-ink-gray-5"
          >
            {{
              __(
                'Stopping a number here leaves the WhatsApp Business app on the phone untouched, and keeps every message it carried. It cannot be deleted: the chat history is attached to it.',
              )
            }}
          </p>
        </section>

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
          <div class="mt-3 flex flex-col gap-4">
            <!--
              Which Meta app signs these calls. A borrowed id is legitimate (one
              app for Facebook and WhatsApp) and also how an agency discovers,
              weeks later, that its WhatsApp calls went out as the Facebook app.

              Only on the provider's own site. On a client's the app is somebody
              else's, its id means nothing they can act on, and a number written
              out under «Meta app in use» reads like something they are supposed
              to check.
            -->
            <div
              v-if="status.data.is_hub && status.data.app?.app_id"
              class="flex flex-wrap items-center gap-2 text-p-sm text-ink-gray-6"
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

            <!-- and which login configuration it sends. An app can hold
                 several, and the choice decides how long the client's token
                 lives and whether they are asked for a business portfolio.
                 Meta's dashboard shows what is selected there, which is not the
                 same as what this CRM sends — so say what this CRM sends. -->
            <div
              v-if="status.data.is_hub && status.data.signup_config?.config_id"
              class="text-p-sm text-ink-gray-6"
            >
              <div class="flex flex-wrap items-center gap-2">
                <span>{{ __('Embedded Signup configuration') }}:</span>
                <span class="text-ink-gray-8">{{
                  status.data.signup_config.config_id
                }}</span>
                <span class="text-ink-gray-5">
                  {{
                    status.data.signup_config.from_bench
                      ? __(
                          '— from the bench config, which wins over this screen',
                        )
                      : __('— set here, in Settings')
                  }}
                </span>
                <!-- An app can hold more than one configuration, and the one it
                     should send changes: a token that expires versus one that
                     does not. -->
                <Button
                  v-if="!status.data.signup_config.from_bench && !editingConfig"
                  variant="ghost"
                  size="sm"
                  :label="__('Change')"
                  @click="startEditingConfig"
                />
              </div>
              <div v-if="editingConfig" class="mt-2 flex items-end gap-2">
                <FormControl
                  v-model="appForm.whatsapp_signup_config_id"
                  type="text"
                  class="w-72"
                  :placeholder="__('Paste the id')"
                />
                <Button
                  :label="__('Save')"
                  variant="solid"
                  :loading="savingApp"
                  @click="saveConfigId"
                />
                <Button :label="__('Cancel')" @click="editingConfig = false" />
              </div>
            </div>

            <!-- what Meta said, last few attempts. Only the hub has these rows:
                 a client site's onboarding is logged where the page lives, not
                 where the CRM does. -->
            <div
              v-if="attempts.data?.is_hub && attempts.data?.attempts?.length"
              class="flex flex-col"
            >
              <div class="mb-1 text-p-sm-medium text-ink-gray-7">
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
                  <!-- what we worked out about a code Meta does not document.
                       A lead, not a verdict — and it is labelled as one. -->
                  <div v-if="row.hint" class="text-ink-gray-6">
                    {{ row.hint }}
                  </div>
                  <!-- the two values Meta asks for in a support ticket -->
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

            <!-- The QR stays the one path a client is offered. This is for a
                 number Embedded Signup cannot reach — Meta's own test number,
                 which is how an agency records the App Review videos before it
                 is a Tech Provider, and without which the CRM cannot send a
                 single message. -->
            <div class="flex flex-col gap-2">
              <div class="text-p-sm-medium text-ink-gray-7">
                {{ __('Add a number with its credentials') }}
              </div>
              <p class="text-p-sm text-ink-gray-6">
                {{
                  __(
                    'For the test number Meta lends the app, from App Dashboard → WhatsApp → API Setup. Use a permanent System User token, not the temporary one, or it stops working halfway through. Clients connect by scanning the QR instead.',
                  )
                }}
              </p>
              <div class="grid grid-cols-2 gap-3">
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
              <div>
                <Button
                  variant="solid"
                  :label="__('Add number')"
                  :loading="addingAccount"
                  @click="addAccount"
                />
              </div>
            </div>
          </div>
        </details>
      </template>
    </div>

    <!-- stopping a number stops its conversations here: asked, not assumed -->
    <Dialog
      v-model="confirmingStop"
      :options="{
        title: __('Stop using {0}?', [stoppingAccount]),
        actions: [
          {
            label: __('Stop using it'),
            theme: 'red',
            variant: 'solid',
            loading: stopping,
            onClick: stopNumber,
          },
        ],
      }"
    >
      <template #body-content>
        <p class="text-p-base text-ink-gray-6">
          {{
            __(
              'The CRM stops sending and receiving on this number. The WhatsApp Business app on the phone is not touched, and every message stays where it is. Scanning the QR again brings it back.',
            )
          }}
        </p>
      </template>
    </Dialog>
  </div>
</template>

<script setup>
import WhatsAppIcon from '@/components/Icons/WhatsAppIcon.vue'
import { call, createResource, Dropdown, FormControl, toast } from 'frappe-ui'
import { computed, onMounted, onUnmounted, reactive, ref, watch } from 'vue'
import { refreshWhatsappState } from '@/composables/whatsapp'
import {
  listenForSignup,
  loadFacebookSdk,
  loginOptions,
  runsHere,
} from '@/utils/whatsappSignup'

const connecting = ref(false)

const status = createResource({
  url: 'crm.integrations.whatsapp.api.get_status',
  auto: true,
})

// what the server decided to send: the technical half only goes to
// administrators, so this is also what the screen shows
const isAdmin = computed(() => Boolean(status.data?.is_admin))

// a number taken out of use keeps its row, for the history it carries
function isActive(account) {
  return account.status !== 'Inactive'
}

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
      refreshWhatsappState()
    },
    onError: (e) => {
      addingAccount.value = false
      toast.error(e.messages?.[0] || __('Could not add the number'))
    },
  })
}

// Both of these are an administrator's, on the server as on the screen: for
// anybody else they are never asked for.
const webhook = createResource({
  url: 'crm.integrations.whatsapp.api.get_webhook',
})

// The signup flow runs on facebook.com and reports itself back to the hub page.
// These are those reports. Reading them used to mean opening the Desk and
// unfolding a JSON blob — a lot of steps between "it didn't work" and the
// sentence that says why.
const attempts = createResource({
  url: 'crm.integrations.whatsapp.api.recent_signup_attempts',
})

watch(
  isAdmin,
  (admin) => {
    if (!admin) return
    if (!webhook.fetched && !webhook.loading) webhook.fetch()
    if (!attempts.fetched && !attempts.loading) attempts.fetch()
  },
  { immediate: true },
)

const configuringWebhook = ref(false)

function configureWebhook() {
  configuringWebhook.value = true
  createResource({
    url: 'crm.integrations.whatsapp.api.configure_webhook',
    auto: true,
    onSuccess: (data) => {
      configuringWebhook.value = false
      webhook.data = data
      if (data.complete)
        toast.success(__('Webhook configured on the WhatsApp app'))
      else toast.error(data.error || __('Webhook not configured'))
    },
    onError: (e) => {
      configuringWebhook.value = false
      toast.error(e.messages?.[0] || __('Could not configure the webhook'))
    },
  })
}

// the ids that belong to the WhatsApp app itself. They can also come from the
// bench config, which wins; this is the way in on a host where the bench is not
// somebody's to edit.
const appForm = reactive({ whatsapp_app_id: '', whatsapp_signup_config_id: '' })
const savingApp = ref(false)
const editingConfig = ref(false)

function startEditingConfig() {
  // prefilled with what is in use, so changing one digit does not mean
  // retyping sixteen
  appForm.whatsapp_signup_config_id =
    status.data?.signup_config?.config_id || ''
  editingConfig.value = true
}

function saveConfigId() {
  if (!appForm.whatsapp_signup_config_id?.trim()) {
    toast.error(__('Paste the configuration id first'))
    return
  }
  saveWhatsAppApp(() => {
    editingConfig.value = false
  })
}

function saveWhatsAppApp(onSaved) {
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
      if (onSaved) onSaved()
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
      if (data.ok) toast.success(__('This number can receive messages'))
      else toast.error(__('Something is still missing, see below'))
    },
    onError: (e) => {
      checking.value = ''
      toast.error(e.messages?.[0] || __('Could not check the number'))
    },
  })
}

// the menu of a number: checking the route messages come back on is a repair
// tool, and an administrator's; stopping a number is anybody's who manages it
function accountActions(account) {
  if (!isActive(account)) return []
  return [
    ...(isAdmin.value
      ? [
          {
            label: __('Check incoming messages'),
            icon: 'activity',
            onClick: () => recheckDelivery(account.name),
          },
        ]
      : []),
    {
      label: __('Stop using this number'),
      icon: 'power',
      onClick: () => askToStop(account.name),
    },
  ]
}

// What Embedded Signup reported about the account the person picked. It comes
// over `postMessage`, separately from the code the callback brings, and either
// can arrive without the other.
let signupData = null
let stopListening = null
// the state of the flow in progress, so the session log knows which one a
// message belongs to
let signupState = ''

// Facebook's script, fetched while the panel is merely open. `FB.login` opens a
// window, and a browser allows that only inside a gesture it is still handling:
// waiting for a script in the click handler loses the gesture and the window is
// blocked. This is also why nothing here is awaited before the call.
// Meta asks for Embedded Signup to be implemented with session logging, and it
// is also the only thing that makes a stalled onboarding explicable afterwards.
// The hub page had it; this path, when it was added, did not — so the log went
// quiet again for exactly the connections we were watching.
function logSignupEvent(event, detail) {
  if (!signupState) return
  call('crm.integrations.whatsapp.signup.log_session_event', {
    state: signupState,
    event,
    data: detail || {},
  }).catch(() => {
    // logging must never be what stops a connection
  })
}

onMounted(() => {
  stopListening = listenForSignup((event, detail) => {
    logSignupEvent(event, detail)
    if (String(event).indexOf('FINISH') === 0) signupData = detail
  })
})

// `status` loads by itself, so the app id arrives after this mounts.
watch(
  () => status.data,
  (data) => {
    const app = data?.app?.app_id
    if (app && runsHere(data?.hub_origin, window.location.origin)) {
      loadFacebookSdk(app).catch(() => {})
    }
  },
  { immediate: true },
)
onUnmounted(() => stopListening && stopListening())

function finishSignup(code, state) {
  return call('crm.integrations.whatsapp.signup.complete_signup', {
    state,
    code,
    waba_id: signupData?.waba_id || '',
    phone_number_id: signupData?.phone_number_id || '',
  })
    .then(() => {
      connecting.value = false
      toast.success(__('WhatsApp connected'))
      status.reload()
      // the tab on a lead, the button in the header, the box in the
      // communication area: all of them hang off flags read when the app
      // loaded, and this connection never left the page
      refreshWhatsappState()
    })
    .catch((e) => {
      connecting.value = false
      const reason = e.messages?.[0] || String(e?.message || e)
      logSignupEvent('ERROR', { current_step: 'complete', message: reason })
      toast.error(reason)
    })
}

// One click, one window — the same thing Meta's own builder does.
//
// It only works where the domain is registered with the Meta app, which for the
// agency is this very domain: its CRM is the hub. A client CRM lives somewhere
// Facebook has never heard of and cannot open the dialog at all, so it is sent
// to the hub's page, which can. That page is not ceremony; it is the only
// address Meta will start the flow from.
function launchHere(data) {
  loadFacebookSdk(data.app_id)
    .then((FB) => {
      signupData = null
      signupState = data.state
      logSignupEvent('STARTED', { current_step: 'launch' })
      FB.login(
        (response) => {
          const code = response?.authResponse?.code
          if (!code) {
            connecting.value = false
            logSignupEvent('CANCEL', {
              current_step: 'login',
              status: response?.status || '',
            })
            toast.error(__('Connection cancelled'))
            return
          }
          finishSignup(code, data.state)
        },
        loginOptions(data.config_id, data.redirect_uri),
      )
    })
    .catch(() => {
      // the script never arrived — a blocker, usually. The hub page says so
      // properly, so send the person there rather than failing in a toast.
      window.location.href = data.url
    })
}

function connect() {
  connecting.value = true
  createResource({
    url: 'crm.integrations.whatsapp.api.get_connect_url',
    auto: true,
    onSuccess: (data) => {
      if (runsHere(data.hub_origin, window.location.origin)) {
        launchHere(data)
        return
      }
      connecting.value = false
      // Another domain: the hub page is the registered one, so it opens
      // Facebook. This tab goes there and comes back when it is done.
      window.location.href = data.url
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
    onSuccess: () => {
      status.reload()
      refreshWhatsappState()
    },
    onError: (e) => toast.error(e.messages?.[0] || __('Failed to update')),
  })
}

// stopping a number switches it off; nothing is deleted, because the chat
// history belongs to it
const confirmingStop = ref(false)
const stoppingAccount = ref('')
const stopping = ref(false)

function askToStop(name) {
  stoppingAccount.value = name
  confirmingStop.value = true
}

function stopNumber() {
  stopping.value = true
  createResource({
    url: 'crm.integrations.whatsapp.api.disconnect',
    params: { name: stoppingAccount.value },
    auto: true,
    onSuccess: () => {
      stopping.value = false
      confirmingStop.value = false
      toast.success(__('This number is no longer in use'))
      status.reload()
      refreshWhatsappState()
    },
    onError: (e) => {
      stopping.value = false
      toast.error(e.messages?.[0] || __('Could not stop this number'))
    },
  })
}
</script>
