<!--
  The door, as the brand's phone has it: the centre's cloud, "enter your area",
  an email, then the code we send to it in six boxes. No password to remember;
  the answer is the same whether the address has an area or not.
-->
<template>
  <div class="flex min-h-full items-center justify-center px-5 py-10">
    <div class="flex w-full max-w-sm flex-col gap-6">
      <div class="flex flex-col items-center gap-3 text-center">
        <img
          v-if="logo && forma === 'wide'"
          :src="logo"
          :alt="centre || ''"
          class="max-h-14 max-w-[14rem] object-contain dark:rounded-lg dark:bg-white dark:px-2 dark:py-1"
        />
        <template v-else-if="logo || centre">
          <CentreTile
            :logo="logo"
            :forma="forma"
            :nome="centre"
            grande
            class="size-16"
          />
          <span v-if="centre" class="text-[15px] font-bold text-ink-gray-9">
            {{ centre }}
          </span>
        </template>
        <img v-else :src="brand.logo" :alt="brand.name" class="h-8 w-auto" />
        <h1 class="area-title mt-2">{{ __('Enter your area') }}</h1>
        <p class="text-p-base text-ink-gray-6">
          <template v-if="link">
            {{ __('The link of your email enters your area: tap Enter.') }}
          </template>
          <template v-else-if="!sent">
            {{ __('Enter with your email') }}.
            {{ __('We send you a code: no password to remember.') }}
          </template>
          <template v-else>
            {{
              __(
                'If this address has an area, a code is on its way. It is valid for {0} minutes.',
                [minutes],
              )
            }}
          </template>
        </p>
      </div>
      <!-- the email's link: it enters on a tap, never on the opening, which
           the programs that check every link of an email would spend -->
      <form v-if="link" class="flex flex-col gap-3" @submit.prevent="withLink">
        <Button
          variant="solid"
          size="lg"
          type="submit"
          :label="__('Enter')"
          :loading="busy === true"
        />
      </form>
      <form
        v-else-if="!sent"
        class="flex flex-col gap-3"
        @submit.prevent="send"
      >
        <ErrorMessage v-if="linkError" :message="linkError" />
        <FormControl
          ref="campoEmail"
          v-model="email"
          type="email"
          size="lg"
          :label="__('Email')"
          autocomplete="email"
        />
        <ErrorMessage :message="error" />
        <!-- always the action's colour: disabled until something was typed,
             the page's only button looked switched off. Pressed without an
             address it says what it needs -->
        <Button
          variant="solid"
          size="lg"
          type="submit"
          :label="__('Send me the code')"
          :loading="busy === true"
        />
        <template v-if="passkeys">
          <div class="flex items-center gap-2 text-p-sm text-ink-gray-5">
            <span class="h-px flex-1 bg-surface-gray-3" />
            {{ __('or') }}
            <span class="h-px flex-1 bg-surface-gray-3" />
          </div>
          <Button
            size="lg"
            :label="__('Enter with a passkey')"
            icon-left="lucide-fingerprint"
            :loading="busy === 'passkey'"
            @click="withPasskey"
          />
        </template>
      </form>
      <form v-else class="flex flex-col gap-4" @submit.prevent="verify">
        <!-- six boxes over the one field that takes the code: the phone fills it
             from the email, and a paste goes in whole -->
        <label class="area-code">
          <span
            v-for="i in 6"
            :key="i"
            class="area-code__box"
            :class="{
              'is-full': code.length >= i,
              'is-here': focused && code.length === i - 1,
            }"
            aria-hidden="true"
          >
            {{ code[i - 1] || '' }}
          </span>
          <input
            ref="field"
            :value="code"
            :aria-label="__('The code')"
            inputmode="numeric"
            autocomplete="one-time-code"
            maxlength="6"
            @input="
              (e) => (code = e.target.value.replace(/\D/g, '').slice(0, 6))
            "
            @focus="focused = true"
            @blur="focused = false"
          />
        </label>
        <ErrorMessage :message="error" />
        <Button
          variant="solid"
          size="lg"
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
      <!-- the product signs at the foot: the centre leads at the top -->
      <p
        v-if="logo || centre"
        class="flex items-center justify-center gap-1.5 text-xs text-ink-gray-5"
      >
        <img :src="brand.icon" alt="" class="size-4 rounded-[4px]" />
        {{ __('Powered by {brand}') }}
      </p>
    </div>
  </div>
</template>

<script setup>
import { Button, ErrorMessage, FormControl, call } from 'frappe-ui'
import { nextTick, ref } from 'vue'
import { useRoute } from 'vue-router'
import { inJSON, opzioniDiAccesso, supported } from '../passkey'
import { messageOf } from '../store'
import CentreTile from '@/components/CentreTile.vue'
import { useFormaDelLogo } from '@/composables/formaDelLogo'
import { marchio } from '@/utils/marchio'

const boot = window.AREA || {}
const centre = boot.centre
// the centre's mark leads: its logo as it is drawn, else its cloud and its name
const logo = boot.logo
const forma = useFormaDelLogo(logo, boot.logo_shape)
const brand = marchio(boot.brand)
const field = ref(null)
const focused = ref(false)

const route = useRoute()
const link = ref(String(route.query.link || ''))
const linkError = ref('')

const email = ref('')
const code = ref('')
const sent = ref(false)
const minutes = ref(10)
const busy = ref(false)
const error = ref('')

const campoEmail = ref(null)

async function send() {
  if (!email.value.trim()) {
    error.value = __('Write the email you gave the centre.')
    campoEmail.value?.$el?.querySelector('input')?.focus()
    return
  }
  busy.value = true
  error.value = ''
  try {
    const answer = await call('crm.area.accesso.send_code', {
      email: email.value.trim(),
    })
    minutes.value = answer.minutes
    sent.value = true
    // straight to the boxes
    await nextTick()
    field.value?.focus()
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

async function withLink() {
  busy.value = true
  try {
    const { page } = await call('crm.area.collegamento.enter', {
      link: link.value,
    })
    // a new session: the page starts again with it, where the email meant
    window.location.href = page ? `/area/${page}` : '/area'
  } catch (e) {
    // old or used: the usual door, which says the same to everybody
    linkError.value = __(messageOf(e))
    link.value = ''
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
