import { useState, useRef, useEffect } from "react";

export default function Chat({ messages, onQuery, isQuerying, docsCount }) {
  const [input, setInput] = useState("");
  const bottomRef = useRef();

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, isQuerying]);

  const handleSend = () => {
    const q = input.trim();
    if (!q || isQuerying) return;
    setInput("");
    onQuery(q);
  };

  const handleKeyDown = (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const suggestions = [
    "What are the main topics in these documents?",
    "Summarize the key findings",
    "What conclusions are mentioned?",
    "List important dates or numbers",
  ];

  return (
    <>
      <div className="chat-messages">
        {messages.length === 0 ? (
          <div className="chat-empty">
            <div className="chat-empty-icon">◈</div>
            <h3>Document Intelligence</h3>
            <p>
              {docsCount === 0
                ? "Upload documents on the left to start asking questions."
                : `${docsCount} document(s) indexed. Ask anything about them.`}
            </p>
            {docsCount > 0 && (
              <div style={{ marginTop: 16, display: "flex", flexDirection: "column", gap: 8, width: "100%", maxWidth: 380 }}>
                {suggestions.map((s) => (
                  <button
                    key={s}
                    onClick={() => onQuery(s)}
                    style={{
                      background: "var(--surface2)",
                      border: "1px solid var(--border2)",
                      borderRadius: 7,
                      padding: "8px 14px",
                      color: "var(--text2)",
                      fontSize: 12,
                      cursor: "pointer",
                      textAlign: "left",
                      fontFamily: "inherit",
                      transition: "all 0.15s",
                    }}
                    onMouseEnter={e => e.target.style.borderColor = "var(--accent)"}
                    onMouseLeave={e => e.target.style.borderColor = "var(--border2)"}
                  >
                    {s}
                  </button>
                ))}
              </div>
            )}
          </div>
        ) : (
          <>
            {messages.map((msg) => (
              <div key={msg.id} className={`message ${msg.role}`}>
                <div className="msg-avatar">
                  {msg.role === "user" ? "U" : "◈"}
                </div>
                <div className="msg-body">
                  <div className="msg-content">{msg.content}</div>
                  {msg.sources?.length > 0 && (
                    <div className="msg-sources">
                      {msg.sources.slice(0, 4).map((s, i) => (
                        <div key={i} className="source-chip" title={s.excerpt}>
                          📄 {s.source.length > 20 ? s.source.slice(0, 18) + "…" : s.source}
                          <span className="score">
                            {Math.round(s.relevance_score * 100)}%
                          </span>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              </div>
            ))}

            {isQuerying && (
              <div className="message assistant">
                <div className="msg-avatar">◈</div>
                <div className="msg-body">
                  <div className="msg-content">
                    <div className="typing">
                      <span /><span /><span />
                    </div>
                  </div>
                </div>
              </div>
            )}
            <div ref={bottomRef} />
          </>
        )}
      </div>

      <div className="chat-input-bar">
        <textarea
          className="chat-input"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="Ask a question about your documents..."
          rows={1}
          disabled={isQuerying}
        />
        <button
          className="send-btn"
          onClick={handleSend}
          disabled={!input.trim() || isQuerying}
        >
          ➤
        </button>
      </div>
    </>
  );
}
