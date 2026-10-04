<!--
  Modifications copyright (c) 2026, NPM2 Solutions Srl
-->
<template>
  <div class="flex min-h-0 flex-1 flex-col gap-5 text-ink-gray-8">
    <div class="flex flex-col gap-1">
      <h2
        class="flex gap-2 text-2xl-semibold leading-tight md:h-5 md:leading-none"
      >
        {{ nuova ? __('Add a mailbox') : accountData.email_account_name }}
      </h2>
      <p class="text-p-base text-ink-gray-6">
        {{
          nuova
            ? __(
                'Where is the centre’s mailbox? Its servers are known already: you write the address and the password.',
              )
            : __(
                'What the mailbox does in {brand}. A new password replaces the one it has.',
              )
        }}
      </p>
    </div>

    <div class="flex min-h-0 flex-1 flex-col gap-5 overflow-y-auto">
      <!-- where the mailbox is: chosen once, its servers are the server's -->
      <div v-if="nuova" class="flex flex-col gap-2">
        <div class="flex flex-wrap gap-x-2 gap-y-3">
          <button
            v-for="f in FORNITORI"
            :key="f.chiave"
            type="button"
            class="w-[72px] rounded-lg focus:outline-none focus-visible:ring-2 focus-visible:ring-outline-gray-3"
            :aria-pressed="stato.provider === f.chiave"
            @click="stato.provider = f.chiave"
          >
            <EmailProviderIcon
              :logo="logoDi[f.chiave]"
              :name="f.nome"
              :label="f.nome"
              :selected="stato.provider === f.chiave"
            />
          </button>
        </div>
        <p class="text-p-sm text-ink-gray-5">
          {{
            __(
              'Outlook, Hotmail and Microsoft 365 sign in on Microsoft’s own page: the agency connects them.',
            )
          }}
        </p>
      </div>
      <div v-else class="flex items-center gap-3">
        <EmailProviderIcon
          :logo="logoDi[stato.provider]"
          :name="scelto?.nome || ''"
        />
        <span class="text-p-base text-ink-gray-7">{{ scelto?.nome }}</span>
      </div>

      <template v-if="scelto">
        <!-- what the provider asks of the password -->
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

        <div class="grid grid-cols-2 gap-4 max-md:grid-cols-1">
          <FormControl
            v-model="stato.email_id"
            type="email"
            :label="__('Address')"
            :placeholder="__('reception@yourcentre.com')"
          />
          <FormControl
            v-model="stato.password"
            type="password"
            :label="__('Password')"
            :placeholder="nuova ? '' : __('Unchanged')"
          />
          <FormControl
            v-model="stato.email_account_name"
            type="text"
            :label="__('Name')"
            :placeholder="__('Reception')"
            :description="
              __('How {brand} calls the mailbox; empty, its address.')
            "
          />
        </div>

        <div class="flex flex-col divide-y divide-outline-gray-1">
          <div
            v-for="i in interruttori(stato, servizio)"
            :key="i.campo"
            class="flex items-start justify-between gap-4 py-3"
          >
            <div class="flex min-w-0 flex-col gap-0.5">
              <span class="text-p-base-medium text-ink-gray-8">
                {{ __(i.etichetta) }}
              </span>
              <span class="text-p-sm text-ink-gray-5">
                {{ __(i.descrizione) }}
              </span>
            </div>
            <Switch
              :aria-label="__(i.etichetta)"
              v-model="stato[i.campo]"
              class="shrink-0"
            />
          </div>
        </div>
      </template>
      <ErrorMessage v-if="errore" :message="errore" />
    </div>

    <div class="dialog-footer flex justify-between gap-2">
      <Button
        :label="__('Back')"
        variant="outline"
        :disabled="salvando"
        @click="emit('update:step', 'email-list')"
      />
      <Button
        :label="nuova ? __('Add') : __('Save')"
        variant="solid"
        :disabled="!scelto"
        :loading="salvando"
        @click="salva"
      />
    </div>
  </div>
</template>

<script setup>
import {
  Button,
  call,
  ErrorMessage,
  FormControl,
  Switch,
  toast,
} from 'frappe-ui'
import { computed, reactive, ref } from 'vue'
import LucideInfo from '~icons/lucide/info'
import {
  daCorreggere,
  FORNITORI,
  fornitore,
  interruttori,
} from '@/utils/caselle'
import { logoDi } from './emailConfig'
import EmailProviderIcon from './EmailProviderIcon.vue'

const props = defineProps({
  // the mailbox to change; without a name, a new one (`servizio`: whether
  // {brand}'s emails leave through the agency's service)
  accountData: { type: Object, default: () => ({}) },
})

const emit = defineEmits(['update:step'])

const nuova = computed(() => !props.accountData?.name)
const servizio = Boolean(props.accountData?.servizio)

const stato = reactive({
  provider: props.accountData?.provider || '',
  email_account_name: props.accountData?.email_account_name || '',
  email_id: props.accountData?.email_id || '',
  // the list never carries a password: typing one is the change
  password: '',
  enable_incoming: nuova.value
    ? true
    : Boolean(props.accountData.enable_incoming),
  enable_outgoing: nuova.value
    ? true
    : Boolean(props.accountData.enable_outgoing),
  default_incoming: Boolean(props.accountData?.default_incoming),
  default_outgoing: Boolean(props.accountData?.default_outgoing),
  create_lead_from_incoming_email: nuova.value
    ? true
    : Boolean(props.accountData.create_lead_from_incoming_email),
})

const scelto = computed(() => fornitore(stato.provider))

const errore = ref('')
const salvando = ref(false)
async function salva() {
  const problema = daCorreggere(stato, !nuova.value)
  errore.value = problema ? __(problema) : ''
  if (problema) return
  const dati = { ...stato }
  if (!dati.password) delete dati.password
  salvando.value = true
  try {
    if (nuova.value) {
      await call('crm.api.settings.create_email_account', { data: dati })
      toast.success(__('Mailbox added'))
    } else {
      await call('crm.api.settings.update_email_account', {
        name: props.accountData.name,
        data: dati,
      })
      toast.success(__('Mailbox saved'))
    }
    emit('update:step', 'email-list')
  } catch (e) {
    // the server says what went wrong in words: the password, the server
    errore.value = e.messages?.[0] || __('Could not save the mailbox')
  } finally {
    salvando.value = false
  }
}
</script>
