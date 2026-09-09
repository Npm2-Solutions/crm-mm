<template>
  <div class="flex h-full flex-col gap-6">
    <div class="flex justify-between">
      <div class="flex flex-col gap-1 w-9/12">
        <div class="flex gap-1 items-center">
          <Button
            v-if="back"
            variant="ghost"
            icon-left="lucide-chevron-left"
            :label="title || __(doctype)"
            size="md"
            class="cursor-pointer -ml-4 hover:bg-transparent focus:bg-transparent focus:outline-none focus:ring-0 focus:ring-offset-0 focus-visible:none active:bg-transparent active:outline-none active:ring-0 active:ring-offset-0 active:text-ink-gray-5 text-2xl-semibold hover:opacity-70 !pr-0 !max-w-96 !justify-start"
            @click="back"
          />
          <h2
            v-else
            class="flex gap-2 text-2xl-semibold leading-none h-5 text-ink-gray-8"
          >
            {{ title || __(doctype) }}
          </h2>
          <Badge
            v-if="data.isDirty"
            :label="__('Not Saved')"
            variant="subtle"
            theme="orange"
          />
        </div>
      </div>
      <div class="flex item-center space-x-2 w-3/12 justify-end">
        <Button
          :loading="data.save.loading"
          :label="__('Update')"
          variant="solid"
          @click="data.save.submit()"
        />
      </div>
    </div>
    <div v-if="!data.get.loading" class="flex-1 overflow-y-auto">
      <FieldLayout
        v-if="data?.doc && tabs"
        :tabs="tabs"
        :data="data.doc"
        :doctype="doctype"
      />
    </div>
    <div v-else class="flex flex-1 items-center justify-center">
      <LoadingIndicator class="size-8" />
    </div>
    <ErrorMessage :message="data.save.error" />
  </div>
</template>
<script setup>
import FieldLayout from '@/components/FieldLayout/FieldLayout.vue'
import {
  createDocumentResource,
  createResource,
  LoadingIndicator,
  Badge,
  toast,
  ErrorMessage,
} from 'frappe-ui'
import { buildTabs } from '@/utils/settingsTabs'
import { computed } from 'vue'

const props = defineProps({
  doctype: { type: String, required: true },
  title: { type: String, default: '' },
  successMessage: { type: String, default: 'Updated successfully' },
  back: { type: Function, default: null },
})

const fields = createResource({
  url: 'crm.api.doc.get_fields',
  cache: ['fields', props.doctype],
  params: {
    doctype: props.doctype,
    allow_all_fieldtypes: true,
  },
  auto: true,
})

const data = createDocumentResource({
  doctype: props.doctype,
  name: props.doctype,
  fields: ['*'],
  auto: true,
  setValue: {
    onSuccess: () => {
      toast.success(__(props.successMessage))
    },
    onError: (err) => {
      toast.error(err.message + ': ' + err.messages[0])
    },
  },
})

const tabs = computed(() => buildTabs(fields.data))
</script>
