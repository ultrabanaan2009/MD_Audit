<template>
  <div class="card">
    <!-- 头部汇总 -->
    <div class="flex items-center justify-between mb-6">
      <h2 class="text-xl font-bold text-gray-800 flex items-center gap-2">
        <svg class="w-6 h-6 text-purple-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 17v-2m3 2v-4m3 4v-6m2 10H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
        </svg>
        批量分析结果
      </h2>
      <span class="px-3 py-1 bg-purple-100 text-purple-700 text-sm font-medium rounded-full">
        {{ results.total_files }} 个文件
      </span>
    </div>

    <!-- 统计卡片 -->
    <div class="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
      <div class="p-4 bg-gradient-to-br from-blue-50 to-blue-100 rounded-xl">
        <p class="text-sm text-blue-600 font-medium">总文件数</p>
        <p class="text-2xl font-bold text-blue-700">{{ results.total_files }}</p>
      </div>
      <div class="p-4 bg-gradient-to-br from-green-50 to-green-100 rounded-xl">
        <p class="text-sm text-green-600 font-medium">成功</p>
        <p class="text-2xl font-bold text-green-700">{{ results.success_count }}</p>
      </div>
      <div class="p-4 bg-gradient-to-br from-red-50 to-red-100 rounded-xl">
        <p class="text-sm text-red-600 font-medium">失败</p>
        <p class="text-2xl font-bold text-red-700">{{ results.failed_count }}</p>
      </div>
      <div class="p-4 bg-gradient-to-br from-purple-50 to-purple-100 rounded-xl">
        <p class="text-sm text-purple-600 font-medium">平均分</p>
        <p class="text-2xl font-bold text-purple-700">{{ results.average_score.toFixed(1) }}</p>
      </div>
    </div>

    <!-- 文件结果列表 -->
    <div class="space-y-3">
      <div
        v-for="(item, index) in results.results"
        :key="index"
        :class="[
          'p-4 rounded-xl border transition-all duration-200 cursor-pointer',
          item.success
            ? 'bg-white border-gray-200 hover:border-blue-300 hover:shadow-md'
            : 'bg-red-50 border-red-200'
        ]"
        @click="item.success && goToDetail(item.history_id)"
      >
        <div class="flex items-center justify-between">
          <div class="flex items-center gap-3 flex-1 min-w-0">
            <!-- 状态图标 -->
            <div :class="[
              'w-10 h-10 rounded-lg flex items-center justify-center shrink-0',
              item.success ? getScoreColorClass(item.total_score) : 'bg-red-100'
            ]">
              <svg v-if="item.success" class="w-5 h-5" :class="getScoreTextClass(item.total_score)" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
              <svg v-else class="w-5 h-5 text-red-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
            </div>

            <!-- 文件信息 -->
            <div class="flex-1 min-w-0">
              <p class="font-medium text-gray-800 truncate">{{ item.file_name }}</p>
              <p v-if="item.success" class="text-sm text-gray-500">
                规则: {{ item.rules_score.toFixed(1) }} | AI: {{ item.ai_score.toFixed(1) }}
              </p>
              <p v-else class="text-sm text-red-500">{{ item.error }}</p>
            </div>
          </div>

          <!-- 分数展示 -->
          <div v-if="item.success" class="flex items-center gap-3">
            <div :class="[
              'text-2xl font-bold',
              getScoreTextClass(item.total_score)
            ]">
              {{ item.total_score.toFixed(1) }}
            </div>
            <svg class="w-5 h-5 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7" />
            </svg>
          </div>
        </div>
      </div>
    </div>

    <!-- 提示 -->
    <div class="mt-4 p-3 bg-gray-50 rounded-lg text-sm text-gray-500 text-center">
      点击任意成功项查看详细报告
    </div>
  </div>
</template>

<script setup>
import { useRouter } from 'vue-router'

const props = defineProps({
  results: {
    type: Object,
    required: true
  }
})

const router = useRouter()

const goToDetail = (historyId) => {
  if (historyId) {
    router.push(`/history/${historyId}`)
  }
}

const getScoreColorClass = (score) => {
  if (score >= 80) return 'bg-green-100'
  if (score >= 60) return 'bg-yellow-100'
  return 'bg-red-100'
}

const getScoreTextClass = (score) => {
  if (score >= 80) return 'text-green-600'
  if (score >= 60) return 'text-yellow-600'
  return 'text-red-600'
}
</script>
