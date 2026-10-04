<!--
  Copyright (c) 2026, NPM2 Solutions Srl and contributors
  For license information, please see license.txt

  Settings > Your account > Your email (doc 51): the mailbox one writes to people
  from - with its password, or signing in with Google or Microsoft where the agency
  set it up - the centre's mailboxes one also writes from, and the signature.

  From one's own mailbox only what is the centre's arrives: the answers to what was
  written from {brand} and the emails of the people the centre knows. The rest of
  one's post stays where it is (crm/posta/personale.py).
-->
<template>
  <SettingsLayoutBase
    :title="__('Your email')"
    :description="
      __(
        'The mailbox you write to people from in {brand}: their answers come back to their page. Only those answers and the emails of the people the centre knows arrive here; the rest of your post stays yours.',
      )
    "
  >
    <template #content>
      <div v-if="stato.data" class="flex flex-col gap-8">
        <!-- one's own mailbox -->
        <section class="flex flex-col gap-3">
          <h3 class="text-base-semibold text-ink-gray-8">
            {{ __('Your mailbox') }}
          </h3>

          <div
            v-if="casella && !modifica"
            class="flex items-center justify-between gap-3 rounded-xl border border-outline-gray-2 px-4 py-3 max-md:flex-col max-md:items-start"
          >
            <div class="flex min-w-0 items-center gap-3">
              <EmailProviderIcon
                :logo="logoDi[casella.provider]"
                :name="nomeDelFornitore(casella.provider)"
              />
              <div class="flex min-w-0 flex-col">
                <span class="truncate text-p-base text-ink-gray-8">
                  {{ casella.email_id }}
                </span>
                <span
                  class="text-p-sm"
                  :class="
                    casella.connected
                      ? 'text-ink-green-8'
                      : casella.waiting
                        ? 'text-ink-amber-8'
                        : 'text-ink-gray-5'
                  "
                >
                  {{ __(statoDellaCasella(casella), null, 'Mailbox') }}
                </span>
              </div>
            </div>
            <div class="flex shrink-0 flex-wrap gap-2">
              <Button
                v-if="casella.waiting && casella.signed_in_with"
                variant="solid"
                :label="__('Finish signing in')"
                :loading="lavoro === casella.signed_in_with"
                @click="accedi(casella.signed_in_with)"
              />
              <Button
                v-if="!casella.connected && !casella.waiting"
                variant="solid"
                :label="__('Connect again')"
                @click="apriModifica"
              />
              <Button
                v-else
                variant="subtle"
                :label="__('Change')"
                @click="apriModifica"
              />
              <Button
                v-if="casella.connected || casella.waiting"
                variant="outline"
                :label="__('Disconnect')"
                :loading="lavoro === 'scollega'"
                @click="scollega"
              />
            </div>
          </div>

          <!-- connecting it -->
          <div v-else class="flex flex-col gap-4">
            <FormControl
              v-model="nuova.email_id"
              class="max-w-md"
              type="email"
              :label="__('Your address')"
              :placeholder="__('reception@yourcentre.com')"
            />

            <!-- signing in on Google's or Microsoft's own page: no password here -->
            <div v-if="accessi.length" class="flex flex-col gap-2">
              <div class="flex flex-wrap gap-2">
                <Button
                  v-for="a in accessi"
                  :key="a.chiave"
                  variant="solid"
                  :label="__(a.etichetta)"
                  :loading="lavoro === a.chiave"
                  @click="accedi(a.chiave)"
                />
              </div>
              <p class="text-p-sm text-ink-gray-5">
                {{
                  __(
                    'Your password stays with them: {brand} gets only the access to read and send, and you can take it back.',
                  )
                }}
              </p>
            </div>

            <div class="flex flex-col gap-2">
              <span class="text-p-sm-medium text-ink-gray-7">
                {{
                  accessi.length
                    ? __('Or with its password, where it is')
                    : __('Where it is')
                }}
              </span>
              <div class="flex flex-wrap gap-x-2 gap-y-3">
                <button
                  v-for="f in FORNITORI"
                  :key="f.chiave"
                  type="button"
                  class="w-[72px] rounded-lg focus:outline-none focus-visible:ring-2 focus-visible:ring-outline-gray-3"
                  :aria-pressed="nuova.provider === f.chiave"
                  @click="nuova.provider = f.chiave"
                >
                  <EmailProviderIcon
                    :logo="logoDi[f.chiave]"
                    :name="f.nome"
                    :label="f.nome"
                    :selected="nuova.provider === f.chiave"
                  />
                </button>
              </div>
            </div>

            <template v-if="scelto">
              <div
                class="flex items-start gap-2 rounded-lg border border-outline-gray-2 px-3 py-2 text-ink-gray-6"
              >
                <LucideInfo class="mt-0.5 size-4 shrink-0" />
                <p class="text-p-sm">
                  {{ __(scelto.nota) }}
                  <a
                    v-if="scelto.link"
                    :href="scelto.link"
                    target="_blank"
                    rel="noopener"
                    class="underline"
                    >{{ __('How to make it') }}</a
                  >
                </p>
              </div>
              <FormControl
                v-model="nuova.password"
                class="max-w-md"
                type="password"
                :label="__('Password')"
                :placeholder="stessa ? __('Unchanged') : ''"
              />
            </template>

            <ErrorMessage v-if="errore" :message="errore" />
            <div class="flex flex-wrap gap-2">
              <Button
                v-if="scelto"
                variant="solid"
                :label="__('Connect')"
                :loading="lavoro === 'collega'"
                @click="collega"
              />
              <Button
                v-if="casella"
                variant="subtle"
                :label="__('Cancel')"
                @click="modifica = false"
              />
            </div>
          </div>
        </section>

        <!-- the centre's mailboxes one writes from too -->
        <section v-if="stato.data.centre.length" class="flex flex-col gap-1">
          <h3 class="text-base-semibold text-ink-gray-8">
            {{ __("The centre's mailboxes you write from") }}
          </h3>
          <p class="text-p-sm text-ink-gray-5">
            {{
              __(
                "Writing to a person, you choose among these and your own. Without any, you write through {brand}, in your name and the centre's, and the answers come back to the centre.",
              )
            }}
          </p>
          <div class="flex flex-col divide-y divide-outline-gray-1">
            <SettingsRow
              v-for="c in stato.data.centre"
              :key="c.name"
              :label="c.name"
              :description="c.email_id"
            >
              <Switch
                :model-value="stato.data.senders.includes(c.name)"
                :disabled="lavoro === 'scelte'"
                :aria-label="c.name"
                @update:model-value="(valore) => scegli(c.name, valore)"
              />
            </SettingsRow>
          </div>
        </section>

        <!-- the signature -->
        <section v-if="utente.doc" class="flex flex-col gap-2">
          <h3 class="text-base-semibold text-ink-gray-8">
            {{ __('Signature') }}
          </h3>
          <p class="text-p-sm text-ink-gray-5">
            {{ __('At the end of the emails you write from {brand}.') }}
          </p>
          <RichTextField
            :label="__('Signature')"
            editor-class="prose-sm min-h-28 max-w-full border rounded-b-lg border-t-0 p-2 border-outline-elevation-2"
            :content="utente.doc.email_signature"
            :fixed-menu="true"
            @change="(valore) => (firma = valore)"
          />
          <div>
            <Button
              variant="solid"
              :label="__('Save')"
              :disabled="firma === null"
              :loading="utente.setValue.loading"
              @click="salvaFirma"
            />
          </div>
        </section>
      </div>
    </template>
  </SettingsLayoutBase>
</template>

<script setup>
import SettingsLayoutBase from '@/components/Layouts/SettingsLayoutBase.vue'
import SettingsRow from '@/components/Settings/SettingsRow.vue'
import RichTextField from '@/components/RichTextField.vue'
import EmailProviderIcon from '@/components/Settings/EmailProviderIcon.vue'
import { logoDi } from '@/components/Settings/emailConfig'
import { openOAuthPopup, onOAuthResult } from '@/composables/oauthPopup'
import {
  ACCESSI,
  FORNITORI,
  daCorreggerePropria,
  fornitore,
  nomeDelFornitore,
  statoDellaCasella,
} from '@/utils/caselle'
import {
  Button,
  call,
  createDocumentResource,
  createResource,
  ErrorMessage,
  FormControl,
  Switch,
  toast,
} from 'frappe-ui'
import { computed, inject, reactive, ref } from 'vue'
import LucideInfo from '~icons/lucide/info'

const { user: utenteDellaSessione } = inject('session')

const modifica = ref(false)
const nuova = reactive({ provider: '', email_id: '', password: '' })
// the sign-in already finished once since the page opened
let finito = false

const stato = createResource({
  url: 'crm.posta.personale.get_my_email',
  auto: true,
  onSuccess: (dati) => {
    if (!nuova.email_id)
      nuova.email_id = dati.mailbox?.email_id || dati.login_email || ''
    // back from Google's or Microsoft's page in this tab, the popup blocked
    if (dati.mailbox?.waiting && !finito) {
      finito = true
      finisci()
    }
  },
})

const utente = createDocumentResource({
  doctype: 'User',
  name: utenteDellaSessione,
})

const casella = computed(() => stato.data?.mailbox || null)
const accessi = computed(() =>
  ACCESSI.filter((a) => stato.data?.sign_in?.[a.chiave]),
)

const scelto = computed(() => fornitore(nuova.provider))
const stessa = computed(
  () =>
    Boolean(casella.value) &&
    casella.value.provider === nuova.provider &&
    !casella.value.signed_in_with,
)

function apriModifica() {
  errore.value = ''
  nuova.provider = casella.value?.signed_in_with
    ? ''
    : casella.value?.provider || ''
  nuova.email_id = casella.value?.email_id || nuova.email_id
  nuova.password = ''
  modifica.value = true
}

const lavoro = ref('')
const errore = ref('')

async function collega() {
  const problema = daCorreggerePropria(nuova, stessa.value)
  errore.value = problema ? __(problema) : ''
  if (problema) return
  lavoro.value = 'collega'
  try {
    const dati = { ...nuova }
    if (!dati.password) delete dati.password
    stato.setData(
      await call('crm.posta.personale.connect_my_mailbox', { data: dati }),
    )
    modifica.value = false
    nuova.password = ''
    toast.success(__('Your mailbox is connected'))
  } catch (e) {
    errore.value = e.messages?.[0] || __('Could not connect the mailbox')
  } finally {
    lavoro.value = ''
  }
}

async function accedi(accesso) {
  errore.value = ''
  lavoro.value = accesso
  try {
    const url = await call('crm.posta.personale.start_sign_in', {
      provider: accesso,
      email_id: nuova.email_id || casella.value?.email_id || '',
    })
    finito = false
    openOAuthPopup(url)
    await stato.reload()
    modifica.value = false
  } catch (e) {
    errore.value = e.messages?.[0] || __('Could not start signing in')
  } finally {
    lavoro.value = ''
  }
}

async function finisci() {
  try {
    const dati = await call('crm.posta.personale.finish_sign_in')
    stato.setData(dati)
    if (dati.mailbox?.connected) toast.success(__('Your mailbox is connected'))
  } catch (e) {
    toast.error(e.messages?.[0] || __('Could not connect the mailbox'))
  }
}

onOAuthResult('posta', ({ error }) => {
  if (error) {
    toast.error(error)
    return
  }
  finisci()
})

async function scollega() {
  lavoro.value = 'scollega'
  try {
    stato.setData(await call('crm.posta.personale.disconnect_my_mailbox'))
    toast.success(__('Your mailbox is disconnected'))
  } catch (e) {
    toast.error(e.messages?.[0] || __('Could not disconnect the mailbox'))
  } finally {
    lavoro.value = ''
  }
}

async function scegli(conto, valore) {
  const scelte = new Set(stato.data.senders)
  if (valore) scelte.add(conto)
  else scelte.delete(conto)
  lavoro.value = 'scelte'
  try {
    stato.setData(
      await call('crm.posta.personale.set_my_senders', {
        accounts: [...scelte],
      }),
    )
  } catch (e) {
    toast.error(e.messages?.[0] || __('Could not save'))
  } finally {
    lavoro.value = ''
  }
}

const firma = ref(null)
function salvaFirma() {
  utente.setValue.submit(
    { email_signature: firma.value },
    {
      onSuccess: () => {
        firma.value = null
        toast.success(__('Signature saved'))
      },
    },
  )
}
</script>
