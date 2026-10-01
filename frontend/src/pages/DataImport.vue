<template>
  <!--
    frappe-ui draws this page, header included, so the fit is made from here:
    its header was 48px tall where every other page's is 42, and in the list the
    status select took the whole row (FormControl makes selects full width) and
    squeezed the search box beside it to an empty 18px pill.
  -->
  <div
    class="h-full overflow-y-auto [&>header]:h-10.5 [&>header]:py-0 [&_.space-x-2.my-5>*:last-child]:w-40 [&_.space-x-2.my-5>*:last-child]:shrink-0"
  >
    <DataImport
      :doctype="route.params.doctype"
      :importName="route.params.importName"
      :doctypeMap="doctypeMap"
    />
  </div>
</template>

<script setup>
import { usePageMeta } from 'frappe-ui'
import { DataImport } from 'frappe-ui/frappe'
import { useRoute } from 'vue-router'

const route = useRoute()

// the titles in the user's words: frappe-ui writes them as it gets them
const doctypeMap = {
  'CRM Lead': {
    title: __('People'),
    listRoute: '/crm/leads',
    pageRoute: `/crm/leads/docname`,
  },
  'CRM Deal': {
    title: __('Deals'),
    listRoute: '/crm/deals',
    pageRoute: `/crm/deals/docname`,
  },
  Contact: {
    title: __('Contacts'),
    listRoute: '/crm/contacts',
    pageRoute: `/crm/contacts/docname`,
  },
  'CRM Task': {
    title: __('Tasks'),
    listRoute: '/crm/tasks',
  },
  'CRM Organization': {
    title: __('Organizations'),
    listRoute: '/crm/organizations',
    pageRoute: `/crm/organizations/docname`,
  },
  'CRM Call Log': {
    title: __('Call Log'),
    listRoute: '/crm/call-logs',
  },
}

usePageMeta(() => {
  return {
    title: __('Data Import'),
  }
})
</script>
