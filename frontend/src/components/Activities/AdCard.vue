<!--
  The ad they actually clicked.

  Whoever calls a lead five minutes after it arrives is the person for whom this
  matters most: knowing what was promised in the ad is the difference between
  "hi, you filled in a form" and continuing a conversation the ad started. Today
  that means going hunting in Ads Manager, so it is here instead.

  It is deliberately quiet: if Meta will not say (no ads access on that account,
  an old ad) the card simply is not there. A lead is worth more than the picture
  of its ad.
-->
<template>
  <div
    v-if="ad.data?.ad_id"
    class="rounded-lg border border-outline-gray-2 px-3 py-2.5"
  >
    <div class="flex items-center justify-between gap-2 pb-2">
      <span class="text-p-base-medium text-ink-gray-7">
        {{ __('The ad they clicked') }}
      </span>
      <Badge v-if="stopped" :label="__(humanStatus)" theme="red" size="sm" />
    </div>
    <div class="flex gap-3">
      <img
        v-if="ad.data.thumbnail_url"
        :src="ad.data.thumbnail_url"
        :alt="ad.data.creative_title || ad.data.ad_name"
        class="size-16 shrink-0 rounded-md object-cover"
        @error="hideImage"
      />
      <div class="min-w-0 flex-1">
        <div class="truncate text-p-sm-medium text-ink-gray-8">
          {{ ad.data.creative_title || ad.data.ad_name || ad.data.ad_id }}
        </div>
        <div
          v-if="ad.data.creative_body"
          class="line-clamp-3 text-p-sm text-ink-gray-6"
        >
          {{ ad.data.creative_body }}
        </div>
        <div class="mt-1 flex items-center gap-2 text-p-sm text-ink-gray-5">
          <span class="truncate">
            {{
              [ad.data.campaign_name, ad.data.adset_name]
                .filter(Boolean)
                .join(' · ')
            }}
          </span>
          <a
            v-if="ad.data.permalink"
            :href="ad.data.permalink"
            target="_blank"
            rel="noopener"
            class="shrink-0 text-ink-blue-link"
          >
            {{ __('Open on Meta') }}
          </a>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { Badge, createResource } from 'frappe-ui'
import { computed } from 'vue'

const props = defineProps({
  doctype: { type: String, default: 'CRM Lead' },
  docname: { type: String, default: '' },
})

const ad = createResource({
  url: 'crm.integrations.meta.api.get_record_ad',
  params: { doctype: props.doctype, name: props.docname },
  auto: true,
})

// Meta's own vocabulary, in words somebody can act on
const WORDS = {
  DISAPPROVED: 'Rejected by Meta',
  WITH_ISSUES: 'Has issues',
  PENDING_REVIEW: 'Waiting for review',
  PAUSED: 'Paused',
  ADSET_PAUSED: 'Ad set paused',
  CAMPAIGN_PAUSED: 'Campaign paused',
}

const stopped = computed(() => {
  const status = ad.data?.effective_status
  return Boolean(status) && status !== 'ACTIVE'
})
const humanStatus = computed(
  () => WORDS[ad.data?.effective_status] || ad.data?.effective_status || '',
)

function hideImage(event) {
  // Meta's CDN links expire; a broken image frame is worse than no image
  event.target.style.display = 'none'
}
</script>
