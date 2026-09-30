<!--
  Getting started: the steps that set the centre up, in a panel over the page.
  frappe-ui's steps, with the product's name and icon; in place of frappe-ui's
  help modal, whose help centre opened another product's documentation. The
  banner in the sidebar opens it while steps are left, "Getting started" after.
-->
<template>
  <div
    v-show="show"
    class="fixed right-0 z-50 m-5 mt-[62px] flex h-[calc(100%_-_80px)] w-80 flex-col gap-2 rounded-lg bg-surface-elevation-2 p-3 text-ink-gray-9 shadow-2xl"
    :class="{ 'top-[calc(100%_-_120px)] border': minimize }"
    @click.stop
  >
    <div class="flex items-center justify-between px-2 py-1.5">
      <div class="text-base font-medium">{{ __('Getting started') }}</div>
      <div class="flex gap-1">
        <Button
          variant="ghost"
          :aria-label="minimize ? __('Expand') : __('Minimise')"
          @click="minimize = !minimize"
        >
          <component
            :is="minimize ? LucideMaximize : LucideMinimize"
            class="size-3.5"
          />
        </Button>
        <Button
          variant="ghost"
          icon="x"
          :aria-label="__('Close')"
          @click="show = false"
        />
      </div>
    </div>
    <div class="flex h-full flex-col overflow-hidden">
      <OnboardingSteps
        title="DottorCloud"
        :logo="CRMLogo"
        :app-name="appName"
        :after-skip="afterSkip"
        :after-skip-all="afterSkipAll"
        :after-reset="afterReset"
        :after-reset-all="afterResetAll"
      />
    </div>
  </div>
</template>

<script setup>
import CRMLogo from '@/components/Icons/CRMLogo.vue'
import LucideMaximize from '~icons/lucide/maximize-2'
import LucideMinimize from '~icons/lucide/minimize-2'
import { Button } from 'frappe-ui'
import { OnboardingSteps, minimize } from 'frappe-ui/frappe'

defineProps({
  // where the steps done are kept for the user: frappe-ui's key, unchanged so
  // nobody's progress is lost
  appName: { type: String, default: 'frappecrm' },
  afterSkip: { type: Function, default: () => {} },
  afterSkipAll: { type: Function, default: () => {} },
  afterReset: { type: Function, default: () => {} },
  afterResetAll: { type: Function, default: () => {} },
})

const show = defineModel({ type: Boolean })
</script>
