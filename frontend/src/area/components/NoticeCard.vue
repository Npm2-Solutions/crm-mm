<!--
  How the person hears of news in their area: the email always; WhatsApp or SMS
  if the centre offers them and the person asks, to their own number that wrote
  to the centre - never to one typed here. The words are the same everywhere:
  there is news in the area, and the link.
-->
<template>
  <section v-if="options.data" class="flex flex-col gap-2">
    <h2 class="text-base font-medium text-ink-gray-7">
      {{ __('How we tell you there is news') }}
    </h2>
    <div class="flex flex-col gap-3 rounded-lg bg-surface-white p-4 shadow-sm">
      <p class="text-p-sm text-ink-gray-6">
        {{
          __(
            'We only say that there is news in your area, never what it is. By email always, to {0}.',
            [options.data.email],
          )
        }}
      </p>
      <div
        v-for="channel in options.data.channels"
        :key="channel.channel"
        class="flex items-center justify-between gap-3"
      >
        <span class="flex min-w-0 flex-col">
          <span class="text-p-base text-ink-gray-8">
            {{ __('Also on {0}', [channel.channel]) }}
          </span>
          <span class="text-p-sm text-ink-gray-5">
            {{
              channel.number
                ? __('to your number {0}', [channel.number])
                : __(
                    'Write to the centre once on {0} from your number, then you can turn this on.',
                    [channel.channel],
                  )
            }}
          </span>
        </span>
        <Switch
          class="shrink-0"
          :model-value="channel.on"
          :disabled="!channel.number || busy === channel.channel"
          :aria-label="__('Also on {0}', [channel.channel])"
          @update:model-value="(on) => set(channel, on)"
        />
      </div>
      <ErrorMessage :message="error" />
    </div>
  </section>
</template>

<script setup>
import { ErrorMessage, Switch, call, createResource } from 'frappe-ui'
import { ref } from 'vue'
import { messageOf } from '../store'

const busy = ref('')
const error = ref('')

const options = createResource({
  url: 'crm.clinica.area.avvisi.notice_options',
  auto: true,
})

async function set(channel, on) {
  busy.value = channel.channel
  error.value = ''
  try {
    options.data = await call('crm.clinica.area.avvisi.set_notice', {
      channel: channel.channel,
      on: on ? 1 : 0,
    })
  } catch (e) {
    error.value = __(messageOf(e))
  } finally {
    busy.value = ''
  }
}
</script>
