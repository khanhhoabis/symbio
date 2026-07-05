# 🚀 Hướng Dẫn Bắt Đầu Dự Án: Symbio

Chào mừng bạn đến với hành trình xây dựng **Symbio**! Vì bạn phát triển dự án này một mình (Solopreneur/Single Developer), mục tiêu hàng đầu là **tối giản hóa công nghệ, tập trung luồng dữ liệu lõi trước, và tận dụng tối đa AI để viết mã nguồn**.

Dưới đây là cẩm nang từng bước để bạn bắt đầu dự án từ con số 0.

---

## 🛠️ Lựa Chọn Stack Công Nghệ Khuyến Nghị

Để đảm bảo hiệu năng cao, nhẹ máy (local-first) và dễ phát triển bởi 1 người, hãy chọn stack sau:

| Tầng hệ thống | Công nghệ đề xuất | Lý do chọn |
| :--- | :--- | :--- |
| **Hạt nhân AI (Agent)** | **Python 3.11+** hoặc **Node.js (TypeScript)** | Python có hệ sinh thái AI rất mạnh (LangChain, LlamaIndex), dễ tích hợp nhanh với API Gemini hoặc Ollama. |
| **Cơ sở dữ liệu Vector** | **LanceDB** hoặc **ChromaDB (Local)** | LanceDB lưu trữ trực tiếp dưới dạng tệp tin phẳng (serverless), cực kỳ nhanh, thích hợp cho local-first. |
| **Giao diện Desktop (Phase 2)** | **Tauri (Rust) + React/Vite (TS)** | Tauri tạo ra các bản build siêu nhẹ (~10MB-15MB) so với Electron (~100MB+), tận dụng tối đa RAM. |
| **Giao diện Mobile (Phase 3)** | **React Native (Expo)** | Dễ dàng tương tác với hệ thống tệp của iOS/Android thông qua DocumentPicker hoặc FileSystem để đọc file Markdown đồng bộ đám mây. |

---

## 📅 Lộ Trình Triển Khai Chi Tiết (Từng Bước Một)

### Bước 1: Khởi Tạo Môi Trường Cục Bộ
Trước tiên, hãy tạo cấu trúc các thư mục chính trong dự án để định hình không gian làm việc.

1. Mở terminal tại thư mục dự án và tạo các thư mục:
   ```bash
   mkdir -p vault/Inbox vault/.system/skills agent docs src
   ```
2. Khởi tạo một ghi chú Markdown mẫu đầu tiên trong `vault/Inbox/hello.md` để làm dữ liệu kiểm thử.

---

### Bước 2: Xây Dựng Hạt Nhân CLI (`agent/`)
Thay vì dựng giao diện ngay, hãy làm CLI trước để kiểm tra xem AI có thể đọc ghi chú và tự tạo ra kỹ năng không.

1. **Khởi tạo môi trường Python** trong thư mục `agent/`:
   * **Cách 1: Sử dụng `uv` (Khuyên dùng - Nhanh và hiện đại)**
     ```bash
     cd agent
     uv venv
     source .venv/bin/activate
     uv pip install -r requirements.txt
     ```
   * **Cách 2: Sử dụng `venv` tiêu chuẩn**
     ```bash
     cd agent
     python3 -m venv venv
     source venv/bin/activate
     pip install -r requirements.txt
     ```
2. **Cấu hình biến môi trường:** Tạo file `.env` chứa API Key (ví dụ: `GEMINI_API_KEY` sử dụng endpoint tương thích OpenAI của Google AI Studio).
3. **Viết Script CLI đầu tiên (`agent/main.py`):**
   - Đọc toàn bộ file `.md` trong thư mục `vault/`.
   - Sử dụng một mô hình LLM để phân tích ghi chú, tự động phân loại thẻ (Auto-tagging).
   - Lưu trữ metadata và nội dung ghi chú vào LanceDB để tìm kiếm ngữ nghĩa sau này (Semantic Search).

---

### Bước 3: Tích Hợp Cơ Chế "Tự Tiến Hóa Kỹ Năng" (Hermes Concept)
Làm thế nào để AI tự viết ra kỹ năng mới hỗ trợ bạn?

1. Thiết lập cấu trúc một **Skill** dưới dạng file Markdown trong `vault/.system/skills/`:
   ```markdown
   ---
   name: "Summarize Project Status"
   description: "Tóm tắt trạng thái tiến độ dự án từ thư mục vault"
   trigger: "khi người dùng yêu cầu báo cáo tiến độ tuần"
   ---
   
   # Hướng dẫn hành động (System Prompt cho Agent)
   1. Quét qua các ghi chú có tag `#project` hoặc `#todo`.
   2. Phân tích các đầu việc đã hoàn thành và chưa hoàn thành.
   3. Trả về báo cáo dạng Markdown bảng biểu đẹp mắt.
   ```
2. Khi người dùng nhập lệnh qua CLI, Agent sẽ quét thư mục `skills/` trước, tìm skill khớp với yêu cầu của bạn bằng Semantic Search, tải hướng dẫn hành động đó vào Context Window rồi thực thi.

---

## 💡 Lời Khuyên Giúp Duy Trì Tri Thức Dự Án (Hermes Workflow)

Vì bạn làm một mình, việc duy trì tài liệu kỹ thuật rất quan trọng để không bị quên ngữ cảnh sau vài tuần ngưng phát triển:

* **Tự động hóa Nhật ký Dev (Dev Journal):** Hãy tạo thư mục `vault/DevJournal/`. Mỗi khi bạn kết thúc một phiên code, hãy dành 2 phút viết nhanh những gì vừa làm và lỗi nào vừa sửa.
* **Huấn luyện Agent từ Nhật ký:** Định kỳ chạy script agent để nó đọc thư mục `DevJournal/` này. Khi bạn quay lại dự án, bạn chỉ cần hỏi Agent: *"Tuần trước tôi đang làm dở cái gì và gặp lỗi gì?"*, Agent sẽ tóm tắt lại chính xác cho bạn.
* **Cộng sinh với IDE:** Hãy sử dụng các công cụ IDE hỗ trợ Agent (như Cursor hoặc Gemini Agent) trỏ thẳng vào thư mục `vault/` này để hỗ trợ bạn lập trình chính dự án Symbio.

---

## 🏃‍♂️ Action Items (Làm ngay bây giờ)

1. [ ] **Tạo cấu trúc thư mục dự án** bằng lệnh `mkdir` trên máy của bạn.
2. [ ] **Tạo một ghi chú Markdown mẫu** đầu tiên.
3. [ ] **Đăng ký Google AI Studio API Key** (miễn phí hạn mức cơ bản, tốc độ rất nhanh và có context window lên tới 2 triệu tokens).
4. [ ] **Thiết lập thư mục `agent/`** và bắt đầu viết script Python kết nối đầu tiên.
