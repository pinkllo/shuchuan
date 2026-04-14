# Frontend Redesign Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Completely redesign the frontend with a Linear/Notion-inspired style, workflow-oriented dashboard, and master-detail layout for all business pages.

**Architecture:** Replace the current warm-toned single-column layout with a cold-gray design system, compact top nav, and a reusable MasterDetail dual-pane pattern. Dashboard becomes a role-based kanban board. All create/edit operations move from dialog modals to inline panels.

**Tech Stack:** Vue 3 + TypeScript + Vite + Element Plus (deep customization) + Inter font + Vanilla CSS variables

**Spec:** `docs/superpowers/specs/2026-04-14-frontend-redesign-design.md`

---

## File Structure

### New Files

| File | Responsibility |
|---|---|
| `apps/web/src/styles/design-tokens.css` | New design system variables |
| `apps/web/src/styles/element-overrides.css` | Element Plus deep customization |
| `apps/web/src/components/MasterDetail.vue` | Dual-pane list+detail container |
| `apps/web/src/components/ItemCard.vue` | Selectable list item card |
| `apps/web/src/components/DetailPanel.vue` | Right-side detail panel container |
| `apps/web/src/components/InlineForm.vue` | In-panel create/edit form wrapper |
| `apps/web/src/components/StatusBadge.vue` | Compact status badge |
| `apps/web/src/components/EmptyState.vue` | Empty state placeholder |
| `apps/web/src/components/AppTimeline.vue` | Vertical timeline component |
| `apps/web/src/components/ProgressBar.vue` | Custom progress bar |
| `apps/web/src/components/FileList.vue` | File list with preview/upload/delete |
| `apps/web/src/components/KanbanBoard.vue` | Kanban multi-column container |
| `apps/web/src/components/KanbanColumn.vue` | Single kanban column |
| `apps/web/src/components/KanbanCard.vue` | Kanban item card |

### Rewritten Files

| File | Change |
|---|---|
| `apps/web/src/styles/theme.css` | Replace with new design tokens |
| `apps/web/src/styles/base.css` | Rewrite with new design system |
| `apps/web/src/layout/AppShell.vue` | Compact 48px top nav |
| `apps/web/src/pages/DashboardPage.vue` | Kanban workflow board |
| `apps/web/src/pages/CatalogPage.vue` | MasterDetail layout |
| `apps/web/src/pages/DemandPage.vue` | MasterDetail layout |
| `apps/web/src/pages/ProcessingPage.vue` | MasterDetail layout |
| `apps/web/src/pages/DeliveryPage.vue` | Clean list view |
| `apps/web/src/pages/LoginPage.vue` | Visual upgrade |
| `apps/web/src/pages/RegisterPage.vue` | Visual upgrade |
| `apps/web/src/pages/AdminUserApprovalPage.vue` | MasterDetail layout |
| `apps/web/src/pages/AdminUserManagementPage.vue` | MasterDetail layout |
| `apps/web/src/pages/AdminAuditLogPage.vue` | Timeline view |
| `apps/web/src/pages/AdminProcessorPage.vue` | MasterDetail layout |

### Deleted Files

| File | Reason |
|---|---|
| `apps/web/src/components/OverviewMetric.vue` | Replaced by KanbanCard |
| `apps/web/src/components/StatusPill.vue` | Replaced by StatusBadge |

### Preserved Files (no changes)

- All stores (`catalogStore.ts`, `demandStore.ts`, `taskStore.ts`, `session.ts`, `capabilityStore.ts`)
- All API clients (`api/*.ts`)
- All types (`types/*.ts`)
- Router config (`router/index.ts`) — only add processor route
- Navigation config (`config/navigation.ts`) — only add processor nav item

---

### Task 1: Design System Foundation

**Files:**
- Create: `apps/web/src/styles/design-tokens.css`
- Create: `apps/web/src/styles/element-overrides.css`
- Rewrite: `apps/web/src/styles/theme.css`
- Rewrite: `apps/web/src/styles/base.css`
- Modify: `apps/web/src/main.ts`

- [ ] **Step 1: Create design-tokens.css**

Create `apps/web/src/styles/design-tokens.css` with all CSS custom properties from the spec: page/surface backgrounds, border colors, text colors, accent/semantic colors, font families, border radii, shadows, and spacing scale.

- [ ] **Step 2: Create element-overrides.css**

Create `apps/web/src/styles/element-overrides.css` with deep customization for Element Plus: button primary color using `--accent`, table header/hover using design tokens, dialog/drawer border radius, form item spacing, input/select border radius.

- [ ] **Step 3: Rewrite theme.css**

Replace the entire content of `apps/web/src/styles/theme.css` to import the Inter font from Google Fonts via `@import` and set `--font-sans` with Inter as primary.

- [ ] **Step 4: Rewrite base.css**

Replace `apps/web/src/styles/base.css` with new global styles: body uses `--bg-page` and `--font-sans`, surface-card uses `--bg-surface` and `--radius-lg`, page-grid gap reduced to 16px, fade-rise animation retained, responsive breakpoints updated. Remove all old warm-toned styles, flow-card, quick-btn, quick-actions classes.

- [ ] **Step 5: Update main.ts imports**

Ensure `apps/web/src/main.ts` imports the new CSS files in correct order: `design-tokens.css` → `theme.css` → `base.css` → `element-overrides.css`.

- [ ] **Step 6: Verify app still loads**

Run: `cd apps/web && npm run dev`
Open browser, confirm the app loads without CSS errors.

- [ ] **Step 7: Commit**

```
git commit -m "feat(web): implement new design system foundation"
```

---

### Task 2: Core Layout Components

**Files:**
- Create: `apps/web/src/components/StatusBadge.vue`
- Create: `apps/web/src/components/EmptyState.vue`
- Create: `apps/web/src/components/MasterDetail.vue`
- Create: `apps/web/src/components/ItemCard.vue`
- Create: `apps/web/src/components/DetailPanel.vue`
- Create: `apps/web/src/components/InlineForm.vue`

- [ ] **Step 1: Create StatusBadge component**

Compact inline badge with colored dot + text. Props: `label: string`, `tone: 'success' | 'warning' | 'danger' | 'info' | 'muted'`. Renders as `<span class="status-badge">` with a small colored circle and text. Uses design tokens for colors.

- [ ] **Step 2: Create EmptyState component**

Centered placeholder for empty panels. Props: `icon?: string`, `title: string`, `description?: string`. Renders centered vertically with muted styling.

- [ ] **Step 3: Create MasterDetail component**

Dual-pane container. Slots: `list` (left 40%), `detail` (right 60%). Props: `hasSelection: boolean`. When no selection, detail slot shows EmptyState. CSS: flex layout, 1px vertical border separator, each pane independently scrollable with `overflow-y: auto` and `height: calc(100vh - 120px)`. Responsive: collapses to single column below 768px.

- [ ] **Step 4: Create ItemCard component**

Selectable list item. Props: `selected: boolean`. Emits: `click`. Renders as a hoverable card with `--bg-hover` on hover, `--bg-active` + left blue border when selected. Default slot for content.

- [ ] **Step 5: Create DetailPanel component**

Right-side panel container. Slots: `header`, `default` (content), `actions`. Renders with proper padding, header area with border-bottom separator, scrollable content area.

- [ ] **Step 6: Create InlineForm component**

Form wrapper for create/edit mode in DetailPanel. Props: `title: string`, `loading: boolean`. Emits: `submit`, `cancel`. Renders title, default slot for form fields, footer with cancel and submit buttons.

- [ ] **Step 7: Write component tests**

Test `MasterDetail` renders both panes, `ItemCard` emits click and shows selected state, `StatusBadge` renders correct tone color.

- [ ] **Step 8: Commit**

```
git commit -m "feat(web): add core layout components (MasterDetail, ItemCard, DetailPanel, etc.)"
```

---

### Task 3: Kanban & Utility Components

**Files:**
- Create: `apps/web/src/components/KanbanBoard.vue`
- Create: `apps/web/src/components/KanbanColumn.vue`
- Create: `apps/web/src/components/KanbanCard.vue`
- Create: `apps/web/src/components/AppTimeline.vue`
- Create: `apps/web/src/components/ProgressBar.vue`
- Create: `apps/web/src/components/FileList.vue`

- [ ] **Step 1: Create KanbanBoard**

Container for kanban columns. Renders as a flex row with equal-width columns and 16px gap. Default slot for KanbanColumn children. Responsive: stacks vertically below 768px.

- [ ] **Step 2: Create KanbanColumn**

Single column with header. Props: `title: string`, `count: number`. Renders title with count badge, then a scrollable card list area. Default slot for KanbanCard children.

- [ ] **Step 3: Create KanbanCard**

Clickable summary card. Props: `icon?: string`. Emits: `click`. Default slot for content. Hover effect with subtle shadow lift.

- [ ] **Step 4: Create AppTimeline**

Vertical timeline. Props: `items: Array<{ time: string, content: string, type?: string }>`. Renders vertical line with dots and content blocks. Uses muted colors from design tokens.

- [ ] **Step 5: Create ProgressBar**

Custom styled progress bar. Props: `value: number` (0-100), `label?: string`, `color?: string`. Renders a thin bar with percentage fill and optional label text.

- [ ] **Step 6: Create FileList**

File list component. Props: `files: Array<CatalogAsset>`, `editable: boolean`, `loading: boolean`. Emits: `preview(file)`, `delete(file)`, `upload(files)`. Renders file rows with name, size, type, and action buttons. Includes a file upload trigger when editable.

- [ ] **Step 7: Commit**

```
git commit -m "feat(web): add kanban, timeline, progress bar, and file list components"
```

---

### Task 4: AppShell Rewrite

**Files:**
- Rewrite: `apps/web/src/layout/AppShell.vue`
- Modify: `apps/web/src/config/navigation.ts`

- [ ] **Step 1: Add processor nav item to navigation.ts**

Add the admin processor page entry to `navItems` array with path `/admin/processors`, label `处理器管理`, and admin-only role.

- [ ] **Step 2: Rewrite AppShell.vue**

Complete rewrite with:
- 48px height top bar, white background, 1px bottom border
- Left: text logo "数传协同平台" (no subtitle)
- Center: nav links as compact tabs with 2px blue bottom indicator on active
- Right: role badge (small, rounded) + display name + logout button
- Content area: full width, `max-width: 1400px`, centered
- Remove page-header section (pages manage their own titles)

- [ ] **Step 3: Verify navigation works**

Run dev server, confirm all nav items render and route correctly.

- [ ] **Step 4: Commit**

```
git commit -m "feat(web): rewrite AppShell with compact top nav"
```

---

### Task 5: Dashboard Kanban Page

**Files:**
- Rewrite: `apps/web/src/pages/DashboardPage.vue`
- Delete: `apps/web/src/components/OverviewMetric.vue`

- [ ] **Step 1: Rewrite DashboardPage.vue**

Complete rewrite with role-based kanban boards:

**Provider view**: 3-column kanban (待处理: pending demands / 进行中: draft catalogs / 近期完成: recent approvals/publishes) + AppTimeline activity feed.

**Aggregator view**: 3-column kanban (待处理: pending demands + actionable approved demands / 处理中: running tasks with progress / 近期完成: completed tasks).

**Admin view**: 3-column kanban (待处理: pending registrations / 系统状态: summary stats / 近期活动: recent audit logs).

**Consumer view**: Simple delivery list with download buttons.

Use `KanbanBoard`, `KanbanColumn`, `KanbanCard`, `AppTimeline` components. Reuse existing stores for data fetching.

- [ ] **Step 2: Delete OverviewMetric.vue**

Remove `apps/web/src/components/OverviewMetric.vue`.

- [ ] **Step 3: Verify dashboard renders for all roles**

Run dev server, login as different roles, confirm kanban boards render correctly.

- [ ] **Step 4: Commit**

```
git commit -m "feat(web): rewrite dashboard as workflow kanban board"
```

---

### Task 6: Catalog Page (MasterDetail)

**Files:**
- Rewrite: `apps/web/src/pages/CatalogPage.vue`
- Delete: `apps/web/src/components/CatalogAssetPreviewPanel.vue`

- [ ] **Step 1: Rewrite CatalogPage.vue**

Complete rewrite using MasterDetail layout:

**List pane**: Search input + status filter dropdown + "+ 新建" button. ItemCard list showing: catalog name, version, StatusBadge (draft/published/archived), file count. Provider sees own catalogs, Aggregator sees published.

**Detail pane (viewing)**: Header with name + version + StatusBadge + action buttons (publish/archive). Info sections: data type, granularity, sensitivity, scale, fields description, upload method. FileList component for catalog assets. Associated demands list with quick approve action (for Provider).

**Detail pane (creating)**: InlineForm with all catalog metadata fields + inline file upload area (multi-file). Submit creates catalog, refreshes list, selects new item.

Use existing `catalogStore` for data. Remove dialog-based creation entirely.

- [ ] **Step 2: Delete CatalogAssetPreviewPanel.vue**

Remove `apps/web/src/components/CatalogAssetPreviewPanel.vue` (merged into FileList).

- [ ] **Step 3: Verify catalog page functions**

Test: list loads, selection works, detail panel shows data, file list displays, create form submits.

- [ ] **Step 4: Commit**

```
git commit -m "feat(web): rewrite catalog page with master-detail layout"
```

---

### Task 7: Demand Page (MasterDetail)

**Files:**
- Rewrite: `apps/web/src/pages/DemandPage.vue`

- [ ] **Step 1: Rewrite DemandPage.vue**

Complete rewrite using MasterDetail layout:

**List pane**: Group demands by status with section headers (待审批 / 已获批 / 处理中 / 已交付 / 已驳回), each with count. ItemCard showing: demand title, catalog name, StatusBadge.

**Detail pane (viewing)**: Header with title + StatusBadge. Info: purpose, delivery plan, catalog summary (name, version, data type, file count). Status flow timeline (applied → approved → data_uploaded → processing → delivered). Actions: Provider sees approve/reject buttons with note input. Aggregator sees "创建任务" that inline-expands a task creation form (select files from catalog, choose task type, config fields).

**Detail pane (creating demand)**: InlineForm with catalog selector, title, purpose, delivery plan fields.

- [ ] **Step 2: Verify demand page functions**

Test: grouped list, detail panel, approve/reject actions, inline task creation.

- [ ] **Step 3: Commit**

```
git commit -m "feat(web): rewrite demand page with master-detail layout"
```

---

### Task 8: Processing Page (MasterDetail)

**Files:**
- Rewrite: `apps/web/src/pages/ProcessingPage.vue`
- Delete: `apps/web/src/components/StatusPill.vue`

- [ ] **Step 1: Rewrite ProcessingPage.vue**

Complete rewrite using MasterDetail layout:

**List pane**: Search + status filter. ItemCard showing: task type, StatusBadge, ProgressBar (for running tasks), processor name or "手动".

**Detail pane (viewing)**: Header with task ID + type + StatusBadge. Config info (model, template, batch size). Input files list (read-only FileList). Progress section: ProgressBar + latest processor message. Artifacts section (after completion): list generated files with download links. Manual mode actions: start/complete/fail buttons + artifact registration form.

**Detail pane (creating)**: InlineForm with demand selector, file multi-select from catalog, task type dropdown (showing online processors with "auto" label + custom option), config fields.

- [ ] **Step 2: Delete StatusPill.vue**

Remove `apps/web/src/components/StatusPill.vue` (replaced by StatusBadge).

- [ ] **Step 3: Update all StatusPill imports**

Search and replace any remaining StatusPill imports in other files with StatusBadge.

- [ ] **Step 4: Verify processing page functions**

Test: task list, progress display, manual mode, inline creation.

- [ ] **Step 5: Commit**

```
git commit -m "feat(web): rewrite processing page with master-detail layout"
```

---

### Task 9: Delivery, Auth & Admin Pages

**Files:**
- Rewrite: `apps/web/src/pages/DeliveryPage.vue`
- Rewrite: `apps/web/src/pages/LoginPage.vue`
- Rewrite: `apps/web/src/pages/RegisterPage.vue`
- Rewrite: `apps/web/src/pages/AdminUserApprovalPage.vue`
- Rewrite: `apps/web/src/pages/AdminUserManagementPage.vue`
- Rewrite: `apps/web/src/pages/AdminAuditLogPage.vue`
- Create: `apps/web/src/pages/AdminProcessorPage.vue`
- Modify: `apps/web/src/router/index.ts`

- [ ] **Step 1: Rewrite DeliveryPage.vue**

Full-width list (no MasterDetail needed). Search + time range filter. Clean table/list with: demand title, file name, sample count, delivery time, download button. Use design tokens for styling.

- [ ] **Step 2: Rewrite LoginPage.vue**

Keep centered card layout. Update: `--bg-page` background, 16px border radius card, subtle shadow, Inter font. Left area with brand tagline, right area with form. Remove warm-toned gradients.

- [ ] **Step 3: Rewrite RegisterPage.vue**

Match LoginPage visual style. Same card layout with registration form.

- [ ] **Step 4: Rewrite AdminUserApprovalPage.vue**

MasterDetail layout. List grouped by status (pending / approved / rejected). Detail panel with application info, role assignment dropdown, approve/reject buttons.

- [ ] **Step 5: Rewrite AdminUserManagementPage.vue**

MasterDetail layout. User list with search. Detail panel with user info and enable/disable toggle.

- [ ] **Step 6: Rewrite AdminAuditLogPage.vue**

Full-width AppTimeline view. Filter bar: operation type dropdown + time range picker. Logs grouped by date. Each log entry shows: time, action, actor, target, detail.

- [ ] **Step 7: Create AdminProcessorPage.vue**

MasterDetail layout. Processor list with status indicator (green/gray dot). Detail panel: processor name, task type, description, endpoint URL, status, last heartbeat time, registered time.

- [ ] **Step 8: Update router with processor page route**

Add `/admin/processors` route to `apps/web/src/router/index.ts`.

- [ ] **Step 9: Commit**

```
git commit -m "feat(web): rewrite delivery, auth, and admin pages"
```

---

### Task 10: Cleanup & Responsive Polish

**Files:**
- Remove: `apps/web/src/components/SharedFilePreviewPanel.vue` (if fully replaced by FileList)
- Modify: various files for responsive fixes

- [ ] **Step 1: Remove unused components**

Delete any components no longer imported by any page: `OverviewMetric.vue`, `StatusPill.vue`, `CatalogAssetPreviewPanel.vue`, `SharedFilePreviewPanel.vue` (if fully merged).

- [ ] **Step 2: Responsive testing**

Verify all pages at 3 breakpoints: >1200px (full dual-pane), 768-1200px (narrow dual-pane), <768px (single column with back navigation).

- [ ] **Step 3: Fix any responsive issues**

Adjust MasterDetail collapse behavior, kanban stacking, form layouts on narrow screens.

- [ ] **Step 4: Run all frontend tests**

Run: `cd apps/web && npx vitest run`
Fix any broken tests due to removed components or changed structure.

- [ ] **Step 5: Final commit**

```
git commit -m "chore(web): cleanup unused components and responsive polish"
```
