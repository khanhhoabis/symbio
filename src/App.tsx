import { useState, useEffect, useRef } from "react";
import { invoke } from "@tauri-apps/api/core";
import "./App.css";

interface NoteFile {
  path: string;
  name: string;
}

interface ActiveFile {
  path: string;
  content: string;
}

interface ChatMessage {
  sender: "user" | "hermes";
  text: string;
  thought?: string;
  context_notes?: Array<{ id: string; path: string; content: string }>;
}

export default function App() {
  const [port, setPort] = useState<number | null>(null);
  const [files, setFiles] = useState<NoteFile[]>([]);
  const [activeFile, setActiveFile] = useState<ActiveFile | null>(null);
  const [chatHistory, setChatHistory] = useState<ChatMessage[]>([
    {
      sender: "hermes",
      text: "Chào bạn! Tôi là Hermes, cộng sự trí tuệ nhân tạo của bạn. Tôi đã kết nối thành công với kho tri thức cục bộ. Hãy đặt câu hỏi hoặc bắt đầu viết ghi chú!",
    },
  ]);
  const [inputMessage, setInputMessage] = useState("");
  const [isGenerating, setIsGenerating] = useState(false);
  const [saveStatus, setSaveStatus] = useState<"synced" | "saving" | "unsaved">("synced");
  const [expandedThoughtIndex, setExpandedThoughtIndex] = useState<number | null>(null);
  const [searchQuery, setSearchQuery] = useState("");
  const [folderExpanded, setFolderExpanded] = useState<Record<string, boolean>>({});
  const [renamingPath, setRenamingPath] = useState<string | null>(null);
  const [showFormatPanel, setShowFormatPanel] = useState(false);
  const [formatPrompt, setFormatPrompt] = useState("");
  const saveTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const chatEndRef = useRef<HTMLDivElement | null>(null);

  // 1. Fetch Dynamic Port from Rust on Startup
  useEffect(() => {
    async function initPort() {
      try {
        const tauriPort = await invoke<number>("get_server_port");
        setPort(tauriPort);
        loggerInfo(`Server connected on port: ${tauriPort}`);
      } catch (err) {
        console.error("Failed to retrieve server port from Tauri:", err);
      }
    }
    initPort();
  }, []);

  // Helper logger
  function loggerInfo(msg: string) {
    console.log(`[SymbioUI] ${msg}`);
  }

  // 2. Fetch File List once port is active
  useEffect(() => {
    if (port !== null) {
      loadFileList();
    }
  }, [port]);

  // Scroll to bottom of chat
  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [chatHistory]);

  async function loadFileList() {
    if (port === null) return;
    try {
      const res = await fetch(`http://127.0.0.1:${port}/api/files`);
      const data = await res.json();
      setFiles(data.files || []);
    } catch (err) {
      console.error("Failed to load file list:", err);
    }
  }
  // Utility: group files by folder
  function groupFilesByFolder(files: NoteFile[]): Array<[string, NoteFile[]]> {
    const groups: Record<string, NoteFile[]> = {};
    files.forEach((f) => {
      const parts = f.path.split("/");
      const folder = parts.length > 1 ? parts[0] : "root";
      if (!groups[folder]) groups[folder] = [];
      groups[folder].push(f);
    });
    return Object.entries(groups);
  }

  const groupedFiles = groupFilesByFolder(files);

  function toggleFolder(folder: string) {
    setFolderExpanded((prev) => ({
      ...prev,
      [folder]: !prev[folder],
    }));
  }

  async function handleRename(oldPath: string, newName: string) {
    if (!newName.trim()) {
      setRenamingPath(null);
      return;
    }
    const newPath = (() => {
      const parts = oldPath.split("/");
      const filename = newName.endsWith(".md") ? newName : `${newName}.md`;
      if (parts.length > 1) {
        return `${parts.slice(0, -1).join("/")}/${filename}`;
      }
      return filename;
    })();
    if (port === null) return;
    try {
      const res = await fetch(`http://127.0.0.1:${port}/api/rename`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ old_path: oldPath, new_path: newPath }),
      });
      if (res.ok) {
        await loadFileList();
        if (activeFile?.path === oldPath) {
          setActiveFile({ ...activeFile, path: newPath, name: filename });
        }
      } else {
        console.error("Rename failed");
      }
    } catch (err) {
      console.error(err);
    } finally {
      setRenamingPath(null);
    }
  }

  function openFormatPanel() {
    setShowFormatPanel(true);
  }

  async function applyFormat() {
    if (!activeFile) return;
    if (port === null) return;
    try {
      const res = await fetch(`http://127.0.0.1:${port}/api/format`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ content: activeFile.content, prompt: formatPrompt }),
      });
      if (res.ok) {
        const data = await res.json();
        const formatted = data.formatted_content || data.content || activeFile.content;
        setActiveFile((prev) => (prev ? { ...prev, content: formatted } : prev));
      }
    } catch (err) {
      console.error(err);
    } finally {
      setShowFormatPanel(false);
      setFormatPrompt("");
    }
  }
  // 3. Load File Content
  async function selectFile(file: NoteFile) {
    if (port === null) return;
    
    // Save current active file first if unsaved
    if (saveStatus === "unsaved" && activeFile) {
      await saveFileContent(activeFile.path, activeFile.content);
    }

    try {
      const res = await fetch(`http://127.0.0.1:${port}/api/file?path=${encodeURIComponent(file.path)}`);
      if (res.ok) {
        const data = await res.json();
        setActiveFile({
          path: data.path,
          content: data.content,
        });
        setSaveStatus("synced");
      }
    } catch (err) {
      console.error("Failed to read file:", err);
    }
  }

  // 4. Save File Content (Auto-save API)
  async function saveFileContent(filePath: string, content: string) {
    if (port === null) return;
    setSaveStatus("saving");
    try {
      const res = await fetch(`http://127.0.0.1:${port}/api/file`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ path: filePath, content }),
      });
      if (res.ok) {
        setSaveStatus("synced");
      } else {
        setSaveStatus("unsaved");
      }
    } catch (err) {
      console.error("Failed to save file:", err);
      setSaveStatus("unsaved");
    }
  }

  // 5. Handle Text Area Input with Debounced Save (1.5s)
  function handleEditorChange(val: string) {
    if (!activeFile) return;

    setActiveFile({
      ...activeFile,
      content: val,
    });
    setSaveStatus("unsaved");

    // Clear previous timeout
    if (saveTimeoutRef.current) {
      clearTimeout(saveTimeoutRef.current);
    }

    // Set new timeout for debounced auto-save
    saveTimeoutRef.current = setTimeout(() => {
      saveFileContent(activeFile.path, val);
    }, 1500);
  }

  // 6. Create New Markdown Note
  async function createNewNote() {
    if (port === null) return;
    const dateStr = new Date().toISOString().slice(0, 10);
    const timestamp = Date.now().toString().slice(-4);
    const newFileName = `Inbox/Ghi_chu_${dateStr}_${timestamp}.md`;
    
    const initialContent = `# Ghi chú mới ngày ${dateStr}\n\nNhập nội dung ghi chú ở đây...`;

    // Save and open
    await saveFileContent(newFileName, initialContent);
    await loadFileList();
    selectFile({ path: newFileName, name: newFileName.split("/").pop() || "" });
  }

  // 7. Send message to AI Companion (Hermes API)
  async function sendMessage() {
    if (port === null || !inputMessage.trim() || isGenerating) return;

    const userMsg = inputMessage.trim();
    setInputMessage("");
    setChatHistory((prev) => [...prev, { sender: "user", text: userMsg }]);
    setIsGenerating(true);

    try {
      const res = await fetch(`http://127.0.0.1:${port}/api/chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message: userMsg }),
      });

      if (res.ok) {
        const data = await res.json();
        setChatHistory((prev) => [
          ...prev,
          {
            sender: "hermes",
            text: data.response,
            thought: data.thought,
            context_notes: data.context_notes,
          },
        ]);
      } else {
        setChatHistory((prev) => [
          ...prev,
          { sender: "hermes", text: "❌ Lỗi: Máy chủ AI không thể xử lý yêu cầu." },
        ]);
      }
    } catch (err) {
      console.error("Chat error:", err);
      setChatHistory((prev) => [
        ...prev,
        { sender: "hermes", text: "❌ Lỗi kết nối: Không thể gửi tin nhắn tới Hermes." },
      ]);
    } finally {
      setIsGenerating(false);
    }
  }
  const wordCount = activeFile ? activeFile.content.trim().split(/\s+/).filter(Boolean).length : 0;
  return (
    <div className="symbio-container">
      {/* COLUMN 1: FILE NAVIGATOR */}
      <aside className="sidebar-nav">
          <div className="sidebar-header">
            <h2>🧠 SYMBIO</h2>
            <button className="new-note-btn" onClick={createNewNote}>
              + Note mới
            </button>
          </div>
          {/* Search Bar */}
          <input
            type="text"
            className="file-search"
            placeholder="🔍 Tìm ghi chú..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
          />
          <div className="file-list">
            {groupedFiles.map(([folder, folderFiles]) => (
              <div key={folder} className="folder-group">
                <div className="folder-title" onClick={() => toggleFolder(folder)}>
                  {folderExpanded[folder] ? "▼" : "▶"} {folder}
                </div>
                {folderExpanded[folder] &&
                  folderFiles
                    .filter((f) => f.name.toLowerCase().includes(searchQuery.toLowerCase()))
                    .map((file) => (
                      <div
                        key={file.path}
                        className={`file-item ${activeFile?.path === file.path ? "active" : ""}`}
                        onClick={() => selectFile(file)}
                      >
                        <span className="file-icon">📄</span>
                        {/* Inline rename */}
                        {renamingPath === file.path ? (
                          <input
                            className="rename-input"
                            defaultValue={file.name.replace(/\.md$/i, "")}
                            onBlur={(e) => handleRename(file.path, e.target.value)}
                            onKeyDown={(e) => {
                              if (e.key === "Enter") {
                                handleRename(file.path, e.currentTarget.value);
                              } else if (e.key === "Escape") {
                                setRenamingPath(null);
                              }
                            }}
                            autoFocus
                          />
                        ) : (
                          <span
                            className="file-name"
                            onDoubleClick={() => setRenamingPath(file.path)}
                          >
                            {file.name}
                          </span>
                        )}
                      </div>
                    ))}
              </div>
            ))}
            {files.length === 0 && (
              <div className="empty-files-placeholder">Chưa có ghi chú nào. Hãy tạo note mới!</div>
            )}
          </div>
        </aside>

      {/* COLUMN 2: MARKDOWN EDITOR */}
      <main className="editor-area">
          {activeFile ? (
            <div className="editor-container">
              <header className="editor-header">
                <div className="editor-title">
                  <span className="editor-file-icon">📂</span>
                  <span className="editor-file-path">{activeFile.path}</span>
                </div>
                <div className="editor-sync-indicator">
                  {saveStatus === "synced" && <span className="status-synced">● Đã lưu</span>}
                  {saveStatus === "saving" && <span className="status-saving">◌ Đang lưu...</span>}
                  {saveStatus === "unsaved" && <span className="status-unsaved">○ Chưa lưu</span>}
                </div>
                {/* AI Format Button */}
                <button className="format-btn" onClick={openFormatPanel}>✨ Format</button>
              </header>
              <textarea
                className="markdown-textarea"
                value={activeFile.content}
                onChange={(e) => handleEditorChange(e.target.value)}
                placeholder="Bắt đầu ghi lại tri thức của bạn..."
              />
            </div>
          ) : (
            <div className="editor-placeholder">
              <div className="placeholder-content">
                <span className="large-logo">🧠</span>
                <h3>Chào mừng bạn đến với Symbio</h3>
                <p>Chọn một ghi chú ở cột bên trái hoặc bấm nút tạo ghi chú mới để bắt đầu.</p>
              </div>
            </div>
          )}
          {/* Format Panel */}
          {showFormatPanel && (
            <div className="format-panel">
              <textarea
                className="format-prompt"
                placeholder="Nhập prompt định dạng (VD: 'Viết lại ngắn gọn')"
                value={formatPrompt}
                onChange={(e) => setFormatPrompt(e.target.value)}
              />
              <div className="quick-prompts">
                <button onClick={() => setFormatPrompt('Cấu trúc lại với heading')}>📐 Cấu trúc</button>
                <button onClick={() => setFormatPrompt('Súc tích hơn')}>✏️ Súc tích</button>
                <button onClick={() => setFormatPrompt('Mở rộng nội dung')}>🌟 Mở rộng</button>
              </div>
              <button className="apply-format" onClick={applyFormat}>Áp dụng</button>
              <button className="close-format" onClick={() => setShowFormatPanel(false)}>✖ Đóng</button>
            </div>
          )}
        </main>

      {/* COLUMN 3: AI SIDEBAR COMPANION */}
      <aside className="sidebar-chat">
        <div className="chat-header">
          <h3>⚡ HERMES COMPANION</h3>
          <span className="agent-status-tag">Local Active</span>
        </div>

        <div className="chat-messages">
          {chatHistory.map((msg, idx) => (
            <div key={idx} className={`chat-bubble-container ${msg.sender}`}>
              <div className="chat-avatar">
                {msg.sender === "hermes" ? "🤖" : "👤"}
              </div>
              <div className="chat-bubble-content">
                {/* 1. Collapsible Thought Box */}
                {msg.thought && (
                  <div className="thought-wrapper">
                    <button
                      className="thought-toggle"
                      onClick={() =>
                        setExpandedThoughtIndex(expandedThoughtIndex === idx ? null : idx)
                      }
                    >
                      {expandedThoughtIndex === idx ? "▼ Ẩn suy nghĩ ngầm" : "▶ Xem tiến trình suy nghĩ của Hermes"}
                    </button>
                    {expandedThoughtIndex === idx && (
                      <pre className="thought-box">{msg.thought}</pre>
                    )}
                  </div>
                )}

                {/* 2. Text Content */}
                <div className="chat-text">{msg.text}</div>

                {/* 3. Retrieve Context Notes References */}
                {msg.context_notes && msg.context_notes.length > 0 && (
                  <div className="references-wrapper">
                    <span className="references-title">🔍 Ghi chú liên quan tìm thấy:</span>
                    <div className="references-list">
                      {msg.context_notes.map((note) => (
                        <div key={note.id} className="reference-item">
                          🔗 {note.path}
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            </div>
          ))}
          <div ref={chatEndRef} />
        </div>

        <div className="chat-input-area">
          <textarea
            className="chat-input-textarea"
            rows={2}
            value={inputMessage}
            onChange={(e) => setInputMessage(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === "Enter" && !e.shiftKey) {
                e.preventDefault();
                sendMessage();
              }
            }}
            placeholder="Hỏi Hermes về các ghi chú của bạn..."
            disabled={isGenerating}
          />
          <button
            className="chat-send-btn"
            onClick={sendMessage}
            disabled={!inputMessage.trim() || isGenerating}
          >
            {isGenerating ? "..." : "Gửi"}
          </button>
        </div>
      </aside>
    </div>
  );
}
