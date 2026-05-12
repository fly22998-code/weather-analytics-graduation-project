<template>
  <div class="server-status-content">
    <div class="page-operations">
      <h2 class="page-title">服务器状态监控</h2>
      <el-button
        type="primary"
        class="refresh-btn"
        @click="fetchServerStatus(true)"
        :loading="isFetchingServerStatus"
      >
        <el-icon><Refresh /></el-icon>
        刷新状态
      </el-button>
    </div>

    <el-card class="status-overview-card">
      <div class="status-grid">
        <div class="status-card">
          <div class="status-card-header">
            <el-icon class="status-icon"><Cpu /></el-icon>
            <span class="status-label">CPU 状态</span>
          </div>
          <div class="status-value" :class="getStatusClass(serverStatus.cpu?.usage_percent, 'cpu')">
            {{ serverStatus.cpu?.usage_percent || 0 }}%
          </div>
          <div class="progress-wrapper">
            <el-progress
              :percentage="serverStatus.cpu?.usage_percent || 0"
              :color="getProgressColor(serverStatus.cpu?.usage_percent || 0, 'cpu')"
              :stroke-width="8"
              :show-text="false"
            />
            <span class="progress-text">{{ serverStatus.cpu?.usage_percent || 0 }}%</span>
          </div>
          <div class="status-details">
            <div class="detail-item">
              <span class="detail-label">核心数:</span>
              <span class="detail-value">{{ serverStatus.cpu?.cores_logical || 0 }} (物理: {{ serverStatus.cpu?.cores_physical || 0 }})</span>
            </div>
            <div class="detail-item">
              <span class="detail-label">频率:</span>
              <span class="detail-value">{{ (serverStatus.cpu?.frequency_current || 0).toFixed(0) }} MHz</span>
            </div>
            <div class="detail-item">
              <span class="detail-label">负载均值:</span>
              <span class="detail-value">{{ formatLoadAvg(serverStatus.cpu?.load_avg) }}</span>
            </div>
          </div>
        </div>

        <div class="status-card">
          <div class="status-card-header">
            <el-icon class="status-icon"><Coin /></el-icon>
            <span class="status-label">内存状态</span>
          </div>
          <div class="status-value" :class="getStatusClass(serverStatus.memory?.used_percent, 'memory')">
            {{ serverStatus.memory?.used_percent || 0 }}%
          </div>
          <div class="progress-wrapper">
            <el-progress
              :percentage="serverStatus.memory?.used_percent || 0"
              :color="getProgressColor(serverStatus.memory?.used_percent || 0, 'memory')"
              :stroke-width="8"
              :show-text="false"
            />
            <span class="progress-text">{{ serverStatus.memory?.used_percent || 0 }}%</span>
          </div>
          <div class="status-details">
            <div class="detail-item">
              <span class="detail-label">已使用:</span>
              <span class="detail-value">{{ formatBytes(serverStatus.memory?.used || 0) }}</span>
            </div>
            <div class="detail-item">
              <span class="detail-label">可用:</span>
              <span class="detail-value">{{ formatBytes(serverStatus.memory?.available || 0) }}</span>
            </div>
            <div class="detail-item">
              <span class="detail-label">总计:</span>
              <span class="detail-value">{{ formatBytes(serverStatus.memory?.total || 0) }}</span>
            </div>
          </div>
        </div>

        <div class="status-card">
          <div class="status-card-header">
            <el-icon class="status-icon"><DataBoard /></el-icon>
            <span class="status-label">磁盘 IO 状态</span>
          </div>
          <div class="disk-io-values">
            <div class="io-item">
              <span class="io-label">读取:</span>
              <span class="io-value">{{ serverStatus.disk?.read_speed || '0.00 MB/s' }}</span>
            </div>
            <div class="io-item">
              <span class="io-label">写入:</span>
              <span class="io-value">{{ serverStatus.disk?.write_speed || '0.00 MB/s' }}</span>
            </div>
          </div>
          <div v-if="serverStatus.disk?.utilization_percent !== undefined && serverStatus.disk?.utilization_percent !== null" class="progress-wrapper">
            <span class="progress-label">利用率:</span>
            <el-progress
              :percentage="serverStatus.disk.utilization_percent"
              :color="getIoProgressColor(serverStatus.disk.utilization_percent)"
              :stroke-width="6"
              :show-text="false"
              class="io-progress"
            />
            <span class="progress-text">{{ serverStatus.disk.utilization_percent.toFixed(1) }}%</span>
          </div>
          <div class="status-details">
            <div class="detail-item">
              <span class="detail-label">读取总量:</span>
              <span class="detail-value">{{ formatBytes(serverStatus.disk?.total_read_bytes || 0) }}</span>
            </div>
            <div class="detail-item">
              <span class="detail-label">写入总量:</span>
              <span class="detail-value">{{ formatBytes(serverStatus.disk?.total_write_bytes || 0) }}</span>
            </div>
            <div class="detail-item">
              <span class="detail-label">IOPS:</span>
              <span class="detail-value">{{ Math.round((serverStatus.disk?.read_count_per_sec || 0) + (serverStatus.disk?.write_count_per_sec || 0)) }}</span>
            </div>
          </div>
        </div>

        <div class="status-card">
          <div class="status-card-header">
            <el-icon class="status-icon"><Connection /></el-icon>
            <span class="status-label">网络状态</span>
          </div>
          <div class="network-values">
            <div class="network-item">
              <span class="network-label">发送速率:</span>
              <span class="network-value">{{ serverStatus.network?.sent_speed || '0 B/s' }}</span>
            </div>
            <div class="network-item">
              <span class="network-label">接收速率:</span>
              <span class="network-value">{{ serverStatus.network?.recv_speed || '0 B/s' }}</span>
            </div>
          </div>
          <div class="status-details">
            <div class="detail-item">
              <span class="detail-label">累计发送:</span>
              <span class="detail-value">{{ formatBytes(serverStatus.network?.bytes_sent || 0) }}</span>
            </div>
            <div class="detail-item">
              <span class="detail-label">累计接收:</span>
              <span class="detail-value">{{ formatBytes(serverStatus.network?.bytes_recv || 0) }}</span>
            </div>
            <div class="detail-item">
              <span class="detail-label">数据包发送:</span>
              <span class="detail-value">{{ formatNumber(serverStatus.network?.packets_sent || 0) }}</span>
            </div>
            <div class="detail-item">
              <span class="detail-label">数据包接收:</span>
              <span class="detail-value">{{ formatNumber(serverStatus.network?.packets_recv || 0) }}</span>
            </div>
            <div class="detail-item">
              <span class="detail-label">错误数:</span>
              <span class="detail-value">{{ serverStatus.network?.errin || 0 }}/{{ serverStatus.network?.errout || 0 }}</span>
            </div>
          </div>
        </div>
      </div>
    </el-card>

    <el-card class="chart-card">
      <div class="chart-header">
        <h3 class="chart-title">实时监控趋势</h3>
        <el-select
          v-model="selectedMetric"
          size="small"
          class="metric-selector"
          @change="updateChartData"
        >
          <el-option label="CPU使用率" value="cpu" />
          <el-option label="内存使用率" value="memory" />
          <el-option label="磁盘IO速率" value="disk" />
          <el-option label="网络速率" value="network" />
        </el-select>
      </div>
      <div class="chart-container">
        <div id="status-chart" class="chart" ref="chartRef"></div>
      </div>
    </el-card>

    <el-card class="disk-partitions-card">
      <h3 class="section-title">磁盘分区详情</h3>
      <div class="disk-table-container">
        <el-table
          :data="serverStatus.disk?.partitions || [{
            device: '未知',
            mountpoint: '未知',
            fstype: '未知',
            total: 0,
            used: 0,
            free: 0,
            used_percent: 0
          }]"
          border
          size="small"
          style="width: 100%;"
        >
          <el-table-column prop="device" label="设备" min-width="100" />
          <el-table-column prop="mountpoint" label="挂载点" min-width="100" />
          <el-table-column prop="fstype" label="文件系统" min-width="80" />
          <el-table-column
            label="总容量"
            min-width="100"
            :formatter="(row) => row.total ? formatBytes(row.total) : '未知'"
          />
          <el-table-column
            label="已使用"
            min-width="100"
            :formatter="(row) => row.used ? formatBytes(row.used) : '未知'"
          />
          <el-table-column
            label="可用"
            min-width="100"
            :formatter="(row) => row.free ? formatBytes(row.free) : '未知'"
          />
          <el-table-column label="使用率" min-width="120">
            <template #default="scope">
              <div class="simple-progress-wrapper">
                <el-progress
                  :percentage="scope.row.percent || 0"
                  :color="getProgressColor(scope.row.percent || 0, 'disk')"
                  :stroke-width="5"
                  :show-text="false"
                  class="simple-progress"
                />
                <span class="simple-progress-text">{{ scope.row.percent ? scope.row.percent.toFixed(1) + '%' : '未知' }}</span>
              </div>
            </template>
          </el-table-column>
        </el-table>
      </div>
    </el-card>

    <el-card class="system-info-card">
      <h3 class="section-title">系统信息</h3>
      <div class="system-info-grid">
        <div class="info-item">
          <span class="info-label">操作系统:</span>
          <span class="info-value">{{ getOsName(serverStatus.system?.os_name, serverStatus.system?.os_version) || '未知' }}</span>
        </div>
        <div class="info-item">
          <span class="info-label">系统版本:</span>
          <span class="info-value">{{ getOsVersion(serverStatus.system?.os_version) || '未知' }}</span>
        </div>
        <div class="info-item">
          <span class="info-label">主机名:</span>
          <span class="info-value">{{ serverStatus.system?.hostname || '未知' }}</span>
        </div>
        <div class="info-item">
          <span class="info-label">运行时长:</span>
          <span class="info-value">{{ serverStatus.system?.uptime || '未知' }}</span>
        </div>
        <div class="info-item">
          <span class="info-label">进程数:</span>
          <span class="info-value">{{ formatNumber(serverStatus.system?.process_count || 0) }}</span>
        </div>
        <div class="info-item">
          <span class="info-label">Python版本:</span>
          <span class="info-value">{{ serverStatus.system?.python_version || '未知' }}</span>
        </div>
        <div class="info-item">
          <span class="info-label">当前时间:</span>
          <span class="info-value">{{ serverStatus.system?.current_time || '未知' }}</span>
        </div>
        <div class="info-item">
          <span class="info-label">系统负载:</span>
          <span class="info-value">{{ formatLoadAvg(serverStatus.cpu?.load_avg) }}</span>
        </div>
      </div>
    </el-card>

    <div class="refresh-time">
      最后刷新时间: {{ lastRefreshTime }}
      <span v-if="autoRefreshEnabled" class="auto-refresh-tag">自动刷新中</span>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted, watch, shallowRef } from 'vue';
import { ElMessage } from 'element-plus';
import { Coin, Connection, Cpu, DataBoard, Refresh } from '@element-plus/icons-vue';
import request, { hasValidToken, redirectToLogin } from '@/utils/requests';
import { BASE_URL } from '@/store/config';
import { debounce } from 'lodash';
import * as echarts from 'echarts';

let isComponentMounted = true;

const MAX_HISTORY_LENGTH = 20;
const AUTO_REFRESH_INTERVAL_MS = 5000;

const isFetchingServerStatus = ref(false);
const serverStatus = ref<any>({});
const lastRefreshTime = ref('');
const autoRefreshEnabled = ref(true);
const autoRefreshInterval = ref<number | null>(null);
const selectedMetric = ref<'cpu' | 'memory' | 'disk' | 'network'>('cpu');
const chartRef = shallowRef<HTMLDivElement | null>(null);
let chartInstance: echarts.ECharts | null = null;
let currentStatusRequestController: AbortController | null = null;
let lastSuccessfulStatusPayload = '';

const historyData = ref({
  cpu: [] as { time: string; value: number }[],
  memory: [] as { time: string; value: number }[],
  diskRead: [] as { time: string; value: number }[],
  diskWrite: [] as { time: string; value: number }[],
  networkSend: [] as { time: string; value: number }[],
  networkRecv: [] as { time: string; value: number }[]
});

const SERVER_STATUS_API = `${BASE_URL || ''}/weather/admin/users/server-status/`;

const parseNumber = (value: unknown, fallback = 0): number => {
  if (typeof value === 'number' && Number.isFinite(value)) return value;
  if (typeof value === 'string') {
    const parsed = Number.parseFloat(value.replace(/[^0-9.-]/g, ''));
    return Number.isFinite(parsed) ? parsed : fallback;
  }
  return fallback;
};

const clampPercent = (value: unknown): number => {
  const parsed = parseNumber(value, 0);
  return Math.min(100, Math.max(0, Number(parsed.toFixed(1))));
};

const formatBytes = (bytes: number, decimals = 2) => {
  if (!bytes) return '0 Bytes';

  const k = 1024;
  const dm = decimals < 0 ? 0 : decimals;
  const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));

  return `${parseFloat((bytes / Math.pow(k, i)).toFixed(dm))} ${sizes[i]}`;
};

const formatRateFromMb = (mbPerSec: unknown) => {
  const mbValue = parseNumber(mbPerSec, 0);
  return `${formatBytes(mbValue * 1024 * 1024)}/s`;
};

const formatNumber = (num: number) => {
  return num.toString().replace(/\B(?=(\d{3})+(?!\d))/g, ',');
};

const formatLoadAvg = (loadAvg: unknown) => {
  if (!Array.isArray(loadAvg) || loadAvg.length === 0) return '未知';
  return loadAvg.map((item) => parseNumber(item, 0).toFixed(2)).join(', ');
};

const getOsName = (osName: string, osVersion: string) => {
  if (!osName) return '';

  if (osName === 'Windows') {
    if (osVersion?.startsWith('10.0.22')) return 'Windows 11';
    if (osVersion?.startsWith('10.0.')) return 'Windows 10';
    if (osVersion?.startsWith('6.3.')) return 'Windows 8.1';
    if (osVersion?.startsWith('6.2.')) return 'Windows 8';
    if (osVersion?.startsWith('6.1.')) return 'Windows 7';
    return 'Windows';
  }

  return osName === 'Darwin' ? 'macOS' : osName;
};

const getOsVersion = (osVersion: string) => {
  if (!osVersion) return '';
  const winVersionMatch = osVersion.match(/\d+\.\d+\.\d+/);
  return winVersionMatch ? winVersionMatch[0] : osVersion;
};

const getStatusClass = (value: number | undefined, type: string) => {
  if (value === undefined) return 'status-normal';

  if (type === 'cpu') {
    if (value > 80) return 'status-danger';
    if (value > 60) return 'status-warning';
    return 'status-normal';
  }

  if (type === 'memory') {
    if (value > 85) return 'status-danger';
    if (value > 70) return 'status-warning';
    return 'status-normal';
  }

  if (type === 'disk') {
    if (value > 90) return 'status-danger';
    if (value > 80) return 'status-warning';
    return 'status-normal';
  }

  return 'status-normal';
};

const getIoProgressColor = (value: number) => {
  if (value > 80) return '#F56C6C';
  if (value > 50) return '#E6A23C';
  return '#67C23A';
};

const getProgressColor = (value: number | undefined, type: string) => {
  if (value === undefined) return '#67C23A';
  return getStatusClass(value, type) === 'status-danger'
    ? '#F56C6C'
    : getStatusClass(value, type) === 'status-warning'
      ? '#E6A23C'
      : '#67C23A';
};

const normalizeServerStatus = (rawData: any = {}) => {
  return {
    ...rawData,
    cpu: {
      ...rawData?.cpu,
      usage_percent: clampPercent(rawData?.cpu?.usage_percent),
      frequency_current: parseNumber(rawData?.cpu?.frequency_current, 0),
      cores_logical: parseNumber(rawData?.cpu?.cores_logical, 0),
      cores_physical: parseNumber(rawData?.cpu?.cores_physical, 0),
      load_avg: Array.isArray(rawData?.cpu?.load_avg) ? rawData.cpu.load_avg.map((item: unknown) => parseNumber(item, 0)) : []
    },
    memory: {
      ...rawData?.memory,
      used_percent: clampPercent(rawData?.memory?.used_percent),
      used: parseNumber(rawData?.memory?.used, 0),
      available: parseNumber(rawData?.memory?.available, 0),
      total: parseNumber(rawData?.memory?.total, 0)
    },
    disk: {
      ...rawData?.disk,
      read_mb_per_sec: parseNumber(rawData?.disk?.read_mb_per_sec, 0),
      write_mb_per_sec: parseNumber(rawData?.disk?.write_mb_per_sec, 0),
      read_speed: formatRateFromMb(rawData?.disk?.read_mb_per_sec),
      write_speed: formatRateFromMb(rawData?.disk?.write_mb_per_sec),
      total_read_bytes: parseNumber(rawData?.disk?.total_read_bytes, 0),
      total_write_bytes: parseNumber(rawData?.disk?.total_write_bytes, 0),
      read_count_per_sec: parseNumber(rawData?.disk?.read_count_per_sec, 0),
      write_count_per_sec: parseNumber(rawData?.disk?.write_count_per_sec, 0),
      utilization_percent: rawData?.disk?.utilization_percent === undefined || rawData?.disk?.utilization_percent === null
        ? undefined
        : clampPercent(rawData?.disk?.utilization_percent),
      partitions: Array.isArray(rawData?.disk?.partitions)
        ? rawData.disk.partitions.map((partition: any) => ({
            ...partition,
            total: parseNumber(partition?.total, 0),
            used: parseNumber(partition?.used, 0),
            free: parseNumber(partition?.free, 0),
            percent: clampPercent(partition?.percent ?? partition?.used_percent)
          }))
        : []
    },
    network: {
      ...rawData?.network,
      sent_mb_per_sec: parseNumber(rawData?.network?.sent_mb_per_sec, 0),
      recv_mb_per_sec: parseNumber(rawData?.network?.recv_mb_per_sec, 0),
      sent_speed: formatRateFromMb(rawData?.network?.sent_mb_per_sec),
      recv_speed: formatRateFromMb(rawData?.network?.recv_mb_per_sec),
      bytes_sent: parseNumber(rawData?.network?.bytes_sent, 0),
      bytes_recv: parseNumber(rawData?.network?.bytes_recv, 0),
      packets_sent: parseNumber(rawData?.network?.packets_sent, 0),
      packets_recv: parseNumber(rawData?.network?.packets_recv, 0),
      errin: parseNumber(rawData?.network?.errin, 0),
      errout: parseNumber(rawData?.network?.errout, 0)
    },
    system: {
      ...rawData?.system,
      process_count: parseNumber(rawData?.system?.process_count, 0)
    }
  };
};

const createSeries = (name: string, data: number[], color: string, gradientTop: string, gradientBottom: string) => ({
  name,
  type: 'line',
  data,
  smooth: true,
  showSymbol: false,
  lineStyle: { width: 2 },
  itemStyle: { color },
  areaStyle: {
    color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
      { offset: 0, color: gradientTop },
      { offset: 1, color: gradientBottom }
    ])
  }
});

const getChartConfig = () => {
  switch (selectedMetric.value) {
    case 'memory':
      return {
        title: '内存使用率趋势',
        legend: ['内存使用率'],
        unit: '%',
        max: 100,
        xAxisData: historyData.value.memory.map((item) => item.time),
        series: [createSeries('内存使用率', historyData.value.memory.map((item) => item.value), '#67c23a', 'rgba(103, 194, 58, 0.3)', 'rgba(103, 194, 58, 0.05)')]
      };
    case 'disk':
      return {
        title: '磁盘IO速率趋势',
        legend: ['读取速率', '写入速率'],
        unit: 'MB/s',
        xAxisData: historyData.value.diskRead.map((item) => item.time),
        series: [
          createSeries('读取速率', historyData.value.diskRead.map((item) => item.value), '#e6a23c', 'rgba(230, 162, 60, 0.3)', 'rgba(230, 162, 60, 0.05)'),
          createSeries('写入速率', historyData.value.diskWrite.map((item) => item.value), '#f56c6c', 'rgba(245, 108, 108, 0.3)', 'rgba(245, 108, 108, 0.05)')
        ]
      };
    case 'network':
      return {
        title: '网络速率趋势',
        legend: ['发送速率', '接收速率'],
        unit: 'MB/s',
        xAxisData: historyData.value.networkSend.map((item) => item.time),
        series: [
          createSeries('发送速率', historyData.value.networkSend.map((item) => item.value), '#909399', 'rgba(144, 147, 153, 0.3)', 'rgba(144, 147, 153, 0.05)'),
          createSeries('接收速率', historyData.value.networkRecv.map((item) => item.value), '#722ed1', 'rgba(114, 46, 209, 0.3)', 'rgba(114, 46, 209, 0.05)')
        ]
      };
    case 'cpu':
    default:
      return {
        title: 'CPU使用率趋势',
        legend: ['CPU使用率'],
        unit: '%',
        max: 100,
        xAxisData: historyData.value.cpu.map((item) => item.time),
        series: [createSeries('CPU使用率', historyData.value.cpu.map((item) => item.value), '#409eff', 'rgba(64, 158, 255, 0.3)', 'rgba(64, 158, 255, 0.05)')]
      };
  }
};

const initChart = () => {
  if (!chartRef.value) return;
  chartInstance = echarts.init(chartRef.value);
  updateChartData();
  window.addEventListener('resize', resizeChart);
};

const resizeChart = debounce(() => {
  chartInstance?.resize();
}, 120);

const updateChartData = () => {
  if (!chartInstance) return;

  const config = getChartConfig();

  chartInstance.setOption(
    {
      title: {
        text: config.title,
        left: 'center',
        textStyle: { fontSize: 14, fontWeight: 500 }
      },
      tooltip: {
        trigger: 'axis',
        formatter(params: any[]) {
          let result = `${params[0]?.name || ''}<br/>`;
          params.forEach((param) => {
            result += `${param.seriesName}: ${param.value}${config.unit === '%' ? '%' : ` ${config.unit}`}<br/>`;
          });
          return result;
        }
      },
      legend: {
        data: config.legend,
        top: 30
      },
      grid: {
        left: '3%',
        right: '4%',
        bottom: '3%',
        containLabel: true
      },
      xAxis: {
        type: 'category',
        boundaryGap: false,
        data: config.xAxisData,
        axisLabel: { fontSize: 11 }
      },
      yAxis: {
        type: 'value',
        max: config.max,
        axisLabel: {
          fontSize: 11,
          formatter: config.unit === '%' ? '{value} %' : `{value} ${config.unit}`
        }
      },
      series: config.series
    },
    { notMerge: true, lazyUpdate: true }
  );
};

const pushHistoryPoint = (collection: { time: string; value: number }[], point: { time: string; value: number }) => {
  collection.push(point);
  if (collection.length > MAX_HISTORY_LENGTH) {
    collection.shift();
  }
};

const addHistoryData = () => {
  const timeStr = new Date().toLocaleTimeString('zh-CN', {
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit'
  });

  pushHistoryPoint(historyData.value.cpu, {
    time: timeStr,
    value: parseNumber(serverStatus.value.cpu?.usage_percent, 0)
  });

  pushHistoryPoint(historyData.value.memory, {
    time: timeStr,
    value: parseNumber(serverStatus.value.memory?.used_percent, 0)
  });

  pushHistoryPoint(historyData.value.diskRead, {
    time: timeStr,
    value: Number(parseNumber(serverStatus.value.disk?.read_mb_per_sec, 0).toFixed(2))
  });

  pushHistoryPoint(historyData.value.diskWrite, {
    time: timeStr,
    value: Number(parseNumber(serverStatus.value.disk?.write_mb_per_sec, 0).toFixed(2))
  });

  pushHistoryPoint(historyData.value.networkSend, {
    time: timeStr,
    value: Number(parseNumber(serverStatus.value.network?.sent_mb_per_sec, 0).toFixed(2))
  });

  pushHistoryPoint(historyData.value.networkRecv, {
    time: timeStr,
    value: Number(parseNumber(serverStatus.value.network?.recv_mb_per_sec, 0).toFixed(2))
  });

  updateChartData();
};

const fetchServerStatus = debounce(async (forceRefresh = false) => {
  if (!isComponentMounted) return;
  if (!hasValidToken()) {
    redirectToLogin();
    return;
  }

  if (isFetchingServerStatus.value && !forceRefresh) {
    return;
  }

  currentStatusRequestController?.abort();
  currentStatusRequestController = new AbortController();
  isFetchingServerStatus.value = true;

  try {
    const res = await request.get(SERVER_STATUS_API, {
      timeout: 15000,
      signal: currentStatusRequestController.signal
    });

    if (!isComponentMounted) return;

    if (res.data.status === 'success') {
      const normalized = normalizeServerStatus(res.data.data || {});
      const payloadKey = JSON.stringify(normalized);

      if (!forceRefresh && payloadKey === lastSuccessfulStatusPayload) {
        lastRefreshTime.value = new Date().toLocaleString('zh-CN');
        return;
      }

      lastSuccessfulStatusPayload = payloadKey;
      serverStatus.value = normalized;
      lastRefreshTime.value = new Date().toLocaleString('zh-CN');
      addHistoryData();
    } else {
      ElMessage.error(res.data.message || '获取服务器状态失败');
    }
  } catch (error: any) {
    if (error?.name === 'CanceledError' || error?.name === 'AbortError' || error?.code === 'ERR_CANCELED') {
      return;
    }

    console.error('获取服务器状态失败:', error);
    if (!isComponentMounted) return;
    ElMessage.error('获取服务器状态失败，请稍后重试');
  } finally {
    currentStatusRequestController = null;
    if (isComponentMounted) {
      isFetchingServerStatus.value = false;
    }
  }
}, 300);

const startAutoRefresh = () => {
  stopAutoRefresh();
  autoRefreshInterval.value = window.setInterval(() => {
    if (isComponentMounted && autoRefreshEnabled.value) {
      fetchServerStatus(false);
    }
  }, AUTO_REFRESH_INTERVAL_MS);
};

const stopAutoRefresh = () => {
  if (autoRefreshInterval.value) {
    clearInterval(autoRefreshInterval.value);
    autoRefreshInterval.value = null;
  }
};

watch(selectedMetric, () => {
  updateChartData();
});

onMounted(() => {
  isComponentMounted = true;
  initChart();
  fetchServerStatus(true);
  if (autoRefreshEnabled.value) {
    startAutoRefresh();
  }
});

onUnmounted(() => {
  isComponentMounted = false;
  stopAutoRefresh();
  currentStatusRequestController?.abort();
  fetchServerStatus.cancel();
  resizeChart.cancel();
  if (chartInstance) {
    chartInstance.dispose();
    chartInstance = null;
  }
  window.removeEventListener('resize', resizeChart);
});
</script>

<style scoped>
/* 鍘熸湁鏍峰紡淇濇寔涓嶅彉 */
.server-status-content {
  padding: 16px;
  height: 100%;
  box-sizing: border-box;
  overflow-y: auto;
  background-color: #f8fafc;
  min-width: 1000px;
}

.page-operations {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
  flex-wrap: wrap;
  gap: 10px;
}

.page-title {
  margin: 0;
  font-size: 18px;
  font-weight: 600;
  color: #1e293b;
  padding-left: 6px;
  border-left: 3px solid #409eff;
}

.refresh-btn {
  display: flex;
  align-items: center;
  gap: 4px;
}

/* 鏂板锛氬浘琛ㄦ牱寮?*/
.chart-card {
  margin-bottom: 16px;
  border-radius: 6px;
}

.chart-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.chart-title {
  font-size: 16px;
  font-weight: 600;
  color: #303133;
  margin: 0;
}

.metric-selector {
  width: 140px;
}

.chart-container {
  width: 100%;
  height: 300px;
}

.chart {
  width: 100%;
  height: 100%;
}

.status-overview-card {
  margin-bottom: 16px;
  border-radius: 6px;
}

.status-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
  gap: 16px;
  padding: 16px;
}

.status-card {
  background: #fff;
  border-radius: 8px;
  padding: 20px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
  transition: all 0.2s;
  min-width: 300px;
}

.status-card:hover {
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.1);
  transform: translateY(-2px);
}

.status-card-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 16px;
}

.status-icon {
  font-size: 18px;
  color: #409eff;
}

.status-label {
  font-size: 14px;
  font-weight: 600;
  color: #303133;
}

.status-value {
  font-size: 28px;
  font-weight: 700;
  text-align: center;
  margin: 16px 0;
}

.progress-wrapper {
  display: flex;
  align-items: center;
  gap: 8px;
  margin: 16px 0;
  width: 100%;
}

.progress-label {
  font-size: 12px;
  color: #606266;
  min-width: 60px;
}

.progress-text {
  font-size: 14px;
  font-weight: 600;
  min-width: 50px;
  text-align: right;
}

.io-progress {
  flex: 1;
}

.disk-io-values {
  display: flex;
  justify-content: space-between;
  margin: 16px 0;
  padding: 8px;
  background-color: #f8f9fa;
  border-radius: 4px;
}

.io-item {
  text-align: center;
}

.io-label {
  font-size: 12px;
  color: #606266;
  display: block;
}

.io-value {
  font-size: 18px;
  font-weight: 600;
  color: #303133;
}

.network-values {
  display: flex;
  justify-content: space-between;
  margin: 16px 0;
  padding: 8px;
  background-color: #f8f9fa;
  border-radius: 4px;
}

.network-item {
  text-align: center;
}

.network-label {
  font-size: 12px;
  color: #606266;
  display: block;
}

.network-value {
  font-size: 16px;
  font-weight: 600;
  color: #303133;
}

.status-normal {
  color: #67C23A;
}

.status-warning {
  color: #E6A23C;
}

.status-danger {
  color: #F56C6C;
}

.status-details {
  margin-top: 16px;
  font-size: 12px;
  color: #606266;
}

.detail-item {
  display: flex;
  justify-content: space-between;
  margin-bottom: 8px;
  padding: 4px 0;
  border-bottom: 1px dashed #f0f0f0;
}

.detail-item:last-child {
  border-bottom: none;
}

.detail-label {
  color: #909399;
  min-width: 80px;
}

.detail-value {
  font-weight: 500;
  text-align: right;
  word-break: break-all;
}

.disk-partitions-card {
  margin-bottom: 16px;
  border-radius: 6px;
}

.disk-table-container {
  overflow-x: auto;
  padding: 0 8px;
}

.simple-progress-wrapper {
  display: flex;
  align-items: center;
  gap: 6px;
  width: 100%;
}

.simple-progress {
  flex: 1;
}

.simple-progress-text {
  font-size: 11px;
  font-weight: 500;
  min-width: 45px;
  color: #606266;
}

.system-info-card {
  margin-bottom: 16px;
  border-radius: 6px;
}

.section-title {
  font-size: 16px;
  font-weight: 600;
  color: #303133;
  margin: 0 0 16px 0;
  padding-bottom: 8px;
  border-bottom: 1px solid #e2e8f0;
}

.system-info-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 16px;
  padding: 8px;
}

.info-item {
  display: flex;
  flex-direction: column;
  padding: 8px 0;
  border-bottom: 1px dashed #f0f0f0;
}

.info-item:last-child {
  border-bottom: none;
}

.info-label {
  color: #606266;
  font-weight: 500;
  font-size: 12px;
  margin-bottom: 4px;
}

.info-value {
  color: #303133;
  font-weight: 600;
  font-size: 14px;
  word-break: break-all;
}

.refresh-time {
  font-size: 12px;
  color: #909399;
  text-align: right;
  padding: 8px 0;
}

.auto-refresh-tag {
  display: inline-block;
  margin-left: 8px;
  padding: 2px 6px;
  background-color: #e1f5fe;
  color: #03a9f4;
  border-radius: 3px;
  font-size: 11px;
}

@media (max-width: 1200px) {
  .status-grid {
    grid-template-columns: repeat(2, 1fr);
  }
}

@media (max-width: 768px) {
  .status-grid {
    grid-template-columns: 1fr;
  }
  
  .system-info-grid {
    grid-template-columns: 1fr;
  }
  
  .page-operations {
    flex-direction: column;
    align-items: flex-start;
  }
  
  .refresh-btn {
    width: 100%;
    justify-content: center;
  }
  
  .server-status-content {
    min-width: auto;
    padding: 8px;
  }
  
  .chart-container {
    height: 250px;
  }
}
</style>

