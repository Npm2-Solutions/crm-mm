<!--
  Modifications copyright (c) 2026, NPM2 Solutions Srl
-->
<template>
  <div
    class="flex h-full flex-col gap-6 py-8 px-6 text-ink-gray-8 max-md:px-3 max-md:py-5"
  >
    <div
      class="flex justify-between px-2 text-ink-gray-8 impostazioni-strette:flex-col impostazioni-strette:items-start impostazioni-strette:gap-3"
    >
      <div class="flex flex-col gap-1">
        <h2
          class="flex gap-2 text-2xl-semibold leading-tight md:h-5 md:leading-none"
        >
          {{ __('Dashboard') }}
        </h2>
        <p class="text-p-base text-ink-gray-6">
          {{
            __(
              'Configure how your dashboard calculates, formats, and displays key metrics, including forecasting, deal values, and currency settings',
            )
          }}
        </p>
      </div>
      <div
        class="flex items-start space-x-2 w-3/12 justify-end impostazioni-strette:w-auto impostazioni-strette:justify-start"
      >
        <AzioneImpostazioni
          v-if="settings.isDirty"
          :loading="settings.loading"
          @click="updateSettings"
        />
      </div>
    </div>

    <!-- the settings arrive after the page: opened by a link, it was drawn on
         a document not there yet -->
    <div v-if="settings.doc" class="flex-1 flex flex-col overflow-y-auto">
      <div class="flex items-center justify-between gap-4 py-3 px-2">
        <div class="flex min-w-0 flex-col">
          <div class="text-p-base-medium text-ink-gray-7">
            {{ __('Enable Forecasting') }}
          </div>
          <div class="text-p-sm text-ink-gray-5">
            {{
              __(
                'Makes "Expected Closure Date" and "Expected Deal Value" mandatory for deal value forecasting',
              )
            }}
          </div>
        </div>
        <div>
          <Switch
            v-model="settings.doc.enable_forecasting"
            :aria-label="__('Enable Forecasting')"
            size="sm"
          />
        </div>
      </div>
      <!-- no switch to add a deal's products up: a deal has no products to add
           any more, its value comes from its quotes (doc 50) -->
      <div class="h-px border-t mx-2 border-outline-elevation-2" />
      <div class="flex items-center justify-between gap-8 py-3 px-2">
        <div class="flex min-w-0 flex-col">
          <div class="text-p-base-medium text-ink-gray-7">
            {{ __('Dashboard Currency') }}
          </div>
          <div class="text-p-sm text-ink-gray-5">
            {{
              __(
                'The currency the dashboard and the deals count in. Until one is chosen it is the centre’s country’s; once chosen, it stays.',
              )
            }}
          </div>
        </div>
        <div>
          <div v-if="settings.doc?.currency" class="text-base text-ink-gray-8">
            {{ nomeDellaValuta(settings.doc.currency, appLocale()) }}
          </div>
          <!-- none chosen counts in the country's: the placeholder says so,
               and a choice asks first, since it stays -->
          <CampoValuta
            v-else
            class="w-48 max-md:w-full"
            :aria-label="__('Dashboard Currency')"
            :placeholder="__('The currency of the centre’s country')"
            @update:modelValue="(v) => v && setCurrency(v)"
          />
        </div>
      </div>
      <!-- which service tells the day's exchange rates is the agency's, as
           its key is (doc 30): a centre reads no list of services' names -->
      <div
        v-if="tecnico"
        class="h-px border-t mx-2 border-outline-elevation-2"
      />
      <div
        v-if="tecnico"
        class="flex items-center justify-between gap-8 py-3 px-2"
      >
        <div class="flex min-w-0 flex-col">
          <div class="text-p-base-medium text-ink-gray-7">
            {{ __('Exchange Rate Provider') }}
          </div>
          <div class="text-p-sm text-ink-gray-5">
            {{ __('Configure the exchange rate provider for {brand}') }}
          </div>
        </div>
        <div class="flex items-center gap-2">
          <FormControl
            v-model="settings.doc.service_provider"
            type="select"
            :aria-label="__('Exchange Rate Provider')"
            class="w-44"
            :options="[
              { label: 'Frankfurter', value: 'frankfurter.app' },
              {
                label: 'Fawaz Ahmed Exchange API',
                value: 'fawazahmed-exchange-api',
              },
              { label: 'Exchangerate Host', value: 'exchangerate.host' },
              { label: 'Exchangerate API', value: 'exchangerate-api' },
            ]"
            :placeholder="__('Select Provider')"
            :disabled="!settings.doc?.currency"
            @update:modelValue="() => tecnico && (settings.doc.access_key = '')"
          />
        </div>
      </div>
      <div
        v-if="requiresAccessKey && tecnico"
        class="h-px border-t mx-2 border-outline-elevation-2"
      />
      <div
        v-if="requiresAccessKey && tecnico"
        class="flex items-center justify-between gap-8 p-3"
      >
        <div class="flex min-w-0 flex-col">
          <div class="text-p-base-medium text-ink-gray-7">
            {{ __('Access Key') }}
          </div>
          <div class="text-p-sm text-ink-gray-5">
            {{
              __('Access key for {0}. Required for fetching exchange rates.', [
                providerMeta.label,
              ])
            }}
          </div>
          <div class="text-p-sm text-ink-gray-5">
            {{ __('You can get your access key from ') }}
            <a
              class="hover:underline text-ink-gray-7"
              :href="providerMeta.docsUrl"
              target="_blank"
            >
              {{ __(providerMeta.docsLabel) }}
            </a>
          </div>
        </div>
        <div class="flex items-center gap-2">
          <FormControl
            v-model="settings.doc.access_key"
            type="password"
            class="w-44"
            :placeholder="__('Enter Access Key')"
            :disabled="!settings.doc?.currency"
          />
        </div>
      </div>
    </div>
    <div v-if="errorMessage" class="px-3">
      <ErrorMessage :message="__(errorMessage)" />
    </div>
  </div>
</template>
<script setup>
import AzioneImpostazioni from '@/components/Settings/AzioneImpostazioni.vue'
import CampoValuta from '@/components/Controls/CampoValuta.vue'
import { getSettings } from '@/stores/settings'
import { appLocale } from '@/utils/locale'
import { nomeDellaValuta } from '@/utils/valute'
import { globalStore } from '@/stores/global'
import { usersStore } from '@/stores/users'
import { useBroadcast } from '@/composables/useBroadcast'
import { ErrorMessage, FormControl, Switch, toast } from 'frappe-ui'
import { useRoute } from 'vue-router'
import { ref, computed } from 'vue'

const route = useRoute()

const { _settings: settings } = getSettings()
const { $dialog } = globalStore()
const { send } = useBroadcast()

const errorMessage = ref('')

// keys and endpoints are the agency's
const tecnico = usersStore().puo('tecnico.integrazioni')

const PROVIDERS_REQUIRING_KEY = ['exchangerate.host', 'exchangerate-api']

const PROVIDER_META = {
  'exchangerate.host': {
    label: 'Exchangerate Host',
    docsUrl: 'https://exchangerate.host/#/docs/access_key',
    docsLabel: 'exchangerate.host',
  },
  'exchangerate-api': {
    label: 'Exchangerate API',
    docsUrl: 'https://www.exchangerate-api.com',
    docsLabel: 'exchangerate-api.com',
  },
}

const serviceProvider = computed(() => settings.doc?.service_provider)
const requiresAccessKey = computed(() =>
  PROVIDERS_REQUIRING_KEY.includes(serviceProvider.value),
)
const providerMeta = computed(() => PROVIDER_META[serviceProvider.value])

function updateSettings() {
  settings.save.submit(null, {
    validate: () => {
      errorMessage.value = ''
      if (!settings.doc?.currency) {
        errorMessage.value = __('Please select a currency before saving.')
        return errorMessage.value
      }
      if (requiresAccessKey.value && tecnico && !settings.doc.access_key) {
        errorMessage.value = __('Please enter the {0} access key.', [
          providerMeta.value.label,
        ])
        return errorMessage.value
      }
    },
    onSuccess: () => {
      toast.success(__('Dashboard settings updated successfully'))

      if (route.name === 'Deal') {
        send('reload-deal-sections')
      }
    },
  })
}

function setCurrency(value) {
  $dialog({
    title: __('Set Currency'),
    message: __(
      'Are you sure you want to set the currency as {0}? This cannot be changed later.',
      [nomeDellaValuta(value, appLocale())],
    ),
    variant: 'solid',
    theme: 'blue',
    actions: [
      {
        label: __('Save'),
        variant: 'solid',
        onClick: (close) => {
          settings.doc.currency = value
          settings.save.submit(null, {
            onSuccess: () => {
              toast.success(
                __('Currency set as {0} successfully', [
                  nomeDellaValuta(value, appLocale()),
                ]),
              )
              close()
            },
          })
        },
      },
    ],
  })
}
</script>
