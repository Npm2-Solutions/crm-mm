<template>
  <div>
    <slot name="header" v-bind="{ opened, hide, open, close, toggle }">
      <div
        v-if="!hide"
        class="section-header flex items-center justify-between"
        :class="headerClass"
      >
        <div
          class="flex text-ink-gray-9 max-w-fit items-center gap-2 text-base"
          :class="labelClass"
        >
          <!-- a section folds from a button that says whether it is open
               (APG disclosure): the header was a div with a click, which no
               key reached, so a section that starts folded (a person's
               company, their billing details) stayed shut to a keyboard. The
               count is not part of its name -->
          <button
            v-if="collapsible"
            type="button"
            class="flex min-w-0 items-center gap-2 rounded text-left"
            :aria-expanded="opened"
            @click="toggle()"
          >
            <span
              v-if="collapseIconPosition === 'left'"
              class="lucide-chevron-right h-4 transition-all duration-300 ease-in-out"
              :class="{ 'rotate-90': opened }"
              aria-hidden="true"
            />
            <span>
              {{ __(label) || __('Untitled') }}
            </span>
            <span
              v-if="collapseIconPosition === 'right'"
              class="lucide-chevron-right h-4 transition-all duration-300 ease-in-out"
              :class="{ 'rotate-90': opened }"
              aria-hidden="true"
            />
          </button>
          <span v-else>
            {{ __(label) || __('Untitled') }}
          </span>
          <Badge
            v-if="count"
            :label="count"
            :variant="countVariant"
            :theme="countTheme"
          />
        </div>
        <slot name="actions"></slot>
      </div>
    </slot>
    <transition
      enter-active-class="duration-300 ease-in"
      leave-active-class="duration-300 ease-[cubic-bezier(0, 1, 0.5, 1)]"
      enter-to-class="max-h-[200px] overflow-hidden"
      leave-from-class="max-h-[200px] overflow-hidden"
      enter-from-class="max-h-0 overflow-hidden"
      leave-to-class="max-h-0 overflow-hidden"
    >
      <div v-show="opened" class="columns" v-bind="$attrs">
        <slot v-bind="{ opened, open, close, toggle }" />
      </div>
    </transition>
  </div>
</template>
<script setup>
import { Badge } from 'frappe-ui'
import { ref } from 'vue'

const props = defineProps({
  label: { type: String, default: '' },
  count: { type: [String, Number], default: '' },
  countVariant: { type: String, default: 'subtle' },
  countTheme: { type: String, default: 'gray' },
  hideLabel: { type: Boolean, default: false },
  opened: { type: Boolean, default: true },
  collapsible: { type: Boolean, default: true },
  collapseIconPosition: { type: String, default: 'left' },
  labelClass: { type: [String, Object, Array], default: '' },
  headerClass: { type: [String, Object, Array], default: '' },
})

const hide = ref(props.hideLabel)
const opened = ref(props.opened)

function toggle() {
  opened.value = !opened.value
}

function open() {
  opened.value = true
}

function close() {
  opened.value = false
}
</script>
<script>
export default {
  inheritAttrs: false,
}
</script>
