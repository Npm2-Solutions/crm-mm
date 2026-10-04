// Copyright (c) 2026, NPM2 Solutions Srl and contributors
// For license information, please see license.txt

import { defineAsyncComponent, h, ref, watch } from 'vue'
import LoaderMark from '@/components/Espresso/LoaderMark.vue'

// what a page shows while it arrives, when it takes long enough to be seen
const Attesa = {
  name: 'Attesa',
  render: () => h('div', { class: 'flex justify-center py-12' }, h(LoaderMark)),
}

/**
 * A part of DottorCloud that comes when it is opened, not with the first page:
 * a settings page, a dialog. Imported at the top of what is always mounted, it
 * was in every page's first download - on a phone, every settings page with
 * the text editor and the phone's SDK, before the reception desk could show.
 * Quick, nothing shows; slow, the brand's loader (`attesa: false` for a dialog,
 * which has no place to draw one until it opens).
 */
export function aRichiesta(carica, { attesa = true } = {}) {
  return defineAsyncComponent({
    loader: carica,
    loadingComponent: attesa ? Attesa : undefined,
    delay: 200,
  })
}

/**
 * Whether a dialog drawn with `aRichiesta` is mounted: from the first time it
 * opens (`aperto`, a getter or a ref), and from then on, so that closing it
 * plays and what was written in it stays. Before, nothing of it is downloaded.
 */
export function apertoUnaVolta(aperto) {
  const montato = ref(false)
  watch(
    aperto,
    (adesso) => {
      if (adesso) montato.value = true
    },
    { immediate: true },
  )
  return montato
}
