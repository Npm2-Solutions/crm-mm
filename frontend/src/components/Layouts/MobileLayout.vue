<!--
  Modifications copyright (c) 2026, NPM2 Solutions Srl
-->
<template>
  <!-- `h-app` rather than `h-screen`: 100vh on a phone is measured with the
       address bar already hidden, so the shell used to hang the height of that
       bar below the fold. `w-full` rather than `w-screen`, which counts the
       scrollbar gutter and hands the page a horizontal scroll it never wanted. -->
  <!-- data-cornice-telefono: while somebody writes, the frame is as tall as
       what the keyboard leaves (utils/tastieraAperta.js, telefono.css) -->
  <div class="flex h-app w-full" data-cornice-telefono>
    <div class="flex h-full min-w-0 flex-1 flex-col px-safe">
      <MobileAppHeader />
      <SenzaRete />
      <!-- The scroll box is this wrapper, not the whole column, so the header
           stays put and the tab bar is never scrolled off the bottom. -->
      <!-- `main`: where a screen reader jumps to the page -->
      <main
        ref="scroll"
        class="flex min-h-0 flex-1 flex-col overflow-auto bg-surface-base"
      >
        <slot />
      </main>
      <MobileBottomNav />
    </div>
    <GlobalModals />
  </div>
</template>
<script setup>
import MobileAppHeader from '@/components/Mobile/MobileAppHeader.vue'
import MobileBottomNav from '@/components/Mobile/MobileBottomNav.vue'
import SenzaRete from '@/components/SenzaRete.vue'
import GlobalModals from '@/components/Modals/GlobalModals.vue'
import { chiudiPrimaDiTornare, tornaConLeBriciole } from '@/utils/indietro'
import { allaCimaConLaScheda } from '@/utils/schedaAttiva'
import { seguiLaTastiera } from '@/utils/tastieraAperta'
import { trascinaIFogli } from '@/utils/trascinaFoglio'
import { registerScrollContainer, unregisterScrollContainer } from 'frappe-ui'
import { onBeforeUnmount, onMounted, useTemplateRef } from 'vue'
import { useRouter } from 'vue-router'

// frappe-ui's shells publish their scroll element to a shared registry; this
// layout is not one of them, so it registers its own. Without it `MobileNavItem`
// has nothing to scroll and tapping the tab you are already on does nothing.
const scroll = useTemplateRef('scroll')

onMounted(() => scroll.value && registerScrollContainer(scroll.value))
onBeforeUnmount(() => scroll.value && unregisterScrollContainer(scroll.value))

// the keyboard covers the bottom of the screen without making the page any
// shorter: while somebody writes, the frame follows what one sees
let smettiDiSeguire = () => {}
onMounted(() => (smettiDiSeguire = seguiLaTastiera()))
onBeforeUnmount(() => smettiDiSeguire())

// the phone's status bar and the browser's own bar wear the app's colour,
// light or dark, and change with it (Android; an iPhone's installed app
// keeps its own)
function coloreDellaBarra() {
  let meta = document.querySelector('meta[name="theme-color"]')
  if (!meta) {
    meta = document.createElement('meta')
    meta.name = 'theme-color'
    document.head.append(meta)
  }
  meta.content = inRgb(
    getComputedStyle(document.documentElement).backgroundColor,
  )
}

// the tokens are written in oklch(), which an older phone's browser does not
// read in a meta: a pixel painted with the colour gives it back in rgb
function inRgb(colore) {
  const tela = document.createElement('canvas').getContext('2d')
  if (!tela) return colore
  tela.fillStyle = colore
  tela.fillRect(0, 0, 1, 1)
  const [r, g, b] = tela.getImageData(0, 0, 1, 1).data
  return `rgb(${r}, ${g}, ${b})`
}
const cambioDiTema = new MutationObserver(coloreDellaBarra)
onMounted(() => {
  coloreDellaBarra()
  cambioDiTema.observe(document.documentElement, {
    attributes: true,
    attributeFilter: ['data-theme', 'data-marchio'],
  })
})
onBeforeUnmount(() => cambioDiTema.disconnect())

// Android's back, and the browser's, closes a sheet, a menu or the agenda's
// panel before it leaves the page (utils/indietro.js)
const router = useRouter()
let smettiIndietro = () => {}
onMounted(() => (smettiIndietro = chiudiPrimaDiTornare(router)))
onBeforeUnmount(() => smettiIndietro())

// the tab one is on, tapped again, takes its page back to the top
let smettiCima = () => {}
onMounted(() => (smettiCima = allaCimaConLaScheda()))
onBeforeUnmount(() => smettiCima())

// the crumb a page came from goes back to it, the list as it was left
let smettiBriciole = () => {}
onMounted(() => (smettiBriciole = tornaConLeBriciole(router)))
onBeforeUnmount(() => smettiBriciole())

// a sheet taken by its grabber follows the finger down and, far enough, closes
// (utils/trascinaFoglio.js)
let smettiDiTrascinare = () => {}
onMounted(() => (smettiDiTrascinare = trascinaIFogli()))
onBeforeUnmount(() => smettiDiTrascinare())

// what one taps shows it is pressed (`active:`) in place of the browser's grey
// flash (telefono.css); iPhone shows it only where a touch is listened to
function alTocco() {}
onMounted(() =>
  document.addEventListener('touchstart', alTocco, { passive: true }),
)
onBeforeUnmount(() => document.removeEventListener('touchstart', alTocco))
</script>
