import { useState, useEffect } from "react";
import axios from "axios";
import ReactMarkdown from "react-markdown";
import "./App.css";

const API = "http://127.0.0.1:8000/api/v1";

export default function App() {
  const [query, setQuery] = useState("");
  const [answer, setAnswer] = useState("");
  const [asked, setAsked] = useState(false);
  const [asking, setAsking] = useState(false);

  const [file, setFile] = useState(null);
  const [uploading, setUploading] = useState(false);
  const [uploadNote, setUploadNote] = useState(null); // { ok, text }

  const [documents, setDocuments] = useState([]);

  const loadDocuments = async () => {
    try {
      const res = await axios.get(`${API}/documents`);
      setDocuments(res.data.documents || []);
    } catch (err) {
      console.error("Error loading documents:", err);
    }
  };

  useEffect(() => {
    loadDocuments();
  }, []);

  const handleAsk = async () => {
    if (!query.trim() || asking) return;
    setAsking(true);
    setAsked(true);
    try {
      const res = await axios.post(`${API}/ask`, null, {
        params: { question: query },
      });
      setAnswer(res.data.answer);
    } catch (err) {
      console.error("Error asking question:", err);
      setAnswer("Couldn't reach the server. Make sure the backend is running on port 8000.");
    } finally {
      setAsking(false);
    }
  };

  const handleUpload = async () => {
    if (!file || uploading) return;
    setUploading(true);
    setUploadNote(null);
    const formData = new FormData();
    formData.append("file", file);
    try {
      const res = await axios.post(`${API}/upload`, formData, {
        headers: { "Content-Type": "multipart/form-data" },
      });
      setUploadNote({ ok: true, text: res.data.message || "Added to your library." });
      setFile(null);
      loadDocuments();
    } catch (err) {
      console.error("Error uploading file:", err);
      setUploadNote({ ok: false, text: "Upload failed. Check the file type and that the server is running." });
    } finally {
      setUploading(false);
    }
  };

  const onKeyDown = (e) => {
    if ((e.metaKey || e.ctrlKey) && e.key === "Enter") handleAsk();
  };

  return (
    <div className="mg-page">
      <div className="mg-shell">
        <header className="mg-head">
          <span className="mg-eyebrow">Document Q&amp;A</span>
          <h1 className="mg-title">Ask your documents anything.</h1>
          <p className="mg-lede">
            Add a file to your library, then ask a question. Every answer is drawn
            from the passages it actually found — shown below as sources.
          </p>
        </header>

        {/* Library / upload */}
        <section className="mg-block">
          <div className="mg-label">01 &middot; Library</div>
          <div className="mg-drop">
            <label className="mg-file">
              <input
                type="file"
                onChange={(e) => {
                  setFile(e.target.files[0] || null);
                  setUploadNote(null);
                }}
                accept=".pdf,.docx,.txt"
              />
              <span className="mg-file-btn">Choose file</span>
              <span className="mg-file-name">
                {file ? file.name : "PDF, DOCX or TXT"}
              </span>
            </label>
            <button
              className="mg-btn mg-btn-ghost"
              onClick={handleUpload}
              disabled={!file || uploading}
            >
              {uploading ? "Adding…" : "Add to library"}
            </button>
          </div>
          {uploadNote && (
            <p className={"mg-note " + (uploadNote.ok ? "is-ok" : "is-err")}>
              {uploadNote.text}
            </p>
          )}

          <div className="mg-lib">
            <div className="mg-lib-head">
              <span>In your library</span>
              <span className="mg-count">{documents.length}</span>
            </div>
            {documents.length === 0 ? (
              <p className="mg-lib-empty">Nothing stored yet. Add a file to get started.</p>
            ) : (
              <ul className="mg-lib-list">
                {documents.map((doc, i) => (
                  <li key={i} className="mg-doc">
                    <span className="mg-doc-name">{doc.file_name}</span>
                    <span className="mg-doc-meta">{doc.chunks} chunks</span>
                  </li>
                ))}
              </ul>
            )}
          </div>
        </section>

        {/* Question */}
        <section className="mg-block">
          <div className="mg-label">02 &middot; Question</div>
          <textarea
            className="mg-input"
            rows="3"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            onKeyDown={onKeyDown}
            placeholder="What would you like to know?"
          />
          <div className="mg-ask-row">
            <span className="mg-hint">⌘ / Ctrl + Enter</span>
            <button
              className="mg-btn mg-btn-solid"
              onClick={handleAsk}
              disabled={!query.trim() || asking}
            >
              {asking ? "Searching…" : "Ask"}
            </button>
          </div>
        </section>

        {/* Answer + sources */}
        <section className="mg-block mg-results">
          {!asked && (
            <div className="mg-empty">
              Your answer will appear here.
            </div>
          )}

          {asked && (
            <div className="mg-fade">
              <div className="mg-label">Finding</div>
              <div className="mg-finding">
                {asking ? (
                  <div className="mg-skel">
                    <span></span><span></span><span></span>
                  </div>
                ) : (
                  <div className="mg-md">
                    <ReactMarkdown>{answer}</ReactMarkdown>
                  </div>
                )}
              </div>
            </div>
          )}
        </section>

        <footer className="mg-foot">Marginalia · answers grounded in your files</footer>
      </div>
    </div>
  );
}