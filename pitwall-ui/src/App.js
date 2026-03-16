import { useState, useEffect } from "react";
import axios from "axios";

const API = "http://127.0.0.1:8000";

export default function App() {
  const [question, setQuestion] = useState("");
  const [messages, setMessages] = useState([
    { role: "ai", text: "Welcome to PitWall AI 🏎️ Ask me anything about F1 drivers from 2000 to 2023!" }
  ]);
  const [loading, setLoading] = useState(false);
  const [drivers, setDrivers] = useState([]);
  const [selectedDriver, setSelectedDriver] = useState(null);
  const [driverStats, setDriverStats] = useState(null);
  const [leaderboard, setLeaderboard] = useState([]);
  const [activeTab, setActiveTab] = useState("chat");

  useEffect(() => {
    axios.get(`${API}/drivers`).then(r => setDrivers(r.data.drivers));
    axios.get(`${API}/leaderboard`).then(r => setLeaderboard(r.data.leaderboard));
  }, []);

  const handleDriverSelect = async (driver) => {
    setSelectedDriver(driver);
    const r = await axios.get(`${API}/stats/${encodeURIComponent(driver)}`);
    setDriverStats(r.data);
    setActiveTab("stats");
  };

  const handleAsk = async () => {
    if (!question.trim()) return;
    const q = question;
    setQuestion("");
    setMessages(m => [...m, { role: "user", text: q }]);
    setLoading(true);
    try {
      const r = await axios.post(`${API}/chat`, { question: q });
      setMessages(m => [...m, { role: "ai", text: r.data.answer, sources: r.data.sources }]);
    } catch {
      setMessages(m => [...m, { role: "ai", text: "Sorry, something went wrong. Is the API running?" }]);
    }
    setLoading(false);
  };

  return (
    <div style={{ fontFamily: "Inter, sans-serif", background: "#0a0a0a", minHeight: "100vh", color: "#fff" }}>
      {/* Header */}
      <div style={{ background: "#e10600", padding: "16px 32px", display: "flex", alignItems: "center", gap: 16 }}>
        <span style={{ fontSize: 28 }}>🏎️</span>
        <div>
          <h1 style={{ margin: 0, fontSize: 22, fontWeight: 800, letterSpacing: 1 }}>PITWALL AI</h1>
          <p style={{ margin: 0, fontSize: 12, opacity: 0.8 }}>F1 Driver Performance Intelligence · 2000–2023</p>
        </div>
        <div style={{ marginLeft: "auto", display: "flex", gap: 8 }}>
          {["chat", "stats", "leaderboard"].map(tab => (
            <button key={tab} onClick={() => setActiveTab(tab)} style={{
              padding: "8px 16px", border: "none", borderRadius: 6, cursor: "pointer", fontWeight: 600,
              background: activeTab === tab ? "#fff" : "rgba(255,255,255,0.2)",
              color: activeTab === tab ? "#e10600" : "#fff", textTransform: "capitalize"
            }}>{tab}</button>
          ))}
        </div>
      </div>

      <div style={{ display: "flex", height: "calc(100vh - 70px)" }}>
        {/* Sidebar */}
        <div style={{ width: 220, background: "#111", borderRight: "1px solid #222", overflowY: "auto", padding: 16 }}>
          <p style={{ color: "#888", fontSize: 11, textTransform: "uppercase", letterSpacing: 1, marginBottom: 8 }}>Drivers</p>
          {drivers.map(d => (
            <div key={d} onClick={() => handleDriverSelect(d)} style={{
              padding: "8px 10px", borderRadius: 6, cursor: "pointer", fontSize: 13,
              background: selectedDriver === d ? "#e10600" : "transparent",
              color: selectedDriver === d ? "#fff" : "#ccc", marginBottom: 2
            }}>{d}</div>
          ))}
        </div>

        {/* Main content */}
        <div style={{ flex: 1, display: "flex", flexDirection: "column", overflow: "hidden" }}>

          {/* CHAT TAB */}
          {activeTab === "chat" && (
            <>
              <div style={{ flex: 1, overflowY: "auto", padding: 24, display: "flex", flexDirection: "column", gap: 16 }}>
                {messages.map((m, i) => (
                  <div key={i} style={{ display: "flex", justifyContent: m.role === "user" ? "flex-end" : "flex-start" }}>
                    <div style={{
                      maxWidth: "70%", padding: "12px 16px", borderRadius: 12, fontSize: 14, lineHeight: 1.6,
                      background: m.role === "user" ? "#e10600" : "#1a1a1a",
                      color: "#fff", borderBottomRightRadius: m.role === "user" ? 0 : 12,
                      borderBottomLeftRadius: m.role === "ai" ? 0 : 12,
                    }}>
                      {m.text}
                      {m.sources && (
                        <div style={{ marginTop: 8, paddingTop: 8, borderTop: "1px solid #333" }}>
                          <p style={{ color: "#888", fontSize: 11, margin: "0 0 4px" }}>SOURCES</p>
                          {m.sources.slice(0, 2).map((s, j) => (
                            <p key={j} style={{ color: "#666", fontSize: 11, margin: "2px 0" }}>· {s.slice(0, 80)}...</p>
                          ))}
                        </div>
                      )}
                    </div>
                  </div>
                ))}
                {loading && (
                  <div style={{ display: "flex", justifyContent: "flex-start" }}>
                    <div style={{ background: "#1a1a1a", padding: "12px 16px", borderRadius: 12, color: "#888", fontSize: 14 }}>
                      Analysing race data... ⏱️
                    </div>
                  </div>
                )}
              </div>
              <div style={{ padding: 16, borderTop: "1px solid #222", display: "flex", gap: 8 }}>
                <input
                  value={question}
                  onChange={e => setQuestion(e.target.value)}
                  onKeyDown={e => e.key === "Enter" && handleAsk()}
                  placeholder="Ask anything... e.g. How does Verstappen perform in wet conditions?"
                  style={{
                    flex: 1, padding: "12px 16px", borderRadius: 8, border: "1px solid #333",
                    background: "#1a1a1a", color: "#fff", fontSize: 14, outline: "none"
                  }}
                />
                <button onClick={handleAsk} disabled={loading} style={{
                  padding: "12px 24px", background: "#e10600", color: "#fff", border: "none",
                  borderRadius: 8, fontWeight: 700, cursor: "pointer", fontSize: 14
                }}>ASK</button>
              </div>
            </>
          )}

          {/* STATS TAB */}
          {activeTab === "stats" && driverStats && (
            <div style={{ padding: 32, overflowY: "auto" }}>
              <h2 style={{ fontSize: 28, margin: "0 0 4px" }}>{driverStats.driver}</h2>
              <p style={{ color: "#888", margin: "0 0 24px" }}>{driverStats.years_active} · {driverStats.teams?.join(", ")}</p>
              <div style={{ display: "grid", gridTemplateColumns: "repeat(4, 1fr)", gap: 16, marginBottom: 32 }}>
                {[
                  { label: "Races", value: driverStats.total_races },
                  { label: "Wins", value: driverStats.wins },
                  { label: "Podiums", value: driverStats.podiums },
                  { label: "Win Rate", value: `${driverStats.win_rate}%` },
                  { label: "Avg Finish", value: driverStats.avg_finish },
                  { label: "Wet Races", value: driverStats.wet_races },
                  { label: "Avg Wet Finish", value: driverStats.avg_wet_finish ?? "N/A" },
                  { label: "Avg Street Finish", value: driverStats.avg_street_finish ?? "N/A" },
                ].map(s => (
                  <div key={s.label} style={{ background: "#1a1a1a", borderRadius: 12, padding: 20, textAlign: "center" }}>
                    <p style={{ color: "#888", fontSize: 12, margin: "0 0 8px", textTransform: "uppercase", letterSpacing: 1 }}>{s.label}</p>
                    <p style={{ color: "#e10600", fontSize: 28, fontWeight: 800, margin: 0 }}>{s.value}</p>
                  </div>
                ))}
              </div>
              <button onClick={() => {
                setActiveTab("chat");
                setQuestion(`Tell me about ${driverStats.driver}'s career performance`);
              }} style={{
                padding: "12px 24px", background: "#e10600", color: "#fff",
                border: "none", borderRadius: 8, fontWeight: 700, cursor: "pointer"
              }}>Ask AI about this driver →</button>
            </div>
          )}

          {/* LEADERBOARD TAB */}
          {activeTab === "leaderboard" && (
            <div style={{ padding: 32, overflowY: "auto" }}>
              <h2 style={{ margin: "0 0 24px" }}>🏆 All-Time Win Leaders (2000–2023)</h2>
              <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
                {leaderboard.map((d, i) => (
                  <div key={d.driver} onClick={() => handleDriverSelect(d.driver)} style={{
                    display: "flex", alignItems: "center", gap: 16, padding: "16px 20px",
                    background: "#1a1a1a", borderRadius: 10, cursor: "pointer",
                    borderLeft: i < 3 ? "4px solid #e10600" : "4px solid #333"
                  }}>
                    <span style={{ fontSize: 20, width: 32, textAlign: "center", fontWeight: 800, color: "#888" }}>
                      {i === 0 ? "🥇" : i === 1 ? "🥈" : i === 2 ? "🥉" : `#${i + 1}`}
                    </span>
                    <span style={{ flex: 1, fontWeight: 600 }}>{d.driver}</span>
                    <span style={{ color: "#e10600", fontWeight: 800, fontSize: 18 }}>{d.wins} wins</span>
                    <span style={{ color: "#888", fontSize: 13 }}>{d.win_rate}% win rate</span>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* STATS TAB - no driver selected */}
          {activeTab === "stats" && !driverStats && (
            <div style={{ flex: 1, display: "flex", alignItems: "center", justifyContent: "center", color: "#888" }}>
              <p>Select a driver from the sidebar to see their stats</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}