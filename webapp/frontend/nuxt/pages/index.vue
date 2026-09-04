<script setup lang="ts">
type Employee = { id: number; name: string; department: string };
type Duty = {
  id: number;
  employee_name: string;
  area_name: string;
  scheduled_date: string;
  status: string;
};

const employees = ref<Employee[]>([]);
const duties = ref<Duty[]>([]);
const busy = ref(false);

const load = async () => {
  const [e, d] = await Promise.all([
    $fetch<Employee[]>("/api/people"),
    $fetch<Duty[]>("/api/lottery-results"),
  ]);
  employees.value = e;
  duties.value = d;
};

onMounted(() => {
  load().catch(console.error);
});

const generate = async () => {
  busy.value = true;
  try {
    const r = await $fetch<{ created: number }>("/api/lottery-results/generate", { method: "POST" });
    alert(`生成: ${r.created} 件`);
    await load();
  } finally {
    busy.value = false;
  }
};
</script>

<template>
  <main style="font-family: system-ui; padding: 24px; max-width: 960px; margin: 0 auto">
    <h1>社内掃除当番アプリ (Nuxt)</h1>
    <button :disabled="busy" style="padding: 8px 16px" @click="generate">
      {{ busy ? "生成中..." : "翌週の当番を生成" }}
    </button>

    <h2>社員一覧 ({{ employees.length }})</h2>
    <ul>
      <li v-for="e in employees" :key="e.id">
        {{ e.name }} <small style="color:#666">({{ e.department }})</small>
      </li>
    </ul>

    <h2>当番一覧 ({{ duties.length }})</h2>
    <table style="border-collapse: collapse; width: 100%">
      <thead>
        <tr>
          <th class="th">日付</th>
          <th class="th">エリア</th>
          <th class="th">担当</th>
          <th class="th">状態</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="d in duties" :key="d.id">
          <td class="td">{{ d.scheduled_date }}</td>
          <td class="td">{{ d.area_name }}</td>
          <td class="td">{{ d.employee_name }}</td>
          <td class="td">{{ d.status }}</td>
        </tr>
      </tbody>
    </table>
  </main>
</template>

<style>
.th { border: 1px solid #ddd; padding: 8px; background: #f5f5f5; text-align: left; }
.td { border: 1px solid #ddd; padding: 8px; }
</style>
