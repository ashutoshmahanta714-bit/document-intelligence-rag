import { useState, useRef, useEffect } from "react";
import Upload from "./components/Upload";
import Chat from "./components/Chat";
import Documents from "./components/Documents";
import "./App.css";

const API_BASE = import.meta.env.VITE_API_URL || "http://localhost:8000";

export default function App() {
  const [documents, setDocuments] = useState([]);
  const [messages, setMessages] = useState([]);
  const [activeTab, setActiveTab] = useState("chat");
  const [isQuerying, setIsQuerying] = useState(false);

  const fetchDocuments = async () => {
    try {
      const res = await fetch(`${API_BASE}/documents`);
      const data = await res.json();
      setDocuments(data.documents || []);
    } catch (e) {
      console.error("Failed to fetch documents", e);
    }
  };

  useEffect(() => {
    fetchDocuments();
  }, []);

  const handleQuery = async (question) => {
    const userMsg = { role: "user", content: question, id: Date.now() };
    setMessages((prev) => [...prev, userMsg]);
    setIsQuerying(true);

    try {
      const res = await fetch(`${API_BASE}/query`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ question, top_k: 5 }),
      });
      const data = await res.json();
      const botMsg = {
        role: "assistant",
        content: data.answer,
        sources: data.sources || [],
        id: Date.now() + 1,
      };
      setMessages((prev) => [...prev, botMsg]);
    } catch (e) {
      setMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          content: "⚠️ Failed to connect to the backend. Make sure the server is running.",
          sources: [],
          id: Date.now() + 1,
        },
      ]);
    } finally {
      setIsQuerying(false);
    }
  };

  return (
    <div className="app">
      <header className="header">
        <div className="header-inner">
          <div className="logo">
            <span className="logo-icon">◈</span>
            <span className="logo-text">DocIntel</span>
            <span className="logo-tag">RAG</span>
          </div>
          <nav className="nav">
            {["chat", "documents"].map((tab) => (
              <button
                key={tab}
                className={`nav-btn ${activeTab === tab ? "active" : ""}`}
                onClick={() => setActiveTab(tab)}
              >
                {tab === "chat" ? "⚡ Chat" : `📁 Docs (${documents.length})`}
              </button>
            ))}
          </nav>
        </div>
      </header>

      <main className="main">
        {activeTab === "chat" ? (
          <div className="chat-layout">
            <div className="sidebar">
              <Upload apiBase={API_BASE} onUploadSuccess={fetchDocuments} />
            </div>
            <div className="chat-area">
              <Chat
                messages={messages}
                onQuery={handleQuery}
                isQuerying={isQuerying}
                docsCount={documents.length}
              />
            </div>
          </div>
        ) : (
          <Documents
            documents={documents}
            apiBase={API_BASE}
            onDelete={fetchDocuments}
          />
        )}
      </main>
    </div>
  );
}
