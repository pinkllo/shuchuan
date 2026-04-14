import { createRouter, createWebHistory } from "vue-router";

import { useSessionStore } from "@/stores/session";
import type { UserRole } from "@/types/auth";

const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: "/login",
      name: "login",
      component: () => import("@/pages/LoginPage.vue"),
      meta: { shell: false, title: "登录系统" }
    },
    {
      path: "/register",
      name: "register",
      component: () => import("@/pages/RegisterPage.vue"),
      meta: { shell: false, title: "提交注册申请" }
    },
    { path: "/", redirect: "/dashboard" },
    {
      path: "/dashboard",
      name: "dashboard",
      component: () => import("@/pages/DashboardPage.vue"),
      meta: {
        auth: true,
        roles: ["admin", "provider", "aggregator", "consumer"],
        title: "平台概览",
        summary: "按角色查看当前链路状态、审核压力和交付结果。"
      }
    },
    {
      path: "/catalogs",
      name: "catalogs",
      component: () => import("@/pages/CatalogPage.vue"),
      meta: {
        auth: true,
        roles: ["provider", "aggregator"],
        title: "数据目录",
        summary: "提供者管理目录，汇聚者浏览可申请的数据供给。"
      }
    },
    {
      path: "/demands",
      name: "demands",
      component: () => import("@/pages/DemandPage.vue"),
      meta: {
        auth: true,
        roles: ["provider", "aggregator"],
        title: "需求协同",
        summary: "围绕真实需求状态、审批和原始文件上传推进链路。"
      }
    },
    {
      path: "/processing",
      name: "processing",
      component: () => import("@/pages/ProcessingPage.vue"),
      meta: {
        auth: true,
        roles: ["aggregator"],
        title: "数据处理",
        summary: "任务中心登记处理任务、推进状态，并记录半接入指令生成产物。"
      }
    },
    {
      path: "/deliveries",
      name: "deliveries",
      component: () => import("@/pages/DeliveryPage.vue"),
      meta: {
        auth: true,
        roles: ["consumer"],
        title: "交付下载",
        summary: "仅数据使用者可查看和下载最终交付结果。"
      }
    },
    {
      path: "/admin/approvals",
      name: "admin-approvals",
      component: () => import("@/pages/AdminUserApprovalPage.vue"),
      meta: {
        auth: true,
        roles: ["admin"],
        title: "注册审核",
        summary: "管理员审批注册申请并分配角色。"
      }
    },
    {
      path: "/admin/users",
      name: "admin-users",
      component: () => import("@/pages/AdminUserManagementPage.vue"),
      meta: {
        auth: true,
        roles: ["admin"],
        title: "用户管理",
        summary: "管理员查看平台账号与状态。"
      }
    },
    {
      path: "/admin/logs",
      name: "admin-audit-logs",
      component: () => import("@/pages/AdminAuditLogPage.vue"),
      meta: {
        auth: true,
        roles: ["admin"],
        title: "审计日志",
        summary: "管理员查看关键写操作与交付下载记录。"
      }
    },
    {
      path: "/admin/processors",
      name: "admin-processors",
      component: () => import("@/pages/AdminProcessorPage.vue"),
      meta: {
        auth: true,
        roles: ["admin"],
        title: "处理器管理",
        summary: "管理员查看已注册外部处理服务与在线状态。"
      }
    },
    {
      path: "/:pathMatch(.*)*",
      redirect: "/dashboard"
    }
  ]
});

router.beforeEach(async (to) => {
  const sessionStore = useSessionStore();

  if (!sessionStore.restored) {
    try {
      await sessionStore.restoreSession();
    } catch {
      if (to.meta.auth) {
        return {
          name: "login",
          query: { redirect: to.fullPath, reason: "session-expired" }
        };
      }
    }
  }

  if (to.meta.auth && !sessionStore.isAuthenticated) {
    return {
      name: "login",
      query: { redirect: to.fullPath }
    };
  }

  if ((to.name === "login" || to.name === "register") && sessionStore.isAuthenticated) {
    return { name: "dashboard" };
  }

  const roles = to.meta.roles as UserRole[] | undefined;
  if (roles && (!sessionStore.role || !roles.includes(sessionStore.role))) {
    return { name: "dashboard" };
  }

  return true;
});

export default router;
