import { createApp } from 'vue'
import { createPinia } from 'pinia'
import ElementPlus from 'element-plus'
import zhCn from 'element-plus/es/locale/lang/zh-cn'
import 'element-plus/dist/index.css'
import App from './App.vue'
import router from './router'
import './styles/design-tokens.css'
import './styles/theme.css'
import './styles/base.css'
import './styles/element-overrides.css'

const TOP_NAV_HEIGHT = 48
const MESSAGE_SAFE_MARGIN = 16
const MESSAGE_OFFSET = TOP_NAV_HEIGHT + MESSAGE_SAFE_MARGIN

const app = createApp(App)

app.use(createPinia())
app.use(router)
app.use(ElementPlus, {
  locale: zhCn,
  message: {
    offset: MESSAGE_OFFSET
  }
})
app.mount('#app')
