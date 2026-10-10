<!--
  A subscription the centre sells from the area (crm/pagamenti/addebiti.py): what
  it is, what it comprises, what one pays, and «Buy». Never in the centre's
  preview: the page asks nothing for it there.
-->
<template>
  <article class="area-card flex flex-col gap-2">
    <h3 class="area-row__title min-w-0">{{ item.title }}</h3>
    <p v-if="item.description" class="text-p-sm text-ink-gray-7">
      {{ item.description }}
    </p>
    <p class="text-p-sm text-ink-gray-6">
      {{
        [cosaDa(item, t), item.services.join(', ')].filter(Boolean).join(' · ')
      }}
    </p>
    <div class="flex flex-wrap items-center justify-between gap-2">
      <span class="text-p-base font-medium text-ink-gray-8">
        {{ prezzoDellAcquisto(item, t) }}
      </span>
      <Button
        variant="solid"
        size="md"
        class="touch-target shrink-0"
        :label="__('Buy')"
        @click="emit('buy', item)"
      />
    </div>
  </article>
</template>

<script setup>
import { cosaDa, prezzoDellAcquisto } from '@/utils/abbonamenti'
import { Button } from 'frappe-ui'

defineProps({ item: { type: Object, required: true } })
const emit = defineEmits(['buy'])
const t = (text, args) => __(text, args)
</script>
