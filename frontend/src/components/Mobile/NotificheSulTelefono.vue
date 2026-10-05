<!--
  Copyright (c) 2026, NPM2 Solutions Srl and contributors
  For license information, please see license.txt

  The More page's card that turns notifications on for the app on the phone's
  home screen (composables/spinta.js): one tap, and the phone asks. Nothing once
  the phone was asked, in a browser tab, or after «Not now» on this phone; the
  settings' Notifications page says the rest.
-->
<template>
  <section
    v-if="offri"
    class="flex flex-col gap-3 rounded-2xl bg-surface-elevation-1 px-4 py-3.5 shadow-sm ring-1 ring-outline-gray-1"
    :aria-label="__('Get notifications on this phone')"
  >
    <div class="flex items-start gap-3">
      <span
        class="grid size-10 shrink-0 place-items-center rounded-xl bg-[var(--brand-subtle)] text-[var(--on-brand-subtle)]"
        aria-hidden="true"
      >
        <span class="lucide-bell-ring size-5" />
      </span>
      <span class="flex min-w-0 flex-1 flex-col gap-0.5">
        <span class="text-base font-semibold text-ink-gray-9">
          {{ __('Get notifications on this phone') }}
        </span>
        <span class="text-p-sm text-ink-gray-6">
          {{ __('They arrive even when {brand} is closed.') }}
        </span>
      </span>
    </div>
    <div class="flex gap-2">
      <Button
        variant="solid"
        class="flex-1"
        :label="__('Turn on')"
        :loading="lavora"
        @click="accendi"
      />
      <Button variant="subtle" :label="__('Not now')" @click="nonOra" />
    </div>
  </section>
</template>

<script setup>
import { attiva, statoQui } from '@/composables/spinta'
import { questoDispositivo } from '@/utils/installa'
import { Button, call, toast } from 'frappe-ui'
import { computed, ref } from 'vue'

// said once on this phone: a convenience of the device, not of the account
const CHIAVE = 'dc-notifiche-non-ora'
function letto() {
  try {
    return window.localStorage.getItem(CHIAVE) === '1'
  } catch {
    return false
  }
}

const scartata = ref(letto())
const chiesto = ref(window.Notification?.permission !== 'default')
const lavora = ref(false)

const offri = computed(
  () =>
    questoDispositivo().installata &&
    statoQui.value === 'pronto' &&
    !chiesto.value &&
    !scartata.value,
)

async function accendi() {
  lavora.value = true
  try {
    const { public_key } = await call('crm.notifiche.spinta.get_push')
    const stato = await attiva(public_key)
    if (stato)
      toast.success(__('Notifications are on: they arrive on this phone.'))
  } catch (e) {
    toast.error(
      e.messages?.join(' ') || __('Notifications could not be turned on here'),
    )
  } finally {
    chiesto.value = window.Notification?.permission !== 'default'
    lavora.value = false
  }
}

function nonOra() {
  scartata.value = true
  try {
    window.localStorage.setItem(CHIAVE, '1')
  } catch {
    // a private window: offered again next time, which is harmless
  }
}
</script>
