import { useEffect, useState } from "react";

type Employee = { id: number; name: string; department: string };
type Duty = {
  id: number;
  employee_name: string;
  area_name: string;
  scheduled_date: string;
  status: string;
};

export default function Home() {
  const [employees, setEmployees] = useState<Employee[]>([]);
  const [duties, setDuties] = useState<Duty[]>([]);
  const [busy, setBusy] = useState(false);

  const load = async () => {
    const [e, d] = await Promise.all([
      fetch("/api/people").then((r) => r.json()),
      fetch("/api/lottery-results").then((r) => r.json()),
    ]);
    setEmployees(e);
    setDuties(d);
  };
  useEffect(() => {
    load().catch(console.error);
  }, []);

  const generate = async () => {
    setBusy(true);
    try {
      const r = await fetch("/api/lottery-results/generate", { method: "POST" });
      const j = await r.json();
      alert(`生成: ${j.created} 件`);
      await load();
    } finally {
      setBusy(false);
    }
  };

  return (
    <main style={{ fontFamily: "system-ui", padding: 24, maxWidth: 960, margin: "0 auto" }}>
      <h1>社内掃除当番アプリ (Next.js)</h1>
      <button onClick={generate} disabled={busy} style={{ padding: "8px 16px" }}>
        {busy ? "生成中..." : "翌週の当番を生成"}
      </button>

      <h2>社員一覧 ({employees.length})</h2>
      <ul>
        {employees.map((e) => (
          <li key={e.id}>{e.name} <small style={{ color: "#666" }}>({e.department})</small></li>
        ))}
      </ul>

      <h2>当番一覧 ({duties.length})</h2>
      <table style={{ borderCollapse: "collapse", width: "100%" }}>
        <thead>
          <tr>
            <th style={th}>日付</th>
            <th style={th}>エリア</th>
            <th style={th}>担当</th>
            <th style={th}>状態</th>
          </tr>
        </thead>
        <tbody>
          {duties.map((d) => (
            <tr key={d.id}>
              <td style={td}>{d.scheduled_date}</td>
              <td style={td}>{d.area_name}</td>
              <td style={td}>{d.employee_name}</td>
              <td style={td}>{d.status}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </main>
  );
}

const th: React.CSSProperties = { border: "1px solid #ddd", padding: 8, background: "#f5f5f5", textAlign: "left" };
const td: React.CSSProperties = { border: "1px solid #ddd", padding: 8 };
