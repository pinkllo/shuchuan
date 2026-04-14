<script setup lang="ts">
import type { FileItem } from "@/types/file";

defineProps<{
  files: FileItem[];
  editable?: boolean;
  loading?: boolean;
}>();

defineEmits<{
  preview: [file: FileItem];
  delete: [file: FileItem];
  upload: [files: FileList];
}>();

function formatSize(bytes?: number): string {
  if (bytes === undefined || bytes === null) return '';
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1048576) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / 1048576).toFixed(1)} MB`;
}

function handleUpload(event: Event) {
  const input = event.target as HTMLInputElement;
  if (input.files && input.files.length > 0) {
    // emit is handled in template
  }
}
</script>

<template>
  <div class="file-list" v-loading="loading">
    <div v-for="file in files" :key="file.id" class="file-list__item">
      <div class="file-list__info">
        <span class="file-list__icon">📄</span>
        <div class="file-list__meta">
          <span class="file-list__name">{{ file.fileName }}</span>
          <span class="file-list__detail">
            <template v-if="file.fileType">{{ file.fileType }}</template>
            <template v-if="file.fileSize"> · {{ formatSize(file.fileSize) }}</template>
          </span>
        </div>
      </div>
      <div class="file-list__actions">
        <el-button text size="small" type="primary" @click="$emit('preview', file)">预览</el-button>
        <el-button v-if="editable" text size="small" type="danger" @click="$emit('delete', file)">删除</el-button>
      </div>
    </div>
    <div v-if="files.length === 0" class="file-list__empty">暂无文件</div>
    <label v-if="editable" class="file-list__upload">
      <input
        type="file"
        multiple
        class="file-list__input"
        @change="(e) => { const t = e.target as HTMLInputElement; if (t.files) $emit('upload', t.files); t.value = ''; }"
      >
      <span class="file-list__upload-text">+ 追加文件</span>
    </label>
  </div>
</template>

<style scoped>
.file-list {
  display: flex;
  flex-direction: column;
  gap: var(--sp-1);
}

.file-list__item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: var(--sp-2) var(--sp-3);
  border-radius: var(--radius-sm);
  border: 1px solid var(--border-light);
  transition: background var(--duration-fast) var(--ease-default);
}

.file-list__item:hover {
  background: var(--bg-hover);
}

.file-list__info {
  display: flex;
  align-items: center;
  gap: var(--sp-2);
  min-width: 0;
}

.file-list__icon {
  font-size: 16px;
  flex-shrink: 0;
}

.file-list__meta {
  display: flex;
  flex-direction: column;
  min-width: 0;
}

.file-list__name {
  font-size: var(--text-sm);
  font-weight: var(--weight-medium);
  color: var(--text-primary);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.file-list__detail {
  font-size: var(--text-xs);
  color: var(--text-tertiary);
}

.file-list__actions {
  display: flex;
  gap: var(--sp-1);
  flex-shrink: 0;
}

.file-list__empty {
  padding: var(--sp-4);
  text-align: center;
  color: var(--text-tertiary);
  font-size: var(--text-sm);
}

.file-list__upload {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: var(--sp-3);
  border: 1px dashed var(--border);
  border-radius: var(--radius-sm);
  cursor: pointer;
  transition: border-color var(--duration-fast) var(--ease-default),
              background var(--duration-fast) var(--ease-default);
}

.file-list__upload:hover {
  border-color: var(--accent);
  background: var(--accent-subtle);
}

.file-list__input {
  display: none;
}

.file-list__upload-text {
  font-size: var(--text-sm);
  color: var(--accent);
  font-weight: var(--weight-medium);
}
</style>
