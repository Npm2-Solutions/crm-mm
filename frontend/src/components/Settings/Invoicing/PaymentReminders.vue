<!--
  Copyright (c) 2026, NPM2 Solutions Srl and contributors
  For license information, please see license.txt

  How the clients pay, and the reminders of what they still owe
  (crm/invoicing/solleciti.py): what the centre writes on how to pay is shown
  in the client area beside what is left to pay; the reminders start off.
-->
<template>
  <div
    class="flex h-full flex-col gap-6 overflow-y-auto py-8 px-6 text-ink-gray-8 max-md:px-3 max-md:py-5"
  >
    <div class="flex flex-col gap-1 px-2">
      <h2
        class="flex gap-2 text-2xl-semibold leading-tight md:h-5 md:leading-none"
      >
        {{ __('Payments and reminders') }}
      </h2>
      <p class="text-p-base text-ink-gray-6">
        {{
          __(
            'How the clients pay, and a polite reminder of the invoices they still have to pay.',
          )
        }}
      </p>
    </div>
    <div class="px-2">
      <DocFields
        doctype="CRM Payment Reminder Settings"
        docname="CRM Payment Reminder Settings"
        :scroll="false"
      />
    </div>
  </div>
</template>

<script setup>
import DocFields from '@/components/Settings/Invoicing/DocFields.vue'
</script>
