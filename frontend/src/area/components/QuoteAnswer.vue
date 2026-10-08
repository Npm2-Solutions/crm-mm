<!--
  The person's answer to a quote, under its card (crm.preventivi.firma): «Accept
  and sign» - the code again if it was not read in the last minutes, then the
  quote to read and the stroke drawn with the forms' pad - or «I do not accept»,
  with a reason if they want. Its PDF, and once signed the signed copy, to
  download; one with health data after a code, as a report.
-->
<template>
  <div class="flex flex-col gap-2">
    <p v-if="quote.expired" class="text-p-sm text-ink-gray-7">
      {{
        __('This quote was valid until {0}: ask the centre for a new one.', [
          day(quote.valid_until),
        ])
      }}
    </p>
    <p v-if="quote.signed_on" class="text-p-sm text-ink-gray-7">
      {{ __('Accepted and signed on {0}.', [day(quote.signed_on)]) }}
    </p>
    <Button
      v-if="offre.pdf"
      size="md"
      class="touch-target w-full"
      icon-left="file-text"
      :label="quote.signed_on ? __('Signed copy') : __('Read the PDF')"
      @click="pdf"
    />
    <!-- the two answers side by side, each the width its words need at 280 -->
    <div
      v-if="offre.risponde"
      class="grid gap-2 grid-cols-[repeat(2,minmax(min-content,1fr))]"
    >
      <Button
        size="md"
        class="touch-target"
        :label="__('I do not accept')"
        @click="openDecline"
      />
      <Button
        size="md"
        variant="solid"
        class="touch-target"
        :label="__('Accept and sign')"
        @click="openSign"
      />
    </div>

    <Dialog
      v-model="signing"
      :options="{ title: __('Accept and sign'), size: 'md' }"
    >
      <template #body-content>
        <div class="flex flex-col gap-3">
          <p class="text-p-base text-ink-gray-8">
            <span class="font-medium">{{ quote.title }}</span>
            · {{ __('Total') }} {{ total }}
          </p>
          <p class="text-p-sm text-ink-gray-6">
            {{
              __(
                'By signing you accept the quote as it is, at the prices shown. The centre receives your signature and you get a signed copy here.',
              )
            }}
          </p>
          <a
            v-if="offre.pdf"
            :href="indirizzoDelPdf(area.person, quote.name)"
            class="area-link w-fit py-1"
          >
            {{ __('Read the quote (PDF)') }}
          </a>
          <SignaturePad
            v-model="stroke"
            :placeholder="__('Sign here with your finger')"
          />
          <ErrorMessage :message="error" />
        </div>
      </template>
      <template #actions>
        <div class="flex flex-wrap justify-end gap-2">
          <Button
            size="md"
            :label="__('Cancel')"
            :disabled="busy"
            @click="signing = false"
          />
          <Button
            size="md"
            variant="solid"
            :label="__('Sign and accept')"
            :disabled="!stroke"
            :loading="busy"
            @click="sign"
          />
        </div>
      </template>
    </Dialog>

    <Dialog
      v-model="declining"
      :options="{ title: __('I do not accept'), size: 'md' }"
    >
      <template #body-content>
        <div class="flex flex-col gap-3">
          <p class="text-p-sm text-ink-gray-6">
            {{
              __(
                'We tell the centre you do not accept «{0}». If you want, say why: it helps them propose something else.',
                [quote.title],
              )
            }}
          </p>
          <FormControl
            v-model="reason"
            type="textarea"
            :rows="3"
            :maxlength="500"
            :label="__('Why (if you want)')"
          />
          <ErrorMessage :message="error" />
        </div>
      </template>
      <template #actions>
        <div class="flex flex-wrap justify-end gap-2">
          <Button
            size="md"
            :label="__('Cancel')"
            :disabled="busy"
            @click="declining = false"
          />
          <Button
            size="md"
            variant="solid"
            theme="red"
            :label="__('I do not accept')"
            :loading="busy"
            @click="decline"
          />
        </div>
      </template>
    </Dialog>

    <CodeDialog v-model="asking" :reason="codeReason" @verified="afterCode" />
  </div>
</template>

<script setup>
import SignaturePad from '@/components/Moduli/SignaturePad.vue'
import { Button, Dialog, ErrorMessage, FormControl, call } from 'frappe-ui'
import { computed, ref } from 'vue'
import { anteprima } from '../anteprima'
import { day } from '../dates'
import { cosaOffre, indirizzoDelPdf } from '../preventivi'
import { area, messageOf } from '../store'
import CodeDialog from './CodeDialog.vue'

const props = defineProps({
  quote: { type: Object, required: true },
  // the session answers quotes; a code was read in the last minutes
  answers: { type: Boolean, default: false },
  verified: { type: Boolean, default: false },
})
const emit = defineEmits(['changed', 'verified', 'declined'])

const offre = computed(() =>
  cosaOffre(props.quote, {
    rispondono: props.answers,
    verificato: props.verified,
    anteprima: Boolean(anteprima),
  }),
)

const total = computed(() =>
  new Intl.NumberFormat(document.documentElement.lang || 'it', {
    style: 'currency',
    currency: props.quote.currency || 'EUR',
  }).format(props.quote.totals?.net || 0),
)

const signing = ref(false)
const declining = ref(false)
const asking = ref(false)
const stroke = ref(null)
const reason = ref('')
const busy = ref(false)
const error = ref('')
// what waits for the code: signing, or the PDF
let afterTheCode = null
const codeReason = ref('')

function withTheCode(needed, then, reason = '') {
  if (!needed) return then()
  afterTheCode = then
  codeReason.value = reason
  asking.value = true
}

function afterCode() {
  emit('verified')
  const then = afterTheCode
  afterTheCode = null
  then?.()
}

function openSign() {
  withTheCode(
    offre.value.codicePerFirmare,
    () => {
      stroke.value = null
      error.value = ''
      signing.value = true
    },
    __('To sign we send you a code again: it says the signature is yours.'),
  )
}

function openDecline() {
  reason.value = ''
  error.value = ''
  declining.value = true
}

function pdf() {
  withTheCode(offre.value.codicePerIlPdf, () => {
    window.location.href = indirizzoDelPdf(area.person, props.quote.name)
  })
}

async function sign() {
  busy.value = true
  error.value = ''
  try {
    const data = await call('crm.preventivi.firma.accept_in_area', {
      person: area.person,
      quote: props.quote.name,
      signature: stroke.value,
    })
    signing.value = false
    emit('changed', data)
  } catch (e) {
    error.value = __(messageOf(e))
  } finally {
    busy.value = false
  }
}

async function decline() {
  busy.value = true
  error.value = ''
  try {
    const data = await call('crm.preventivi.firma.decline_in_area', {
      person: area.person,
      quote: props.quote.name,
      reason: reason.value,
    })
    declining.value = false
    emit('declined', data)
  } catch (e) {
    error.value = __(messageOf(e))
  } finally {
    busy.value = false
  }
}
</script>
