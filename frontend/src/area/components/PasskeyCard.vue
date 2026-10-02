<!--
  A passkey for the next time: face or fingerprint instead of the code, the key
  staying on the phone. Offered once it is known the phone can; the passkeys are
  listed with the device they came from, and removed here.
-->
<template>
  <section v-if="shown" class="flex flex-col gap-2">
    <h2 class="area-label">
      {{ __('Entering with a passkey') }}
    </h2>
    <div class="area-card flex flex-col gap-3">
      <template v-if="!list.length">
        <p class="text-p-base text-ink-gray-8">
          {{
            __(
              'Next time, enter with your face or fingerprint instead of a code. The key stays on this phone.',
            )
          }}
        </p>
        <div class="flex flex-wrap gap-2">
          <Button
            variant="solid"
            icon-left="lucide-fingerprint"
            :label="__('Add a passkey')"
            :loading="busy === 'add'"
            @click="add"
          />
          <Button variant="ghost" :label="__('Not now')" @click="notNow" />
        </div>
      </template>
      <template v-else>
        <div
          v-for="key in list"
          :key="key.name"
          class="flex items-center justify-between gap-3"
        >
          <span class="flex min-w-0 flex-col">
            <span class="text-p-base text-ink-gray-8">{{ key.label }}</span>
            <span class="text-p-sm text-ink-gray-5">
              {{
                key.last_used_on
                  ? __('used {0}', [day(key.last_used_on)])
                  : __('added {0}', [day(key.created_on)])
              }}
            </span>
          </span>
          <Button
            class="touch-target shrink-0"
            variant="ghost"
            :label="__('Remove')"
            :loading="busy === key.name"
            @click="remove(key)"
          />
        </div>
        <Button
          class="w-fit"
          icon-left="lucide-plus"
          :label="__('Add one on another device')"
          :loading="busy === 'add'"
          @click="add"
        />
      </template>
      <ErrorMessage :message="error" />
    </div>
  </section>
</template>

<script setup>
import { Button, ErrorMessage, call } from 'frappe-ui'
import { computed, onMounted, ref } from 'vue'
import { day } from '../dates'
import { inJSON, opzioniDiCreazione, supported } from '../passkey'
import { messageOf } from '../store'

const DISMISSED = 'area:passkey:not-now'

const list = ref([])
const loaded = ref(false)
const dismissed = ref(false)
const busy = ref('')
const error = ref('')

try {
  dismissed.value = localStorage.getItem(DISMISSED) === '1'
} catch {
  dismissed.value = false
}

const shown = computed(
  () => supported() && loaded.value && (list.value.length || !dismissed.value),
)

onMounted(async () => {
  if (!supported()) return
  try {
    list.value = (await call('crm.area.passkey.my_passkeys')).passkeys
    loaded.value = true
  } catch {
    loaded.value = false
  }
})

async function add() {
  busy.value = 'add'
  error.value = ''
  try {
    const options = await call('crm.area.passkey.registration_options')
    const credenziale = await navigator.credentials.create({
      publicKey: opzioniDiCreazione(options),
    })
    list.value = (
      await call('crm.area.passkey.register', {
        credential: JSON.stringify(inJSON(credenziale)),
      })
    ).passkeys
  } catch (e) {
    // closed on the phone: nothing to say
    if (e?.name !== 'NotAllowedError') error.value = __(messageOf(e))
  } finally {
    busy.value = ''
  }
}

async function remove(key) {
  busy.value = key.name
  error.value = ''
  try {
    list.value = (
      await call('crm.area.passkey.remove_passkey', { name: key.name })
    ).passkeys
  } catch (e) {
    error.value = __(messageOf(e))
  } finally {
    busy.value = ''
  }
}

function notNow() {
  dismissed.value = true
  try {
    localStorage.setItem(DISMISSED, '1')
  } catch {
    /* only for this visit, then */
  }
}
</script>
