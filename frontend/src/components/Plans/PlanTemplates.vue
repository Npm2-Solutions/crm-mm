<!--
  Copyright (c) 2026, NPM2 Solutions Srl and contributors
  For license information, please see license.txt

  Where a new plan starts from a template (crm.piani.modelli): one's own and the
  centre's shared ones of the plan's kind, each with what it holds and whose it
  is; one's own taken away from here. Nothing shows when there is none.
-->
<template>
  <div
    v-if="templates.data?.length"
    class="flex flex-col gap-2 rounded-lg bg-surface-gray-1 p-3"
  >
    <span class="text-sm font-medium text-ink-gray-7">
      {{ __('Start from a template') }}
    </span>
    <ul class="flex flex-col gap-1">
      <li
        v-for="template in templates.data"
        :key="template.name"
        class="flex items-center gap-2"
      >
        <button
          type="button"
          class="flex min-w-0 flex-1 flex-col rounded px-2 py-1.5 text-left hover:bg-surface-gray-2 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-outline-gray-3 disabled:opacity-60"
          :disabled="busy"
          @click="use(template)"
        >
          <span class="truncate text-base text-ink-gray-8">
            {{ template.title }}
          </span>
          <span class="truncate text-p-xs text-ink-gray-5">
            {{
              [
                template.moments === 1
                  ? __('one moment')
                  : __('{0} moments', [template.moments]),
                template.items === 1
                  ? __('one item')
                  : __('{0} items', [template.items]),
                template.mine ? '' : template.practitioner_name,
                template.shared ? __('for the whole centre') : '',
              ]
                .filter(Boolean)
                .join(' · ')
            }}
          </span>
        </button>
        <!-- removed after a second word: a template is lost for the whole centre -->
        <template v-if="template.mine && daTogliere === template.name">
          <Button
            size="sm"
            :label="__('Cancel')"
            class="shrink-0"
            @click="daTogliere = ''"
          />
          <Button
            size="sm"
            theme="red"
            variant="subtle"
            :label="__('Remove')"
            class="shrink-0"
            @click="remove(template)"
          />
        </template>
        <Button
          v-else-if="template.mine"
          variant="ghost"
          icon="trash-2"
          class="touch-target shrink-0"
          :aria-label="__('Remove the template {0}', [template.title])"
          @click="daTogliere = template.name"
        />
      </li>
    </ul>
  </div>
</template>

<script setup>
import { Button, call, createResource, toast } from 'frappe-ui'
import { ref } from 'vue'

const props = defineProps({
  planType: { type: String, required: true },
})
const emit = defineEmits(['use'])

const templates = createResource({
  url: 'crm.piani.modelli.get_templates',
  makeParams: () => ({ plan_type: props.planType }),
  auto: true,
})
const busy = ref(false)
// the template whose removal waits for its second word
const daTogliere = ref('')

async function use(template) {
  busy.value = true
  try {
    const content = await call('crm.piani.modelli.use_template', {
      name: template.name,
    })
    emit('use', content)
    if (content.left_out)
      toast.warning(
        content.left_out === 1
          ? __('One item was left out: the library no longer offers it')
          : __('{0} items were left out: the library no longer offers them', [
              content.left_out,
            ]),
      )
  } catch (e) {
    toast.error(e.messages?.join(' ') || e.message)
  } finally {
    busy.value = false
  }
}

async function remove(template) {
  daTogliere.value = ''
  try {
    await call('crm.piani.modelli.delete_template', { name: template.name })
    templates.reload()
  } catch (e) {
    toast.error(e.messages?.join(' ') || e.message)
  }
}

defineExpose({ reload: () => templates.reload() })
</script>
