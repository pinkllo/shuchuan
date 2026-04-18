import type { Component } from "vue";
import { markRaw } from "vue";
import {
  DocumentChecked,
  DataAnalysis,
  DocumentCopy,
  Files,
  Operation,
  SwitchButton,
  Tickets,
  User
} from "@element-plus/icons-vue";

import type { UserRole } from "@/types/auth";

export interface NavItem {
  name: string;
  path: string;
  label: string;
  hint: string;
  icon: Component;
  roles?: UserRole[];
}

export const navItems: NavItem[] = [
  {
    name: "dashboard",
    path: "/dashboard",
    label: "平台概览",
    hint: "总览看板",
    icon: markRaw(DataAnalysis),
    roles: ["admin", "provider", "consumer"]
  },
  {
    name: "workbench",
    path: "/workbench",
    label: "工作台",
    hint: "提交任务与下载结果",
    icon: markRaw(Operation),
    roles: ["aggregator"]
  },
  {
    name: "catalogs",
    path: "/catalogs",
    label: "数据目录",
    hint: "供给侧信息与浏览",
    icon: markRaw(Files),
    roles: ["provider", "aggregator"]
  },
  {
    name: "demands",
    path: "/demands",
    label: "需求协同",
    hint: "申请与审批",
    icon: markRaw(SwitchButton),
    roles: ["provider", "aggregator"]
  },
  {
    name: "deliveries",
    path: "/deliveries",
    label: "交付下载",
    hint: "下载结果",
    icon: markRaw(Tickets),
    roles: ["consumer"]
  },
  {
    name: "admin-approvals",
    path: "/admin/approvals",
    label: "注册审核",
    hint: "管理员审批申请",
    icon: markRaw(DocumentChecked),
    roles: ["admin"]
  },
  {
    name: "admin-users",
    path: "/admin/users",
    label: "用户管理",
    hint: "查看平台账号",
    icon: markRaw(User),
    roles: ["admin"]
  },
  {
    name: "admin-audit-logs",
    path: "/admin/logs",
    label: "审计日志",
    hint: "查看关键操作",
    icon: markRaw(DocumentCopy),
    roles: ["admin"]
  },
  {
    name: "admin-processors",
    path: "/admin/processors",
    label: "处理器管理",
    hint: "查看外部处理器",
    icon: markRaw(Operation),
    roles: ["admin"]
  }
];

export function filterNavItems(role: UserRole | null): NavItem[] {
  if (role === null) {
    return [];
  }

  return navItems.filter((item) => item.roles?.includes(role) ?? false);
}
