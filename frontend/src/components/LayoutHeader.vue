<template>
  <Teleport v-if="showHeader" to="#app-header">
    <slot>
      <!--
        The title gives way, the actions do not: the left side may shrink (the
        breadcrumbs truncate, then fold into «…»), the right side keeps its
        size. Without it a long name pushed the page's own buttons off the
        right edge of a phone — Save included.
      -->
      <header
        class="flex h-10.5 items-center justify-between gap-2 py-[7px] sm:pl-5 pl-2"
      >
        <div class="flex min-w-0 items-center gap-2">
          <slot name="left-header" />
        </div>
        <div class="flex shrink-0 items-center gap-2">
          <slot name="right-header" class="flex items-center gap-2" />
        </div>
      </header>
    </slot>
  </Teleport>
</template>
<script setup>
import { ref, nextTick } from 'vue'

const showHeader = ref(false)

nextTick(() => {
  showHeader.value = true
})
</script>
