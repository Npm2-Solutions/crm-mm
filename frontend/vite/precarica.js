// Copyright (c) 2026, NPM2 Solutions Srl and contributors
/**
 * What a part of DottorCloud preloads when it opens another: only what is not
 * loaded yet.
 *
 * Vite gives every dynamic import the whole list of what it needs - Vue's
 * runtime, frappe-ui, the router - and its helper, for each one it has not seen,
 * goes through every <link> of the page (the iPhone's splash images, the
 * preloads before) to look for it, then adds a <link> of its own. On a slow
 * phone the start spent a quarter of a second in it, for files that were all
 * there already: whoever calls `import()` is running, so everything it imports,
 * all the way down, is loaded. The list keeps only the rest.
 */

/** The parts loaded once `host` runs: itself and what it imports, all the way down. */
export function caricati(grafo, host) {
  const visti = new Set()
  const visita = (file) => {
    if (visti.has(file)) return
    visti.add(file)
    const pezzo = grafo[file]
    if (pezzo && pezzo.type === 'chunk') pezzo.imports.forEach(visita)
  }
  visita(host)
  return visti
}

/**
 * Of what a dynamic import in `host` needs, what is not loaded already: not what
 * `host` imports, and not what the app's one entry imports - the browser fetches
 * and links all of that before any code of it runs, so before any `import()`.
 */
export function daPrecaricare(grafo, host, dipendenze) {
  if (!grafo || !grafo[host]) return dipendenze
  const gia = caricati(grafo, host)
  const ingressi = Object.keys(grafo).filter(
    (file) => grafo[file].type === 'chunk' && grafo[file].isEntry,
  )
  // with more entries (more pages), which one came first is not known
  if (ingressi.length === 1)
    for (const file of caricati(grafo, ingressi[0])) gia.add(file)
  return dipendenze.filter((file) => !gia.has(file))
}

/**
 * The plugin that sees the bundle's parts, and the `resolveDependencies` of
 * `build.modulePreload` that asks it. Without the bundle (another order of the
 * hooks), the list stays whole: it costs time, never a part that does not come.
 */
export default function precaricaSoloIlNuovo() {
  let grafo = null
  return {
    plugin: {
      name: 'dottorcloud-precarica-solo-il-nuovo',
      enforce: 'pre',
      generateBundle(_, bundle) {
        grafo = bundle
      },
    },
    resolveDependencies(file, dipendenze, { hostId, hostType }) {
      // the page's own list (the HTML's preloads) stays as it is
      if (hostType !== 'js') return dipendenze
      return daPrecaricare(grafo, hostId, dipendenze)
    },
  }
}
