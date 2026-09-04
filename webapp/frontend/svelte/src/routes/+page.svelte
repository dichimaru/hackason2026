<script>
  import { onMount } from "svelte";

  let employees = [];
  let duties = [];
  let busy = false;

  async function load() {
    const [e, d] = await Promise.all([
      fetch("/api/people").then((r) => r.json()),
      fetch("/api/lottery-results").then((r) => r.json()),
    ]);
    employees = e;
    duties = d;
  }
  onMount(() => { load().catch(console.error); });

  async function generate() {
    busy = true;
    try {
      const r = await fetch("/api/lottery-results/generate", { method: "POST" });
      const j = await r.json();
      alert(`生成: ${j.created} 件`);
      await load();
    } finally {
      busy = false;
    }
  }
</script>

<main style="font-family: system-ui; padding: 24px; max-width: 960px; margin: 0 auto">
  <h1>社内掃除当番アプリ (SvelteKit)</h1>
  <button on:click={generate} disabled={busy} style="padding: 8px 16px">
    {busy ? "生成中..." : "翌週の当番を生成"}
  </button>

  <h2>社員一覧 ({employees.length})</h2>
  <ul>
    {#each employees as e (e.id)}
      <li>{e.name} <small style="color:#666">({e.department})</small></li>
    {/each}
  </ul>

  <h2>当番一覧 ({duties.length})</h2>
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
      {#each duties as d (d.id)}
        <tr>
          <td class="td">{d.scheduled_date}</td>
          <td class="td">{d.area_name}</td>
          <td class="td">{d.employee_name}</td>
          <td class="td">{d.status}</td>
        </tr>
      {/each}
    </tbody>
  </table>
</main>

<style>
  .th { border: 1px solid #ddd; padding: 8px; background: #f5f5f5; text-align: left; }
  .td { border: 1px solid #ddd; padding: 8px; }
</style>
