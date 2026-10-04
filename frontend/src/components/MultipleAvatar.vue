<!--
  Modifications copyright (c) 2026, NPM2 Solutions Srl
-->
<template>
  <div
    v-if="avatars?.length"
    class="mr-1.5 flex cursor-pointer items-center"
    :class="[
      avatars?.length > 1 ? 'flex-row-reverse' : 'truncate [&>div]:truncate',
    ]"
  >
    <Tooltip v-if="avatars?.length == 1" :text="avatars[0].name">
      <div class="flex items-center gap-2 text-base">
        <Avatar
          shape="circle"
          :image="avatars[0].image"
          :label="avatars[0].label"
          :size="size"
        />
        <div v-if="withName" class="truncate">{{ avatars[0].label }}</div>
      </div>
    </Tooltip>
    <Tooltip
      v-for="avatar in reverseAvatars"
      v-else
      :key="avatar.name"
      :text="avatar.name"
    >
      <Avatar
        class="user-avatar -mr-1.5 transform ring-2 ring-outline-base transition hover:z-10 hover:scale-110"
        shape="circle"
        :image="avatar.image"
        :label="avatar.label"
        :size="size"
        :data-name="avatar.name"
      />
    </Tooltip>
  </div>
</template>
<script setup>
import { Avatar, Tooltip } from 'frappe-ui'
import { computed } from 'vue'

const props = defineProps({
  avatars: { type: Array, default: () => [] },
  size: { type: String, default: 'md' },
  // the name beside a single avatar: a phone's header keeps its room for the
  // page's own title
  withName: { type: Boolean, default: true },
})
const reverseAvatars = computed(() => [...props.avatars].reverse())
</script>
