<!--
  Copyright (c) 2026, NPM2 Solutions Srl and contributors
  For license information, please see license.txt

  The area on the phone's home screen: it opens like an app, full screen,
  without the browser (utils/installa.js). The browser's own offer a tap away
  on Android, the two taps in Safari on an iPhone; nothing once it is there,
  or after «Not now» on this phone.
-->
<template>
  <section v-if="come !== 'nulla'" class="flex flex-col gap-2">
    <h2 class="area-label">{{ __('On your home screen') }}</h2>
    <div class="area-card flex flex-col gap-3">
      <p class="text-p-base text-ink-gray-8">
        {{
          __(
            'Add the area to your home screen: it opens like an app, without the browser.',
          )
        }}
      </p>
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
      <div class="flex flex-wrap gap-2">
        <Button
          v-if="come === 'pulsante'"
          variant="solid"
          icon-left="lucide-smartphone"
          :label="__('Install')"
          @click="installa"
        />
        <Button variant="ghost" :label="__('Not now')" @click="nonOra" />
      </div>
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

// said once on this phone: a convenience of the device
const NON_ORA = 'area:installa:not-now'

function letto() {
  try {
    return window.localStorage.getItem(NON_ORA) === '1'
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
  // an offer is good once
  offertaDiInstallazione.value = null
  if (outcome === 'dismissed') nonOra()
}

function nonOra() {
  scartata.value = true
  try {
    window.localStorage.setItem(NON_ORA, '1')
  } catch {
    // a private window keeps nothing: the card comes back next time
  }
}
</script>
