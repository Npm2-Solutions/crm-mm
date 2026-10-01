import { createDocumentResource } from 'frappe-ui'
import { reactive, ref } from 'vue'
import { marchio } from '@/utils/marchio'

const settings = ref({})
const brand = reactive({})

const _settings = createDocumentResource({
  doctype: 'FCRM Settings',
  name: 'FCRM Settings',
  onSuccess: (data) => {
    settings.value = data
    getSettings().setupBrand()
    return data
  },
})

export function getSettings() {
  // The centre's own name and logo (Settings > General > Name & logo): they lead
  // on the pages its people open (crm.marchio). The sidebar's logo and the tab's
  // icon are always the product's - the vertical's brand.
  function setupBrand() {
    brand.name = settings.value?.brand_name
    brand.logo = settings.value?.brand_logo
    brand.favicon = marchio().favicon
  }

  return {
    _settings,
    settings,
    brand,
    setupBrand,
  }
}
