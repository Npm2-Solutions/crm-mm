<!--
  The door: an email, then the code we send to it. No password to remember;
  the answer is the same whether the address has an area or not.
-->
<template>
  <div class="flex min-h-full items-center justify-center px-4 py-10">
    <div class="flex w-full max-w-sm flex-col gap-5">
      <div class="flex flex-col items-center gap-2 text-center">
        <img v-if="logo" :src="logo" alt="" class="max-h-10 max-w-[10rem]" />
        <h1 class="text-xl font-semibold text-ink-gray-9">
          {{ centre || __('Your area') }}
        </h1>
        <p class="text-p-base text-ink-gray-6">
          {{ __('Enter with your email') }}.
          {{ __('We send you a code: no password to remember.') }}
        </p>
      </div>
      <form
        v-if="!sent"
        class="flex flex-col gap-3 rounded-lg bg-surface-elevation-1 p-4 shadow-sm"
        @submit.prevent="send"
      >
        <FormControl
          v-model="email"
          type="email"
          :label="__('Email')"
          autocomplete="email"
        />
        <ErrorMessage :message="error" />
        <Button
          variant="solid"
          type="submit"
          :label="__('Send me the code')"
          :loading="busy === true"
          :disabled="!email.trim()"
        />
        <template v-if="passkeys">
          <div class="flex items-center gap-2 text-p-sm text-ink-gray-5">
            <span class="h-px flex-1 bg-surface-gray-3" />
            {{ __('or') }}
            <span class="h-px flex-1 bg-surface-gray-3" />
          </div>
          <Button
            :label="__('Enter with a passkey')"
            icon-left="lucide-fingerprint"
            :loading="busy === 'passkey'"
            @click="withPasskey"
          />
        </template>
      </form>
      <form
        v-else
        class="flex flex-col gap-3 rounded-lg bg-surface-elevation-1 p-4 shadow-sm"
        @submit.prevent="verify"
      >
        <p class="text-p-sm text-ink-gray-6">
          {{
            __(
              'If this address has an area, a code is on its way. It is valid for {0} minutes.',
              [minutes],
            )
          }}
        </p>
        <FormControl
          v-model="code"
          :label="__('The code')"
          inputmode="numeric"
          autocomplete="one-time-code"
          maxlength="6"
        />
        <ErrorMessage :message="error" />
        <Button
          variant="solid"
          type="submit"
          :label="__('Enter')"
          :loading="busy === true"
          :disabled="code.trim().length < 6"
        />
        <div class="flex justify-between">
          <Button
            variant="ghost"
            :label="__('Another address')"
            @click="reset"
          />
          <Button variant="ghost" :label="__('Send it again')" @click="send" />
        </div>
      </form>
    </div>
  </div>
</template>

<script setup>
import { Button, ErrorMessage, FormControl, call } from 'frappe-ui'
import { ref } from 'vue'
import { inJSON, opzioniDiAccesso, supported } from '../passkey'
import { messageOf } from '../store'

const boot = window.AREA || {}
const centre = boot.centre
const logo = boot.logo

const email = ref('')
const code = ref('')
const sent = ref(false)
const minutes = ref(10)
const busy = ref(false)
const error = ref('')

async function send() {
  busy.value = true
  error.value = ''
  try {
    const answer = await call('crm.area.accesso.send_code', {
      email: email.value.trim(),
    })
    minutes.value = answer.minutes
    sent.value = true
  } catch (e) {
    error.value = __(messageOf(e))
  } finally {
    busy.value = false
  }
}

// the phone offers its passkeys for this site: no address to type
const passkeys = supported()

async function withPasskey() {
  busy.value = 'passkey'
  error.value = ''
  try {
    const { options, state } = await call(
      'crm.area.passkey.authentication_options',
    )
    const credenziale = await navigator.credentials.get({
      publicKey: opzioniDiAccesso(options),
    })
    await call('crm.area.passkey.authenticate', {
      credential: JSON.stringify(inJSON(credenziale)),
      state,
    })
    window.location.href = '/area'
  } catch (e) {
    // closed on the phone: nothing to say
    if (e?.name !== 'NotAllowedError') error.value = __(messageOf(e))
  } finally {
    busy.value = false
  }
}

async function verify() {
  busy.value = true
  error.value = ''
  try {
    await call('crm.area.accesso.verify_code', {
      email: email.value.trim(),
      code: code.value.trim(),
    })
    // a new session: the page starts again with it
    window.location.href = '/area'
  } catch (e) {
    error.value = __(messageOf(e))
  } finally {
    busy.value = false
  }
}

function reset() {
  sent.value = false
  code.value = ''
  error.value = ''
}
</script>
