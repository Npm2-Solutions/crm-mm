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
  // The centre's own name and logo (Settings > Brand): the logo goes beside the
  // product's. The tab's icon is always the product's - the vertical's brand.
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
