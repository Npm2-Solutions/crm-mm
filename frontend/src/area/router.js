import { createRouter, createWebHistory } from 'vue-router'

const routes = [
  { path: '/', name: 'Home', component: () => import('./pages/Home.vue') },
  {
    path: '/appointments',
    name: 'Appointments',
    component: () => import('./pages/Appointments.vue'),
  },
  {
    path: '/plans',
    name: 'Plans',
    component: () => import('./pages/Plans.vue'),
  },
  {
    path: '/plans/:plan',
    name: 'Plan',
    component: () => import('./pages/Plan.vue'),
  },
  {
    path: '/documents',
    name: 'Documents',
    component: () => import('./pages/Documents.vue'),
  },
  {
    path: '/messages',
    name: 'Messages',
    component: () => import('./pages/Messages.vue'),
  },
  {
    path: '/invoices',
    name: 'Invoices',
    component: () => import('./pages/Invoices.vue'),
  },
  {
    path: '/login',
    name: 'Login',
    component: () => import('./pages/Login.vue'),
  },
  { path: '/:pathMatch(.*)*', redirect: '/' },
]

const router = createRouter({ history: createWebHistory('/area'), routes })

// who is not in goes to the door; who is in does not see the door again
router.beforeEach((to) => {
  const guest = !window.AREA?.user || window.AREA.user === 'Guest'
  if (guest && to.name !== 'Login') return { name: 'Login' }
  if (!guest && to.name === 'Login') return { name: 'Home' }
})

export default router
