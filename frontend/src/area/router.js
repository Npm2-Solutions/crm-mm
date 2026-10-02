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
    path: '/plans/:plan/shopping',
    name: 'PlanShopping',
    component: () => import('./pages/PlanShopping.vue'),
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
    path: '/chat',
    name: 'Chat',
    component: () => import('./pages/Chat.vue'),
  },
  // the invoices are with the documents, as on the brand's phone
  { path: '/invoices', redirect: '/documents' },
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
