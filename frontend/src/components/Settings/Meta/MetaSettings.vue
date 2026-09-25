<!--
  Meta, in one place: the connection, and what it feeds.

  These were four pages side by side in the settings list, between the Social
  Planner and WhatsApp, and nothing said they were one integration — "Lead
  quality" could have belonged to anything. Now they are the tabs of the page
  that connects them, under Integrations, and the connection's state is loaded
  once, here, for all of them.
-->
<template>
  <div
    class="flex h-full flex-col gap-5 overflow-y-auto px-4 py-6 sm:px-6 sm:py-8 text-ink-gray-8"
  >
    <div class="flex flex-col gap-1 px-2">
      <h2 class="flex items-center gap-2 text-2xl-semibold leading-none h-5">
        {{ __('Meta') }}
        <Badge
          v-if="status.data"
          :label="connected ? __('Connected') : __('Not connected')"
          :theme="connected ? 'green' : 'gray'"
          size="sm"
        />
      </h2>
      <p class="text-p-base text-ink-gray-6">
        {{
          __(
            'Facebook and Instagram: the leads from your ads, what they cost, and the Pages the Social Planner publishes to.',
          )
        }}
      </p>
    </div>

    <div class="px-2">
      <TabButtons v-model="tab" :buttons="tabs" />
    </div>

    <MetaConnection
      v-if="tab === 'connection'"
      :status="status"
      @navigate="navigate"
    />
    <MetaLeadForms
      v-else-if="tab === 'leads'"
      :status="status"
      @navigate="navigate"
    />
    <MetaAdSpend
      v-else-if="tab === 'ads'"
      :status="status"
      @navigate="navigate"
    />
    <MetaLeadQuality
      v-else-if="tab === 'quality'"
      :status="status"
      @navigate="navigate"
    />
  </div>
</template>

<script setup>
import MetaConnection from '@/components/Settings/Meta/MetaConnection.vue'
import MetaLeadForms from '@/components/Settings/Meta/MetaLeadForms.vue'
import MetaAdSpend from '@/components/Settings/Meta/MetaAdSpend.vue'
import MetaLeadQuality from '@/components/Settings/Meta/MetaLeadQuality.vue'
import { activeSettingsPage } from '@/composables/settings'
import { onOAuthResult } from '@/composables/oauthPopup'
import { Badge, createResource, TabButtons } from 'frappe-ui'
import { computed, ref, watch } from 'vue'

const tabs = [
  { label: __('Connection'), value: 'connection' },
  { label: __('Lead Ads'), value: 'leads' },
  { label: __('Ad performance'), value: 'ads' },
  { label: __('Lead quality'), value: 'quality' },
]

// the names these tabs had when they were pages of their own: a link or a
// button that still uses one lands on the right tab
const TAB_OF_PAGE = {
  'Meta connection': 'connection',
  'Lead forms': 'leads',
  'Ad performance': 'ads',
  'Lead quality': 'quality',
}

const tab = ref('connection')

watch(
  activeSettingsPage,
  (page) => {
    if (TAB_OF_PAGE[page]) tab.value = TAB_OF_PAGE[page]
  },
  { immediate: true },
)

const status = createResource({
  url: 'crm.integrations.meta.api.get_status',
  auto: true,
})

const connected = computed(() => Boolean(status.data?.connected))

// The Facebook popup can come back while another tab is open, and the tab that
// opened it — the one that says so — is gone by then. The state it changed
// belongs to the whole page, so the page listens too.
onOAuthResult('meta', () => status.reload())

// a tab of this page, or another settings page altogether
function navigate(where) {
  if (tabs.some((t) => t.value === where)) tab.value = where
  else activeSettingsPage.value = where
}
</script>
