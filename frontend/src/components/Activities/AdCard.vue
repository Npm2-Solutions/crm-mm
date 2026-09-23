<!--
  The ad they actually clicked, as a row on the journey.

  Whoever calls a lead five minutes after it arrives is the person for whom this
  matters most: knowing what was promised in the ad is the difference between
  "hi, you filled in a form" and continuing a conversation the ad started. Today
  that means going hunting in Ads Manager, so it is here instead — and on the
  timeline rather than in a box above it, because seeing the ad is the first
  thing that happened to this person, not a footnote to it.

  It is deliberately quiet: if Meta will not say (no ads access on that account,
  an old ad) the row simply is not there. A lead is worth more than the picture
  of its ad.
-->
<template>
  <div v-if="ad?.ad_id" class="min-w-0">
    <div class="flex flex-wrap items-center gap-2 py-1">
      <Badge :label="__('Ad')" theme="orange" size="sm" />
      <span class="truncate text-base font-medium text-ink-gray-8">
        {{ ad.creative_title || ad.ad_name || ad.ad_id }}
      </span>
      <Badge v-if="stopped" :label="__(humanStatus)" theme="red" size="sm" />
    </div>
    <div class="flex gap-3 pt-1">
      <img
        v-if="ad.thumbnail_url"
        :src="ad.thumbnail_url"
        :alt="ad.creative_title || ad.ad_name"
        class="size-14 shrink-0 rounded-md object-cover"
        @error="hideImage"
      />
      <div class="min-w-0 flex-1">
        <div
          v-if="ad.creative_body"
          class="line-clamp-3 text-p-sm text-ink-gray-6"
        >
          {{ ad.creative_body }}
        </div>
        <div class="mt-1 flex items-center gap-2 text-p-sm text-ink-gray-5">
          <span class="truncate">
            {{ [ad.campaign_name, ad.adset_name].filter(Boolean).join(' · ') }}
          </span>
          <a
            v-if="ad.permalink"
            :href="ad.permalink"
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
import { Badge } from 'frappe-ui'
import { computed } from 'vue'

// The ad is fetched by the timeline, not here: it has to be placed in time
// alongside everything else, and a component that fetches its own data cannot
// be sorted into a list.
const props = defineProps({
  ad: { type: Object, default: () => ({}) },
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
  const status = props.ad?.effective_status
  return Boolean(status) && status !== 'ACTIVE'
})
const humanStatus = computed(
  () => WORDS[props.ad?.effective_status] || props.ad?.effective_status || '',
)

function hideImage(event) {
  // Meta's CDN links expire; a broken image frame is worse than no image
  event.target.style.display = 'none'
}
</script>
