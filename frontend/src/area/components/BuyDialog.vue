<!--
  «Buy» a subscription from the area: what it is, from today until when, what one
  pays and - paid by the month - the words the person agrees to before the card is
  kept for the next instalments. «Go to payment» opens Stripe's page; the
  subscription starts once the payment arrives.
-->
<template>
  <Dialog v-model="show" :options="{ title: item?.title || '', size: 'md' }">
    <template #body-content>
      <div v-if="item" class="flex flex-col gap-3">
        <p v-if="item.description" class="text-p-base text-ink-gray-8">
          {{ item.description }}
        </p>
        <dl class="flex flex-col gap-2">
          <div class="flex flex-col">
            <dt class="area-label">{{ __('What it comprises') }}</dt>
            <dd class="text-p-base text-ink-gray-8">
              {{
                [cosaDa(item, t), item.services.join(', ')]
                  .filter(Boolean)
                  .join(' · ')
              }}
            </dd>
          </div>
          <div class="flex flex-col">
            <dt class="area-label">{{ __('When') }}</dt>
            <dd class="text-p-base text-ink-gray-8">
              {{ __('From today until {0}', [day(item.until)]) }}
            </dd>
          </div>
          <div class="flex flex-col">
            <dt class="area-label">{{ __('You pay') }}</dt>
            <dd class="text-p-base text-ink-gray-8">
              {{ prezzoDellAcquisto(item, t) }}
            </dd>
          </div>
        </dl>
        <p
          v-if="item.monthly"
          class="rounded-[12px_12px_12px_2px] bg-[var(--brand-subtle)] px-3 py-2 text-p-sm text-[var(--on-brand-subtle)]"
        >
          {{ mandatoInParole(item, t, day) }}
        </p>
        <p class="text-p-sm text-ink-gray-6">
          {{
            __(
              'You pay by card on Stripe, the centre’s payment service: the centre never sees the card. The invoice comes in your Documents once paid.',
            )
          }}
        </p>
        <ErrorMessage :message="error" />
      </div>
    </template>
    <template #actions>
      <div class="flex flex-wrap justify-end gap-2">
        <Button size="md" :label="__('Cancel')" @click="show = false" />
        <Button
          size="md"
          variant="solid"
          :label="__('Go to payment')"
          :loading="busy"
          @click="buy"
        />
      </div>
    </template>
  </Dialog>
</template>

<script setup>
import {
  cosaDa,
  mandatoInParole,
  prezzoDellAcquisto,
} from '@/utils/abbonamenti'
import { Button, Dialog, ErrorMessage, call } from 'frappe-ui'
import { ref, watch } from 'vue'
import { day } from '../dates'
import { area } from '../store'

const props = defineProps({ item: { type: Object, default: null } })
const show = defineModel({ type: Boolean })
const t = (text, args) => __(text, args)

const busy = ref(false)
const error = ref('')

watch(show, (open) => {
  if (open) error.value = ''
})

async function buy() {
  busy.value = true
  error.value = ''
  try {
    const link = await call('crm.area.api.buy_subscription', {
      person: area.person,
      subscription_type: props.item.name,
    })
    window.location.href = link.url
  } catch (e) {
    busy.value = false
    error.value =
      e.messages?.[0] || __('The payment could not start: try again.')
  }
}
</script>
