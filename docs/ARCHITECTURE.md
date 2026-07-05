# 🏗️ Tài Liệu Kiến Trúc Dự Án Symbio (ARCHITECTURE.md)

Tài liệu này mô tả chi tiết kiến trúc kỹ thuật của hệ điều hành tri thức cá nhân Symbio. Đây là nguồn tri thức nền tảng dùng cho cả nhà phát triển (người dùng) và AI Agent để luôn giữ sự đồng bộ và tránh sai lệch thiết kế (context drift).

---

## 📂 Tổng Quan Cấu Trúc Mã Nguồn

Hạt nhân AI của Symbio nằm trong thư mục `agent/` và được chia thành các module chức năng độc lập:

| Tên Module | Tệp tin | Chức năng chính |
| :--- | :--- | :--- |
| **Hệ thống Cấu hình** | [agent/config.py](file:///Users/hoanhk5/Documents/khbis_github/symbio/agent/config.py) | Nạp biến môi trường từ `.env` cục bộ (đường dẫn tuyệt đối), tự động tạo các thư mục lưu trữ hệ thống ngầm trong Vault. |
| **Cơ sở dữ liệu Vector**| [agent/db.py](file:///Users/hoanhk5/Documents/khbis_github/symbio/agent/db.py) | Thiết lập kết nối serverless LanceDB, sinh vector embeddings thông qua `google-genai` hoặc Ollama, định nghĩa schemas và thực thi tìm kiếm ngữ nghĩa. |
| **Trình quản lý Kỹ năng**| [agent/skills.py](file:///Users/hoanhk5/Documents/khbis_github/symbio/agent/skills.py) | Quét các tệp Markdown định nghĩa kỹ năng trong thư mục `.agents/skills/` và các tệp trong Vault hệ thống để phân tích YAML frontmatter cấu hình kỹ năng và nạp vào Vector DB. |
| **Hạt nhân Trình chạy** | [agent/hermes.py](file:///Users/hoanhk5/Documents/khbis_github/symbio/agent/hermes.py) | Điều phối luồng làm việc. Kết nối truy vấn DB tìm ghi chú và kỹ năng, lắp ráp prompt có cấu trúc suy nghĩ `<thought>` gửi đến LLM. |
| **Trình đồng bộ Tài liệu** | [agent/sync_docs.py](file:///Users/hoanhk5/Documents/khbis_github/symbio/agent/sync_docs.py) | Đồng bộ hóa tự động tài liệu kiến trúc và quy tắc Agent (`ARCHITECTURE.md`, `AGENTS.md`) dựa trên `git diff` sử dụng LLM. Bao gồm cơ chế chống lặp vô hạn (auto-commit). |
| **Động cơ Giám sát Vault**| [agent/watcher.py](file:///Users/hoanhk5/Documents/khbis_github/symbio/agent/watcher.py) | Giám sát tệp tin hệ thống thời gian thực (watchdog), tự động đồng bộ hóa gia tăng (incremental sync) ghi chú mới/sửa đổi/xóa vào Vector DB. |
| **Khung kiểm thử** | [agent/tests/](file:///Users/hoanhk5/Documents/khbis_github/symbio/agent/tests/) | Chứa các bộ kiểm thử tự động sử dụng `pytest` để đảm bảo tính đúng đắn của DB, cấu hình, kỹ năng và các hooks. |

---

## ⚙️ Cấu Hình Biến Môi Trường (`agent/.env`)

Các biến cấu hình bắt buộc:
* `VAULT_PATH`: Đường dẫn thư mục ghi chú cục bộ (Mặc định: `../vault`).
* `LLM_PROVIDER`: Nhà cung cấp LLM, hỗ trợ `gemini` hoặc `ollama`.
* `LLM_MODEL`: Tên mô hình chạy (Mặc định: `gemini-2.5-flash` cho Gemini).
* `GEMINI_API_KEY`: API Key lấy từ Google AI Studio (Bắt buộc nếu chọn provider là `gemini`).
* `OLLAMA_HOST`: Địa chỉ local endpoint (Mặc định: `http://localhost:11434`).

---

## 🗄️ Cấu Trúc Cơ Sở Dữ Liệu Vector (LanceDB Schema)

Cơ sở dữ liệu được lưu trữ serverless tại: `vault/.system/symbio_db`. 

### 1. Bảng Ghi Chú (`notes`)
Sử dụng để tìm kiếm ngữ nghĩa nội dung ghi chú Markdown của người dùng.
* `id` (`string`): Khóa định danh duy nhất (thường là đường dẫn hoặc tên file).
* `path` (`string`): Đường dẫn tương đối từ Vault đến tệp tin Markdown.
* `content` (`string`): Nội dung văn bản thô của ghi chú.
* `tags` (`string`): Các thẻ phân loại được lưu cách nhau bởi dấu phẩy.
* `last_modified` (`float`): Thời gian cập nhật tệp tin cuối cùng (timestamp).
* `vector` (`list[float32]`): Vector nhúng ngữ nghĩa của ghi chú.
  - Kích thước mặc định cho Gemini: **3072 chiều** (Mô hình: `gemini-embedding-2`).
  - Kích thước mặc định cho Ollama: **768 chiều** (Mô hình: `nomic-embed-text`).

### 2. Bảng Kỹ Năng Agent (`skills`)
Sử dụng để khớp ngữ cảnh các hành động Agent có thể thực hiện.
* `id` (`string`): Khóa định danh của kỹ năng.
* `name` (`string`): Tên kỹ năng thân thiện.
* `description` (`string`): Mô tả ngắn gọn nhiệm vụ kỹ năng hỗ trợ.
* `trigger` (`string`): Điều kiện kích hoạt tự nhiên.
* `file_path` (`string`): Đường dẫn tệp tin Markdown kỹ năng.
* `vector` (`list[float32]`): Vector nhúng của chuỗi thông tin `[Name + Description + Trigger]`.
  - Kích thước khớp hoàn toàn với cấu hình kích thước của Bảng `notes`.

---

## 🔄 Quy Tắc Đường Dẫn Cục Bộ (Local-First Portability)
Để đảm bảo người dùng có thể di chuyển cả thư mục ghi chú sang máy khác hoặc đồng bộ lên iCloud/Google Drive mà AI Agent vẫn không bị lỗi cấu hình:
1. Tất cả dữ liệu hệ thống ngầm, DB và Skills đều được lưu trữ **bên trong** thư mục `vault/.system/`.
2. Mọi đường dẫn trong mã nguồn Python khi đọc file cấu hình tương đối đều phải được giải quyết (resolve) thông qua vị trí tuyệt đối của thư mục `agent/` làm mốc tham chiếu thay vì dùng Cwd.

---

## 👁️ Động cơ Giám sát Vault (Watcher Engine)
Module [agent/watcher.py](file:///Users/hoanhk5/Documents/khbis_github/symbio/agent/watcher.py) thực hiện đồng bộ hóa tự động hai chiều giữa ổ đĩa cứng và LanceDB:
1. **Quét gia tăng khi khởi động (Incremental Sync):**
   - Đọc bảng chỉ mục hiện tại từ LanceDB thành danh sách Python sử dụng `table.to_arrow().to_pylist()` để tránh phụ thuộc vào thư viện nặng `pandas`.
   - Đối chiếu trường `last_modified` (timestamp) của tất cả tệp `.md` trên ổ đĩa với thuộc tính tương ứng lưu trong database.
   - Chỉ cập nhật/thêm các tệp mới/sửa đổi và tự động xóa bỏ các chỉ mục rác của các tệp đã bị xóa khi watcher ngoại tuyến (offline).
2. **Theo dõi sự kiện thời gian thực (Watchdog):**
   - Sử dụng thư viện `watchdog` lắng nghe sự kiện hệ thống tệp.
   - Các sự kiện `Created`/`Modified` kích hoạt sinh embedding và gọi `index_note()` để cập nhật bản ghi.
   - Sự kiện `Deleted` gọi `table.delete()` để xóa bản ghi.
   - Sự kiện `Moved` (đổi tên/di chuyển) thực thi xóa bản ghi cũ và nạp lại bản ghi ở đường dẫn mới.
3. **Loại trừ An toàn:**
   - Watcher bỏ qua tất cả tệp tin bắt đầu bằng dấu chấm `.` hoặc không thuộc định dạng `.md`.
   - **Đặc biệt loại trừ thư mục `.system/`** để tránh vòng lặp sự kiện vô hạn (ghi vào DB kích hoạt watcher quay lại ghi DB).

---

## 💻 Kiến Trúc Giao Diện Desktop (Tauri v2 + React)
Symbio Desktop đóng gói hạt nhân Python thành một ứng dụng đồ họa cục bộ mượt mà:

```text
  +-------------------------------------------------------------+
  |                   Symbio Desktop Shell                      |
  |                                                             |
  |  +--------------------+             +--------------------+  |
  |  |  React Frontend    |             |    Rust Backend    |  |
  |  |  (Vite + TS)       |             |    (Tauri Core)    |  |
  |  +--------------------+             +--------------------+  |
  |         |                                    |              |
  |         | 1. Gọi Tauri Command               |              |
  |         v                                    v              |
  |    get_server_port() -------> Lấy Cổng Mạng Cục Bộ          |
  |         |                                    |              |
  |         | 3. HTTP REST Requests              | 2. Spawn     |
  |         +-------------------+                | Subprocess   |
  |                             |                |              |
  |                             v                v              |
  |                     +---------------------------------+     |
  |                     |  Python Server (server.py)      |     |
  |                     |  (Cổng mạng động, CORS active)  |     |
  |                     +---------------------------------+     |
  +-------------------------------------------------------------+
```

### 1. Đồng Hành Tiến Trình (Subprocess Symbiosis)
- **Khởi chạy động (Dynamic Port):** Khi khởi động, Tauri Rust (`src-tauri/src/lib.rs`) quét tìm một cổng TCP cục bộ trống ngẫu nhiên (sử dụng `TcpListener` bind cổng `0`), sau đó khởi tạo tiến trình con chạy tệp Python REST API `agent/server.py` bằng tham số `--port <port>`.
- **Dọn dẹp tài nguyên:** Khi ứng dụng bị đóng (sự kiện `RunEvent::Exit`), Rust backend sẽ thu hồi tài nguyên và gọi hàm `.kill()` trên handle tiến trình con để dập tắt Python server chạy ngầm, bảo vệ RAM của hệ thống và giải phóng cổng mạng.

### 2. Cầu Nối API Giao Diện (React UI Connection)
- React Frontend giao tiếp với Tauri thông qua thư viện API của Tauri để chạy lệnh `get_server_port`.
- Giao diện 3 cột thực thi gọi các HTTP JSON endpoint cục bộ của Python server để nạp tài liệu, soạn thảo ghi chú, tự động lưu (auto-save với debounce 1.5 giây) và nói chuyện với Hermes Agent.