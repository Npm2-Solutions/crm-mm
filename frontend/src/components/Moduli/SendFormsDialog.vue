<!--
  Forms the person fills on their own: a link by email, for home, or the desk's
  tablet handed over. The server says where a link goes (the person, or who
  signs for them) and which forms are filled away but signed at the desk.
-->
<template>
  <Dialog
    v-model="show"
    :options="{ title: __('Forms to fill on their own'), size: 'lg' }"
  >
    <template #body-content>
      <div v-if="!options && !error" class="flex justify-center py-8">
        <LoadingIndicator class="w-4" />
      </div>
      <div v-else-if="options" class="flex flex-col gap-4">
        <div class="flex flex-col gap-1.5">
          <TabButtons
            class="w-full [&_button>span]:w-full [&_button]:w-full [&_div]:w-full"
            :modelValue="mode"
            :buttons="modes"
            @update:modelValue="(value) => (mode = value)"
          />
          <p class="text-p-sm text-ink-gray-5">
            {{
              mode === 'link'
                ? __(
                    'An email with a link; a code to the same address opens it. The message does not say which forms.',
                  )
                : __(
                    'This device is handed to the person: you are logged out on it, and it shows only these forms.',
                  )
            }}
          </p>
        </div>

        <div class="flex flex-col gap-0.5">
          <span class="text-sm text-ink-gray-5">{{ __('Forms') }}</span>
          <p
            v-if="!options.templates.length"
            class="text-p-base text-ink-gray-6"
          >
            {{ __('Publish a form in Settings > Forms to send it.') }}
          </p>
          <label
            v-for="template in options.templates"
            :key="template.name"
            class="flex cursor-pointer items-start gap-2 rounded px-1.5 py-2 hover:bg-surface-gray-2"
          >
            <Checkbox
              class="touch-target mt-0.5 shrink-0"
              :modelValue="chosen.includes(template.name)"
              @update:modelValue="toggle(template.name)"
            />
            <span class="min-w-0 flex-1">
              <span class="block text-base text-ink-gray-8">{{
                template.title
              }}</span>
              <span
                v-if="template.sign_at_desk"
                class="block text-sm text-ink-gray-5"
              >
                {{
                  __('Filled on their own, signed at the desk: {0}', [
                    template.why,
                  ])
                }}
              </span>
            </span>
          </label>
        </div>

        <div
          v-if="mode === 'link'"
          class="rounded-lg bg-surface-gray-2 px-3 py-2.5 text-p-sm"
        >
          <span v-if="options.link.reason" class="text-ink-red-4">
            {{ options.link.reason }}
          </span>
          <span v-else class="text-ink-gray-7">
            {{
              options.link.for_them
                ? __('It goes to {0}, who answers for them, at {1}.', [
                    options.link.to,
                    options.link.address,
                  ])
                : __('It goes to {0} at {1}. The link lasts 7 days.', [
                    options.link.to,
                    options.link.address,
                  ])
            }}
          </span>
        </div>
        <div v-else class="flex flex-col gap-2">
          <FormControl
            v-if="options.representatives.length"
            v-model="holder"
            type="select"
            :label="__('Who holds the tablet')"
            :options="holders"
          />
          <p
            v-if="options.minor && !options.representatives.length"
            class="text-p-sm text-ink-red-4"
          >
            {{
              __(
                "A minor's forms are answered by a parent or guardian: add them to the related people first",
              )
            }}
          </p>
          <p class="text-p-sm text-ink-gray-5">
            {{ __('When the tablet comes back, log in again.') }}
          </p>
        </div>
      </div>
      <ErrorMessage class="mt-3" :message="error" />
    </template>
    <template #actions>
      <div class="dialog-footer flex justify-end gap-2">
        <Button :label="__('Cancel')" @click="show = false" />
        <Button
          variant="solid"
          :label="
            mode === 'link' ? __('Send the link') : __('Hand over the tablet')
          "
          :disabled="!ready"
          :loading="going"
          @click="go"
        />
      </div>
    </template>
  </Dialog>
</template>

<script setup>
import {
  Button,
  Checkbox,
  Dialog,
  ErrorMessage,
  FormControl,
  LoadingIndicator,
  TabButtons,
  call,
  toast,
} from 'frappe-ui'
import { computed, ref, watch } from 'vue'

const props = defineProps({
  lead: { type: String, required: true },
  // the forms the person owes, chosen already; the appointment they are for
  preselect: { type: Array, default: () => [] },
  appointment: { type: String, default: null },
})
const emit = defineEmits(['sent'])
const show = defineModel({ type: Boolean })

const options = ref(null)
const mode = ref('link')
const chosen = ref([])
const holder = ref('')
const error = ref('')
const going = ref(false)

const modes = [
  { label: __('Link by email'), value: 'link' },
  { label: __('Tablet at the desk'), value: 'tablet' },
]

const holders = computed(() => [
  ...(options.value?.minor
    ? []
    : [{ label: __('The person themselves'), value: '' }]),
  ...(options.value?.representatives || []).map((person) => ({
    label: person.label,
    value: person.name,
  })),
])

const ready = computed(() => {
  if (!options.value || !chosen.value.length) return false
  if (mode.value === 'link') return !options.value.link.reason
  return !(options.value.minor && !holder.value)
})

function toggle(name) {
  chosen.value = chosen.value.includes(name)
    ? chosen.value.filter((one) => one !== name)
    : [...chosen.value, name]
}

watch(
  show,
  async (open) => {
    if (!open) return
    options.value = null
    chosen.value = [...props.preselect]
    error.value = ''
    try {
      const found = await call('crm.moduli.richieste.get_send_options', {
        lead: props.lead,
      })
      options.value = found
      holder.value = found.minor ? found.representatives[0]?.name || '' : ''
      mode.value = found.link.reason ? 'tablet' : 'link'
    } catch (e) {
      error.value = e.messages?.join(' ') || e.message
    }
  },
  { immediate: true },
)

async function go() {
  going.value = true
  error.value = ''
  const templates = JSON.stringify(chosen.value)
  try {
    if (mode.value === 'link') {
      await call('crm.moduli.richieste.send_form_link', {
        lead: props.lead,
        templates,
        appointment: props.appointment,
      })
      toast.success(__('Link sent'))
      show.value = false
      emit('sent')
      return
    }
    const handed = await call('crm.moduli.richieste.hand_over_tablet', {
      lead: props.lead,
      templates,
      given_by: holder.value || '',
      appointment: props.appointment,
    })
    // the operator's session ends here: the person sees their forms only
    await call('logout')
    window.location.href = handed.url
  } catch (e) {
    error.value = e.messages?.join(' ') || e.message
  } finally {
    going.value = false
  }
}
</script>
