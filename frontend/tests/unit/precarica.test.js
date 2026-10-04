// Copyright (c) 2026, NPM2 Solutions Srl and contributors
// What a dynamic import preloads: only what its caller has not loaded already
// (frontend/vite/precarica.js)
import precaricaSoloIlNuovo, {
  caricati,
  daPrecaricare,
} from '../../vite/precarica.js'

const pezzo = (imports, isEntry = false) => ({
  type: 'chunk',
  imports,
  isEntry,
})

// the entry imports the router, Vue's runtime and a tooltip; the router opens a
// page that needs the runtime, the tooltip and its own tile
const GRAFO = {
  'assets/index.js': pezzo(
    ['assets/router.js', 'assets/runtime-core.js', 'assets/Tooltip.js'],
    true,
  ),
  'assets/Tooltip.js': pezzo([]),
  'assets/router.js': pezzo(['assets/runtime-core.js', 'assets/resources.js']),
  'assets/runtime-core.js': pezzo([]),
  'assets/resources.js': pezzo(['assets/runtime-core.js']),
  'assets/Today.js': pezzo(['assets/runtime-core.js', 'assets/StatTile.js']),
  'assets/StatTile.js': pezzo([]),
  'assets/index.css': { type: 'asset' },
}

describe('what a dynamic import preloads', () => {
  it('knows what is loaded once a part runs, all the way down', () => {
    expect([...caricati(GRAFO, 'assets/index.js')].sort()).toEqual([
      'assets/Tooltip.js',
      'assets/index.js',
      'assets/resources.js',
      'assets/router.js',
      'assets/runtime-core.js',
    ])
  })

  it('keeps only what the caller and the entry have not loaded', () => {
    expect(
      daPrecaricare(GRAFO, 'assets/router.js', [
        'assets/Today.js',
        'assets/runtime-core.js',
        'assets/Tooltip.js',
        'assets/StatTile.js',
      ]),
    ).toEqual(['assets/Today.js', 'assets/StatTile.js'])
  })

  it('with two entries, counts only on what the caller imports', () => {
    const dueIngressi = {
      ...GRAFO,
      'assets/area.js': pezzo(['assets/runtime-core.js'], true),
    }
    expect(
      daPrecaricare(dueIngressi, 'assets/router.js', [
        'assets/Today.js',
        'assets/Tooltip.js',
      ]),
    ).toEqual(['assets/Today.js', 'assets/Tooltip.js'])
  })

  it('leaves the list whole for a caller it does not know', () => {
    const tutte = ['assets/Today.js', 'assets/runtime-core.js']
    expect(daPrecaricare(GRAFO, 'assets/altro.js', tutte)).toBe(tutte)
    expect(daPrecaricare(null, 'assets/router.js', tutte)).toBe(tutte)
  })

  it('asks the bundle the plugin saw, and leaves the page’s own list alone', () => {
    const { plugin, resolveDependencies } = precaricaSoloIlNuovo()
    const deps = ['assets/Today.js', 'assets/runtime-core.js']
    // before the bundle is seen: whole
    expect(
      resolveDependencies('assets/Today.js', deps, {
        hostId: 'assets/router.js',
        hostType: 'js',
      }),
    ).toBe(deps)
    plugin.generateBundle({}, GRAFO)
    expect(
      resolveDependencies('assets/Today.js', deps, {
        hostId: 'assets/router.js',
        hostType: 'js',
      }),
    ).toEqual(['assets/Today.js'])
    expect(
      resolveDependencies('assets/Today.js', deps, {
        hostId: 'index.html',
        hostType: 'html',
      }),
    ).toBe(deps)
  })
})
