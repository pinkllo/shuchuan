import { createRouter, createWebHistory } from "vue-router";
import { readSession } from "@/stores/session";

const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: "/login",
      name: "login",
      component: () => import("@/pages/LoginPage.vue"),
      meta: { shell: false, title: "进入平台" }
    },
    { path: "/", redirect: "/dashboard" },
    {
      path: "/dashboard",
      name: "dashboard",
      component: () => import("@/pages/DashboardPage.vue"),
      meta: {
        auth: true,
        title: "平台概览",
        summary: "从目录发布到指令生成，先把全链路的进度和风险看清楚。"
      }
    },
    {
      path: "/catalogs",
      name: "catalogs",
      component: () => import("@/pages/CatalogPage.vue"),
      meta: {
        auth: true,
        title: "数据目录",
        summary: "展示数据提供者已发布的数据目录、可申请范围和版本节奏。"
      }
    },
    {
      path: "/demands",
      name: "demands",
      component: () => import("@/pages/DemandPage.vue"),
      meta: {
        auth: true,
        title: "需求协同",
        summary: "围绕需求发起、审批、交付和反馈，把中间状态收拢到一个界面。"
      }
    },
    {
      path: "/processing",
      name: "processing",
      component: () => import("@/pages/ProcessingPage.vue"),
      meta: {
        auth: true,
        title: "数据处理",
        summary: "任务中心统一管理清洗、指令生成、拆书、病句修改等处理任务和能力接入。"
      }
    }
  ]
});

router.beforeEach((to) => {
  const session = readSession();
  if (to.meta.auth && !session.loggedIn) {
    return { name: "login" };
  }
  if (to.name === "login" && session.loggedIn) {
    return { name: "dashboard" };
  }
  return true;
});

export default router;
