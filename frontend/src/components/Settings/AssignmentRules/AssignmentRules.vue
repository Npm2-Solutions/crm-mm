<template>
  <div
    class="flex h-full flex-col gap-6 p-6 text-ink-gray-8 max-md:px-3 max-md:py-5"
  >
    <!-- Header -->
    <div
      class="flex justify-between px-2 pt-2 max-md:flex-col max-md:items-start max-md:gap-3"
    >
      <div class="flex flex-col gap-1 w-9/12 max-md:w-full">
        <h2
          class="flex gap-2 text-2xl-semibold leading-tight md:h-5 md:leading-none"
        >
          {{ __('Assignment Rules') }}
        </h2>
        <p class="text-p-base text-ink-gray-6">
          {{
            __(
              'Auto-assign leads/deals to the right sales user based on predefined conditions',
            )
          }}
        </p>
      </div>
      <div
        class="flex items-start space-x-2 w-3/12 justify-end max-md:w-auto max-md:justify-start"
      >
        <Button
          :label="__('New')"
          icon-left="lucide-plus"
          variant="solid"
          @click="goToNew()"
        />
      </div>
    </div>

    <!-- Assignment rules list -->
    <div class="flex h-full overflow-y-auto">
      <AssignmentRulesList />
    </div>
  </div>
</template>

<script setup>
import AssignmentRulesList from './AssignmentRulesList.vue'
import { createResource } from 'frappe-ui'
import { inject, provide } from 'vue'

const updateStep = inject('updateStep')

const assignmentRulesListData = createResource({
  url: 'crm.api.assignment_rule.get_assignment_rules_list',
  cache: ['assignmentRules', 'get_assignment_rules_list'],
  auto: true,
})

provide('assignmentRulesList', assignmentRulesListData)

const goToNew = () => {
  updateStep('view', null)
}
</script>
