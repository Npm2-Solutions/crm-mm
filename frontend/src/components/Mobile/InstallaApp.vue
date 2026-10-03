<!--
  Copyright (c) 2026, NPM2 Solutions Srl and contributors
  For license information, please see license.txt

  The More page's card that puts DottorCloud on the phone's home screen
  (utils/installa.js): the browser's own offer a tap away on Android, the two
  taps in Safari on an iPhone. Nothing once it is installed, or after «Not now»
  on this phone.
-->
<template>
  <section
    v-if="come !== 'nulla'"
    class="flex flex-col gap-3 rounded-2xl bg-surface-elevation-1 px-4 py-3.5 shadow-sm ring-1 ring-outline-gray-1"
    :aria-label="__('Put {brand} on your home screen')"
  >
    <div class="flex items-start gap-3">
      <span
        class="grid size-10 shrink-0 place-items-center rounded-xl bg-[var(--brand-subtle)] text-[var(--on-brand-subtle)]"
        aria-hidden="true"
      >
        <span class="lucide-smartphone size-5" />
      </span>
      <span class="flex min-w-0 flex-1 flex-col gap-0.5">
        <span class="text-base font-semibold text-ink-gray-9">
          {{ __('Put {brand} on your home screen') }}
        </span>
        <span class="text-p-sm text-ink-gray-6">
          {{ __('It opens like an app: full screen, without the browser.') }}
        </span>
      </span>
    </div>
    <p v-if="come === 'ios'" class="flex gap-2 text-p-sm text-ink-gray-7">
      <span class="lucide-share mt-0.5 size-4 shrink-0" aria-hidden="true" />
      <span>{{ __('In Safari tap Share, then «Add to Home Screen».') }}</span>
    </p>
    <p v-else-if="come === 'android'" class="text-p-sm text-ink-gray-7">
      {{
        __(
          'Open the browser’s menu (⋮), then «Install app» or «Add to Home screen».',
        )
      }}
    </p>
    <div class="flex gap-2">
      <Button
        v-if="come === 'pulsante'"
        variant="solid"
        class="flex-1"
        :label="__('Install')"
        @click="installa"
      />
      <Button
        variant="subtle"
        :class="come === 'pulsante' ? '' : 'flex-1'"
        :label="__('Not now')"
        @click="nonOra"
      />
    </div>
  </section>
</template>

<script setup>
import {
  comeInstallare,
  offertaDiInstallazione,
  questoDispositivo,
} from '@/utils/installa'
import { Button } from 'frappe-ui'
import { computed, ref } from 'vue'

// said once on this phone: a convenience of the device, not of the account
const CHIAVE = 'dc-installa-non-ora'
function letto() {
  try {
    return window.localStorage.getItem(CHIAVE) === '1'
  } catch {
    return false
  }
}

const scartata = ref(letto())
const dispositivo = questoDispositivo()

const come = computed(() =>
  comeInstallare({
    ...dispositivo,
    scartata: scartata.value,
    offerta: Boolean(offertaDiInstallazione.value),
  }),
)

async function installa() {
  const offerta = offertaDiInstallazione.value
  if (!offerta) return
  offerta.prompt()
  const { outcome } = (await offerta.userChoice) || {}
  // an offer is good once: asked again, the browser makes a new one
  offertaDiInstallazione.value = null
  if (outcome === 'dismissed') nonOra()
}

function nonOra() {
  scartata.value = true
  try {
    window.localStorage.setItem(CHIAVE, '1')
  } catch {
    // a private window keeps nothing: the card comes back next time
  }
}
</script>
