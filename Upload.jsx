import { useState, useRef } from "react";

export default function Upload({ apiBase, onUploadSuccess }) {
  const [file, setFile] = useState(null);
  const [status, setStatus] = useState(null);
  const [dragging, setDragging] = useState(false);
  const inputRef = useRef();

  const handleFile = (f) => {
    if (f) setFile(f);
  };

  const handleUpload = async () => {
    if (!file) return;
    setStatus({ type: "loading", msg: "Uploading & indexing..." });

    const formData = new FormData();
    formData.append("file", file);

    try {
      const res = await fetch(`${apiBase}/upload`, {
        method: "POST",
        body: formData,
      });
      const data = await res.json();
      if (res.ok) {
        setStatus({ type: "success", msg: `✓ ${data.chunks_indexed} chunks indexed` });
        setFile(null);
        onUploadSuccess();
        setTimeout(() => setStatus(null), 3000);
      } else {
        setStatus({ type: "error", msg: data.detail || "Upload failed" });
      }
    } catch (e) {
      setStatus({ type: "error", msg: "Cannot reach backend server" });
    }
  };

  const getFileIcon = (name) => {
    const ext = name?.split(".").pop()?.toLowerCase();
    const icons = { pdf: "📕", docx: "📘", txt: "📄", csv: "📊", md: "📝" };
    return icons[ext] || "📄";
  };

  return (
    <div className="card">
      <div className="card-title">⬆ Upload Document</div>

      <div
        className={`upload-zone ${dragging ? "dragging" : ""}`}
        onDragOver={(e) => { e.preventDefault(); setDragging(true); }}
        onDragLeave={() => setDragging(false)}
        onDrop={(e) => { e.preventDefault(); setDragging(false); handleFile(e.dataTransfer.files[0]); }}
      >
        <input
          ref={inputRef}
          type="file"
          accept=".pdf,.txt,.docx,.csv,.md"
          onChange={(e) => handleFile(e.target.files[0])}
        />
        <div className="upload-icon">📂</div>
        <div className="upload-hint">
          Drop file here or <span>browse</span>
          <br />PDF, TXT, DOCX, CSV, MD
        </div>
      </div>

      {file && (
        <div className="selected-file">
          {getFileIcon(file.name)} {file.name}
        </div>
      )}

      <button
        className="upload-btn"
        onClick={handleUpload}
        disabled={!file || status?.type === "loading"}
      >
        {status?.type === "loading" ? "Indexing..." : "Index Document"}
      </button>

      {status && (
        <div className={`upload-status ${status.type}`}>
          {status.msg}
        </div>
      )}
    </div>
  );
}
