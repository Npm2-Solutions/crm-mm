<!--
  One attribution snapshot — the campaign that introduced this person, or the
  one that brought them back — as a row on the journey.

  Blank fields are dropped rather than shown empty: a direct visit has no
  campaign, and a row reading "Campaign: —" is noise.
-->
<template>
  <div class="min-w-0">
    <!--
      With the ad rendered directly above, its own heading would be a second
      title for one thing: the attribution is not a separate event, it is the
      same arrival written in another vocabulary.
    -->
    <div v-if="heading" class="flex flex-wrap items-center gap-2 py-1">
      <Badge
        v-if="touch?.category"
        :label="__(touch.category)"
        :theme="theme"
        size="sm"
      />
      <span class="truncate text-base font-medium text-ink-gray-8">
        {{ title }}
      </span>
    </div>
    <div
      v-if="rows.length"
      class="flex flex-wrap gap-x-3 gap-y-0.5 text-p-sm"
      :class="heading ? '' : 'pt-1.5'"
    >
      <!--
        Each pair is its own flex row with a gap. A space written inside the
        markup does not survive: the template's own newline and indentation
        collapse it away, and what reaches the screen is «Sourcefacebook».
      -->
      <span
        v-for="row in rows"
        :key="row.label"
        class="flex min-w-0 items-baseline gap-1"
      >
        <span class="shrink-0 text-ink-gray-5">{{ row.label }}</span>
        <span class="truncate text-ink-gray-7" :title="row.value">
          {{ row.value }}
        </span>
      </span>
    </div>
    <div v-else class="text-p-sm text-ink-gray-5">{{ __('Not recorded') }}</div>
  </div>
</template>

<script setup>
import { Badge } from 'frappe-ui'
import { computed } from 'vue'

const props = defineProps({
  title: { type: String, required: true },
  touch: { type: Object, default: () => ({}) },
  theme: { type: String, default: 'blue' },
  heading: { type: Boolean, default: true },
})

// A lead ad fills the same three slots with an ad, an ad set and a campaign.
// "Content: Promo Autunno" is the right value under the wrong word, so the
// words follow where the person came from.
const rows = computed(() => {
  const t = props.touch || {}
  const fromAnAd = t.landing_page === 'lead_ad_form'
  return [
    { label: __('Source'), value: t.source },
    { label: __('Medium'), value: t.medium },
    { label: __('Campaign'), value: t.campaign },
    { label: fromAnAd ? __('Ad set') : __('Term'), value: t.term },
    { label: fromAnAd ? __('Ad') : __('Content'), value: t.content },
    {
      label: __('Landing page'),
      value: fromAnAd ? __('Lead form') : t.landing_page,
    },
    { label: __('Referrer'), value: t.referrer },
  ].filter((row) => row.value)
})
</script>
