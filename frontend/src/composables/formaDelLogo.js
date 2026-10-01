// Copyright (c) 2026, NPM2 Solutions Srl and contributors
// The shape of a logo where a page draws it: DottorCloud's sidebar, the client
// area (which must not load DottorCloud's stores: it is built apart).
import { misuraIlLogo } from '@/utils/marchio'
import { ref, toValue, watch } from 'vue'

// 'wide', 'square', or '' until it is known: what the server measured (`nota`),
// else what the browser does once it has the image.
export function useFormaDelLogo(url, nota = '') {
  const forma = ref(toValue(nota) || '')
  watch(
    () => [toValue(url), toValue(nota)],
    async ([indirizzo, saputa]) => {
      forma.value = saputa || ''
      const misurata = await misuraIlLogo(indirizzo, saputa)
      if (toValue(url) === indirizzo) forma.value = misurata
    },
    { immediate: true },
  )
  return forma
}
