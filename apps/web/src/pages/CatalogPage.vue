<script setup lang="ts">
import { ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import StatusPill from '@/components/StatusPill.vue'
import CatalogFormDialog from '@/components/CatalogFormDialog.vue'
import { useCatalogStore, catalogStatusLabels, catalogStatusTones, sensitivityLabels, type CatalogItem } from '@/stores/catalogStore'
import { usePermission } from '@/composables/usePermission'

const catalogStore = useCatalogStore()
const { can } = usePermission()

const showForm = ref(false)
const editItem = ref<CatalogItem | null>(null)
const searchQuery = ref('')
const detailItem = ref<CatalogItem | null>(null)
const showDetail = ref(false)

const filteredItems = ref(catalogStore.items)

function doSearch() {
  const q = searchQuery.value.trim().toLowerCase()
  if (!q) {
    filteredItems.value = catalogStore.items
    return
  }
  filteredItems.value = catalogStore.items.filter(
    i => i.name.toLowerCase().includes(q) || i.provider.toLowerCase().includes(q) || i.type.toLowerCase().includes(q)
  )
}

function handleCreate() {
  editItem.value = null
  showForm.value = true
}

function handleEdit(item: CatalogItem) {
  editItem.value = item
  showForm.value = true
}

function handleDetail(item: CatalogItem) {
  detailItem.value = item
  showDetail.value = true
}

async function handleDelete(item: CatalogItem) {
  try {
    await ElMessageBox.confirm(`确定删除数据「${item.name}」？此操作不可恢复。`, '确认删除', { type: 'warning' })
    catalogStore.removeCatalog(item.id)
    ElMessage.success('数据已删除')
  } catch { /* cancelled */ }
}
</script>

<template>
  <div class="page-grid">
    <section class="surface-card">
      <div class="card-head">
        <div>
          <h3>数据目录</h3>
          <p>数据提供者发布数据集，汇聚者根据数据集发起需求。</p>
        </div>
        <div class="head-actions">
          <el-input v-model="searchQuery" placeholder="搜索目录..." clearable style="width:220px" @input="doSearch" />
          <el-button v-if="can('catalog.create')" type="primary" @click="handleCreate">发布数据</el-button>
        </div>
      </div>

      <el-table :data="filteredItems" stripe>
        <el-table-column prop="id" label="编号" width="100" />
        <el-table-column prop="name" label="目录名称" min-width="180">
          <template #default="{ row }">
            <el-button type="primary" link @click="handleDetail(row)">{{ row.name }}</el-button>
          </template>
        </el-table-column>
        <el-table-column prop="provider" label="提供者" width="130" />
        <el-table-column prop="type" label="类型" width="110" />
        <el-table-column prop="scale" label="规模" min-width="150" />
        <el-table-column prop="version" label="版本" width="100" />
        <el-table-column label="敏感级别" width="100">
          <template #default="{ row }">
            <el-tag :type="row.sensitivity === 'sensitive' ? 'danger' : row.sensitivity === 'internal' ? 'warning' : 'success'" size="small">
              {{ sensitivityLabels[row.sensitivity as keyof typeof sensitivityLabels] }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="状态" width="100">
          <template #default="{ row }">
            <StatusPill
              :label="catalogStatusLabels[row.status as keyof typeof catalogStatusLabels]"
              :tone="catalogStatusTones[row.status as keyof typeof catalogStatusTones] as any"
            />
          </template>
        </el-table-column>
        <el-table-column label="操作" width="150" fixed="right">
          <template #default="{ row }">
            <el-button v-if="can('catalog.edit')" type="primary" link size="small" @click="handleEdit(row)">编辑</el-button>
            <el-button v-if="can('catalog.delete')" type="danger" link size="small" @click="handleDelete(row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
    </section>

    <!-- 目录详情抽屉 -->
    <el-drawer v-model="showDetail" :title="`目录详情 — ${detailItem?.id ?? ''}`" size="480px" direction="rtl">
      <template v-if="detailItem">
        <el-descriptions :column="1" border size="small">
          <el-descriptions-item label="目录名称">{{ detailItem.name }}</el-descriptions-item>
          <el-descriptions-item label="提供者">{{ detailItem.provider }}</el-descriptions-item>
          <el-descriptions-item label="数据类型">{{ detailItem.type }}</el-descriptions-item>
          <el-descriptions-item label="粒度说明">{{ detailItem.granularity }}</el-descriptions-item>
          <el-descriptions-item label="版本">{{ detailItem.version }}</el-descriptions-item>
          <el-descriptions-item label="字段范围">{{ detailItem.fields }}</el-descriptions-item>
          <el-descriptions-item label="数据规模">{{ detailItem.scale }}</el-descriptions-item>
          <el-descriptions-item label="敏感级别">
            <el-tag size="small">{{ sensitivityLabels[detailItem.sensitivity] }}</el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="状态">
            <StatusPill :label="catalogStatusLabels[detailItem.status]" :tone="catalogStatusTones[detailItem.status] as any" />
          </el-descriptions-item>
          <el-descriptions-item label="创建时间">{{ detailItem.createdAt }}</el-descriptions-item>
        </el-descriptions>
        <div v-if="detailItem.description" style="margin-top:20px">
          <h4 style="margin:0 0 8px">描述说明</h4>
          <p style="margin:0;line-height:1.8;color:var(--text-soft)">{{ detailItem.description }}</p>
        </div>
      </template>
    </el-drawer>

    <CatalogFormDialog v-model:visible="showForm" :edit-item="editItem" />
  </div>
</template>

<style scoped>
.head-actions {
  display: flex;
  gap: 10px;
  align-items: center;
}
</style>
