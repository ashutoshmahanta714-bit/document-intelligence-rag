import { useState } from "react";

export default function Documents({ documents, apiBase, onDelete }) {
  const [deleting, setDeleting] = useState(null);

  const handleDelete = async (docName) => {
    setDeleting(docName);
    try {
      await fetch(`${apiBase}/documents/${encodeURIComponent(docName)}`, {
        method: "DELETE",
      });
      onDelete();
    } catch (e) {
      console.error("Delete failed", e);
    } finally {
      setDeleting(null);
    }
  };

  const getFileIcon = (name) => {
    const ext = name?.split(".").pop()?.toLowerCase();
    const icons = { pdf: "📕", docx: "📘", txt: "📄", csv: "📊", md: "📝" };
    return icons[ext] || "📄";
  };

  return (
    <div>
      <div className="page-title">
        📁 Indexed Documents
        <span className="badge">{documents.length} files</span>
      </div>

      <div className="docs-grid">
        {documents.length === 0 ? (
          <div className="docs-empty">
            No documents indexed yet. Upload files from the Chat tab.
          </div>
        ) : (
          documents.map((doc) => (
            <div key={doc.name} className="doc-card">
              <div className="doc-icon">{getFileIcon(doc.name)}</div>
              <div className="doc-name">{doc.name}</div>
              <div className="doc-chunks">⬡ {doc.chunks} chunks indexed</div>
              <button
                className="doc-delete"
                onClick={() => handleDelete(doc.name)}
                disabled={deleting === doc.name}
              >
                {deleting === doc.name ? "Deleting..." : "🗑 Remove from index"}
              </button>
            </div>
          ))
        )}
      </div>
    </div>
  );
}
