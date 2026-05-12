<template>
  <div class="traffic-page">
    <header class="traffic-header">
      <div>
        <h2>流量统计</h2>
        <span>{{ updatedAt || '等待刷新' }}</span>
      </div>
      <el-button :icon="Refresh" :loading="loading" type="primary" plain @click="fetchTrafficStats">
        刷新
      </el-button>
    </header>

    <section class="stat-grid">
      <article v-for="item in statCards" :key="item.label" class="stat-card">
        <span>{{ item.label }}</span>
        <strong>{{ formatNumber(item.value) }}</strong>
        <small>{{ item.hint }}</small>
      </article>
    </section>

    <section class="main-grid">
      <article class="panel trend-panel">
        <div class="panel-title">
          <h3>最近 30 分钟</h3>
          <span>成功率 {{ today.success_rate || 0 }}%</span>
        </div>
        <div ref="chartRef" class="trend-chart"></div>
      </article>

      <article class="panel endpoint-panel">
        <div class="panel-title">
          <h3>接口调用排行</h3>
          <span>今日</span>
        </div>
        <div v-if="endpointStats.length" class="endpoint-list">
          <div v-for="item in endpointStats" :key="item.endpoint" class="endpoint-row">
            <div class="endpoint-main">
              <div class="endpoint-name" :title="item.endpoint">{{ item.endpoint }}</div>
              <div class="endpoint-metrics">
                <strong>{{ formatNumber(item.count) }}</strong>
                <span :class="{ danger: item.error_count > 0 }">
                  异常 {{ formatNumber(item.error_count) }}
                </span>
                <small>{{ item.error_rate || 0 }}%</small>
              </div>
            </div>
            <div v-if="item.users.length" class="endpoint-users">
              <span v-for="user in item.users" :key="`${item.endpoint}-${user.email}`" class="endpoint-user">
                <b :title="user.email">{{ user.email }}</b>
                <em>{{ formatNumber(user.count) }}次</em>
                <em v-if="user.error_count" class="danger">异常{{ formatNumber(user.error_count) }}</em>
              </span>
            </div>
          </div>
        </div>
        <el-empty v-else description="暂无接口统计" :image-size="88" />
      </article>
    </section>

    <section class="panel">
      <div class="panel-title table-title">
        <h3>近 7 天</h3>
        <span>访问次数按 30 分钟会话统计</span>
      </div>
      <el-table :data="dailyRows" stripe class="traffic-table">
        <el-table-column prop="date" label="日期" min-width="130" />
        <el-table-column prop="api_total" label="接口调用" min-width="120">
          <template #default="{ row }">{{ formatNumber(row.api_total) }}</template>
        </el-table-column>
        <el-table-column prop="visit_total" label="访问次数" min-width="120">
          <template #default="{ row }">{{ formatNumber(row.visit_total) }}</template>
        </el-table-column>
        <el-table-column prop="unique_visitors" label="独立访客" min-width="120">
          <template #default="{ row }">{{ formatNumber(row.unique_visitors) }}</template>
        </el-table-column>
        <el-table-column prop="api_success" label="成功" min-width="100">
          <template #default="{ row }">{{ formatNumber(row.api_success) }}</template>
        </el-table-column>
        <el-table-column prop="api_error" label="异常" min-width="100">
          <template #default="{ row }">
            <span :class="{ danger: row.api_error > 0 }">{{ formatNumber(row.api_error) }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="success_rate" label="成功率" min-width="100">
          <template #default="{ row }">{{ row.success_rate || 0 }}%</template>
        </el-table-column>
      </el-table>
    </section>
  </div>
</template>

<script setup lang="ts">
import { computed, nextTick, onMounted, onUnmounted, ref, shallowRef } from 'vue';
import { ElMessage } from 'element-plus';
import { Refresh } from '@element-plus/icons-vue';
import * as echarts from 'echarts';
import request from '@/utils/requests';
import { BASE_URL } from '@/store/config';

type TrafficDay = {
  date: string;
  api_total: number;
  visit_total: number;
  unique_visitors: number;
  api_success: number;
  api_error: number;
  success_rate: number;
};

type MinutePoint = {
  time: string;
  count: number;
};

type EndpointStat = {
  endpoint: string;
  count: number;
  error_count: number;
  error_rate: number;
  users: EndpointUserStat[];
};

type EndpointUserStat = {
  email: string;
  count: number;
  error_count: number;
  error_rate: number;
};

const TRAFFIC_STATS_API = `${BASE_URL || ''}/weather/admin/users/traffic-stats/`;

const loading = ref(false);
const updatedAt = ref('');
const today = ref<TrafficDay>({
  date: '',
  api_total: 0,
  visit_total: 0,
  unique_visitors: 0,
  api_success: 0,
  api_error: 0,
  success_rate: 0
});
const dailyRows = ref<TrafficDay[]>([]);
const minuteSeries = ref<MinutePoint[]>([]);
const endpointStats = ref<EndpointStat[]>([]);
const chartRef = shallowRef<HTMLDivElement | null>(null);
let chartInstance: echarts.ECharts | null = null;
let autoRefreshTimer: number | null = null;

const formatNumber = (value: unknown) => {
  const num = Number(value || 0);
  return Number.isFinite(num) ? num.toLocaleString('zh-CN') : '0';
};

const statCards = computed(() => [
  { label: '接口调用', value: today.value.api_total, hint: '今日累计请求' },
  { label: '访问次数', value: today.value.visit_total, hint: '30 分钟会话' },
  { label: '独立访客', value: today.value.unique_visitors, hint: '用户 / IP 去重' },
  { label: '异常请求', value: today.value.api_error, hint: '4xx / 5xx' }
]);

const normalizeDay = (raw: any = {}): TrafficDay => ({
  date: raw.date || '',
  api_total: Number(raw.api_total || 0),
  visit_total: Number(raw.visit_total || 0),
  unique_visitors: Number(raw.unique_visitors || 0),
  api_success: Number(raw.api_success || 0),
  api_error: Number(raw.api_error || 0),
  success_rate: Number(raw.success_rate || 0)
});

const updateChart = () => {
  if (!chartInstance) return;

  chartInstance.setOption(
    {
      tooltip: {
        trigger: 'axis',
        formatter(params: any[]) {
          const point = params[0];
          return `${point?.axisValue || ''}<br/>请求量：${point?.value || 0}`;
        }
      },
      grid: { left: 36, right: 18, top: 20, bottom: 30 },
      xAxis: {
        type: 'category',
        boundaryGap: false,
        data: minuteSeries.value.map((item) => item.time),
        axisTick: { show: false },
        axisLine: { lineStyle: { color: '#d6dfec' } },
        axisLabel: { color: '#7b8ba3', fontSize: 11 }
      },
      yAxis: {
        type: 'value',
        minInterval: 1,
        splitLine: { lineStyle: { color: 'rgba(120, 142, 166, 0.14)' } },
        axisLabel: { color: '#7b8ba3', fontSize: 11 }
      },
      series: [
        {
          type: 'line',
          smooth: true,
          showSymbol: false,
          data: minuteSeries.value.map((item) => item.count),
          lineStyle: { width: 3, color: '#2563eb' },
          areaStyle: {
            color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
              { offset: 0, color: 'rgba(37, 99, 235, 0.22)' },
              { offset: 1, color: 'rgba(37, 99, 235, 0.02)' }
            ])
          }
        }
      ]
    },
    { notMerge: true, lazyUpdate: true }
  );
};

const resizeChart = () => chartInstance?.resize();

const fetchTrafficStats = async () => {
  if (loading.value) return;
  loading.value = true;

  try {
    const res = await request.get(TRAFFIC_STATS_API, { params: { days: 7 } });
    if (res.data?.status !== 'success') {
      ElMessage.error(res.data?.message || '获取流量统计失败');
      return;
    }

    const data = res.data.data || {};
    today.value = normalizeDay(data.today);
    dailyRows.value = Array.isArray(data.daily) ? data.daily.map(normalizeDay) : [];
    minuteSeries.value = Array.isArray(data.minute_series)
      ? data.minute_series.map((item: any) => ({ time: item.time || '', count: Number(item.count || 0) }))
      : [];
    endpointStats.value = Array.isArray(data.endpoint_stats)
      ? data.endpoint_stats.map((item: any) => ({
          endpoint: item.endpoint || '-',
          count: Number(item.count || 0),
          error_count: Number(item.error_count || 0),
          error_rate: Number(item.error_rate || 0),
          users: Array.isArray(item.users)
            ? item.users.map((user: any) => ({
                email: user.email || '-',
                count: Number(user.count || 0),
                error_count: Number(user.error_count || 0),
                error_rate: Number(user.error_rate || 0)
              }))
            : []
        }))
      : [];
    updatedAt.value = data.updated_at || '';

    await nextTick();
    updateChart();
  } catch (error) {
    console.error('获取流量统计失败:', error);
    ElMessage.error('获取流量统计失败，请稍后重试');
  } finally {
    loading.value = false;
  }
};

onMounted(async () => {
  if (chartRef.value) {
    chartInstance = echarts.init(chartRef.value);
    window.addEventListener('resize', resizeChart);
  }

  await fetchTrafficStats();
  autoRefreshTimer = window.setInterval(fetchTrafficStats, 10000);
});

onUnmounted(() => {
  if (autoRefreshTimer) {
    window.clearInterval(autoRefreshTimer);
    autoRefreshTimer = null;
  }
  window.removeEventListener('resize', resizeChart);
  chartInstance?.dispose();
  chartInstance = null;
});
</script>

<style scoped>
.traffic-page {
  min-height: 100vh;
  padding: 28px;
  background: #f5f7fb;
  color: #172033;
}

.traffic-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  margin-bottom: 18px;
}

.traffic-header h2 {
  margin: 0 0 6px;
  font-size: 24px;
  font-weight: 800;
}

.traffic-header span,
.panel-title span,
.stat-card small {
  color: #8391a7;
  font-size: 13px;
}

.stat-grid {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 14px;
  margin-bottom: 14px;
}

.stat-card,
.panel {
  border: 1px solid #e7edf5;
  border-radius: 18px;
  background: #fff;
  box-shadow: 0 12px 32px rgba(39, 57, 84, 0.06);
}

.stat-card {
  display: grid;
  gap: 8px;
  padding: 20px;
}

.stat-card span {
  color: #64748b;
  font-size: 14px;
  font-weight: 700;
}

.stat-card strong {
  font-size: 30px;
  line-height: 1;
}

.main-grid {
  display: grid;
  grid-template-columns: minmax(0, 1.55fr) minmax(320px, 0.85fr);
  gap: 14px;
  margin-bottom: 14px;
}

.panel {
  padding: 20px;
}

.panel-title {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 14px;
}

.panel-title h3 {
  margin: 0;
  font-size: 17px;
  font-weight: 800;
}

.trend-chart {
  width: 100%;
  height: 280px;
}

.endpoint-list {
  display: grid;
  gap: 8px;
  max-height: 280px;
  overflow: auto;
  padding-right: 2px;
}

.endpoint-row {
  padding: 10px 12px;
  border-radius: 12px;
  background: #f8fafc;
}

.endpoint-main {
  display: grid;
  grid-template-columns: minmax(0, 1fr) 148px;
  align-items: center;
  gap: 12px;
}

.endpoint-name {
  overflow: hidden;
  color: #475569;
  font-size: 13px;
  font-family: Consolas, 'SFMono-Regular', monospace;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.endpoint-metrics {
  display: grid;
  grid-template-columns: 1fr;
  justify-items: end;
  gap: 2px;
}

.endpoint-metrics strong {
  color: #2563eb;
  font-size: 14px;
}

.endpoint-metrics span,
.endpoint-metrics small {
  color: #8391a7;
  font-size: 12px;
}

.endpoint-users {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  margin-top: 8px;
}

.endpoint-user {
  display: inline-flex;
  align-items: center;
  max-width: 100%;
  gap: 6px;
  padding: 4px 8px;
  border-radius: 999px;
  background: #eef4ff;
  color: #64748b;
  font-size: 12px;
}

.endpoint-user b {
  overflow: hidden;
  max-width: 180px;
  color: #334155;
  font-weight: 700;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.endpoint-user em {
  color: #64748b;
  font-style: normal;
}

.traffic-table {
  width: 100%;
}

.danger {
  color: #dc2626;
  font-weight: 700;
}

@media (max-width: 1200px) {
  .stat-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }

  .main-grid {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 720px) {
  .traffic-page {
    padding: 18px;
  }

  .traffic-header {
    align-items: flex-start;
    flex-direction: column;
  }

  .stat-grid {
    grid-template-columns: 1fr;
  }
}
</style>
