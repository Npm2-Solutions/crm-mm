<!--
  A code again before a document is handed over: design.md, "per scaricare un
  referto si rientra". Verified, downloads work for fifteen minutes - and a
  quote is signed, the code saying who signs.
-->
<template>
  <Dialog v-model="show" :options="{ title: __('The code'), size: 'sm' }">
    <template #body-content>
      <div class="flex flex-col gap-3">
        <p class="text-p-sm text-ink-gray-6">
          {{ reason || __('To download a document we send you a code again.') }}
        </p>
        <FormControl
          v-model="code"
          :label="__('The code')"
          inputmode="numeric"
          autocomplete="one-time-code"
          maxlength="6"
        />
        <ErrorMessage :message="error" />
      </div>
    </template>
    <template #actions>
      <div class="flex justify-end gap-2">
        <Button :label="__('Send it again')" @click="send" />
        <Button
          variant="solid"
          :label="__('Enter')"
          :loading="busy"
          :disabled="code.trim().length < 6"
          @click="verify"
        />
      </div>
    </template>
  </Dialog>
</template>

<script setup>
import { Button, Dialog, ErrorMessage, FormControl, call } from 'frappe-ui'
import { ref, watch } from 'vue'
import { messageOf } from '../store'

// why the code is asked: a download, unless the caller says (signing a quote)
defineProps({ reason: { type: String, default: '' } })
const emit = defineEmits(['verified'])
const show = defineModel({ type: Boolean })
const code = ref('')
const error = ref('')
const busy = ref(false)

watch(show, (open) => {
  if (!open) return
  code.value = ''
  error.value = ''
  send()
})

async function send() {
  try {
    await call('crm.area.accesso.send_code')
  } catch (e) {
    error.value = __(messageOf(e))
  }
}

async function verify() {
  busy.value = true
  error.value = ''
  try {
    await call('crm.area.accesso.verify_code', {
      code: code.value.trim(),
    })
    show.value = false
    emit('verified')
  } catch (e) {
    error.value = __(messageOf(e))
  } finally {
    busy.value = false
  }
}
</script>
