<!--
  Copyright (c) 2026, NPM2 Solutions Srl and contributors
  For license information, please see license.txt

  The first steps in the sidebar (doc 37): how many are done, and the way into
  the panel; with the sidebar collapsed, an icon. Nothing once they are all done,
  or hidden.
-->
<template>
  <template v-if="visibili">
    <div
      v-if="!collapsed"
      class="flex flex-col gap-2.5 rounded-lg bg-surface-elevation-2 px-3 py-2.5 shadow-sm"
    >
      <div class="flex items-start gap-2">
        <LucideListChecks
          class="mt-0.5 size-4 shrink-0 text-[var(--brand-action)]"
          aria-hidden="true"
        />
        <div class="flex min-w-0 flex-1 flex-col gap-0.5">
          <span class="text-p-sm font-medium text-ink-gray-9">
            {{ __('First steps') }}
          </span>
          <span class="text-p-sm text-ink-gray-6">
            {{ __('{0} of {1} done', [stato.fatti, stato.totale]) }}
          </span>
        </div>
      </div>
      <div
        class="h-1 overflow-hidden rounded-full bg-surface-gray-3"
        role="progressbar"
        :aria-label="__('First steps')"
        :aria-valuenow="stato.percentuale"
        aria-valuemin="0"
        aria-valuemax="100"
      >
        <div
          class="h-full rounded-full bg-[var(--brand-segno)]"
          :style="{ width: `${stato.percentuale}%` }"
        />
      </div>
      <Button
        variant="solid"
        :label="stato.fatti ? __('Continue') : __('Begin')"
        icon-right="lucide-chevron-right"
        @click="apriPannello"
      />
    </div>
    <Tooltip v-else :text="__('First steps')" placement="right">
      <Button
        variant="ghost"
        class="w-full"
        :aria-label="__('First steps')"
        @click="apriPannello"
      >
        <LucideListChecks class="size-4 text-[var(--brand-action)]" />
      </Button>
    </Tooltip>
  </template>
</template>

<script setup>
import LucideListChecks from '~icons/lucide/list-checks'
import { usePrimiPassi } from '@/composables/primiPassi'
import { Tooltip } from 'frappe-ui'

defineProps({
  collapsed: { type: Boolean, default: false },
})

const { stato, visibili, apriPannello } = usePrimiPassi()
</script>
