import { createRouter, createWebHistory } from 'vue-router'

const routes = [
  {
    path: '/',
    redirect: '/chat'
  },
  {
    path: '/chat',
    name: 'Chat',
    component: () => import('@/views/ChatView.vue'),
    meta: { title: '聊天' }
  },
  {
    path: '/image-gen',
    name: 'ImageGen',
    component: () => import('@/views/ImageGenView.vue'),
    meta: { title: '文生图' }
  },
  {
    path: '/image-edit',
    name: 'ImageEdit',
    component: () => import('@/views/ImageEditView.vue'),
    meta: { title: '图生图' }
  },
  {
    path: '/fuse',
    name: 'Fuse',
    component: () => import('@/views/FuseView.vue'),
    meta: { title: '多图融合' }
  },
  {
    path: '/settings',
    name: 'Settings',
    component: () => import('@/views/SettingsView.vue'),
    meta: { title: '设置' }
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

// 路由标题
router.beforeEach((to, from, next) => {
  document.title = to.meta.title ? `${to.meta.title} · AI Generation Studio` : 'AI Generation Studio'
  next()
})

export default router