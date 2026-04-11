import type { Component } from "vue";
import { markRaw } from "vue";
import {
  DataAnalysis,
  Files,
  Operation,
  SwitchButton
} from "@element-plus/icons-vue";

export interface NavItem {
  name: string;
  path: string;
  label: string;
  hint: string;
  icon: Component;
}

export const navItems: NavItem[] = [
  {
    name: "dashboard",
    path: "/dashboard",
    label: "平台概览",
    hint: "总览看板",
    icon: markRaw(DataAnalysis)
  },
  {
    name: "catalogs",
    path: "/catalogs",
    label: "数据目录",
    hint: "供给侧信息",
    icon: markRaw(Files)
  },
  {
    name: "demands",
    path: "/demands",
    label: "需求协同",
    hint: "审批与交付",
    icon: markRaw(SwitchButton)
  },
  {
    name: "processing",
    path: "/processing",
    label: "数据处理",
    hint: "任务与能力",
    icon: markRaw(Operation)
  }
];
