# Workspace Agent Rules - Symbio

Mọi Agent AI (bao gồm cả coding assistants) hoạt động trong thư mục này phải tuyệt đối tuân thủ các quy tắc sau để duy trì tính toàn vẹn của mã nguồn và tri thức dự án.

---

## 🚫 1. Quy Tắc Phân Nhánh (Branching Rules)
* **KHÔNG ĐƯỢC PHÉP** thực hiện các thay đổi (commit, push) trực tiếp trên nhánh `main`. Nhánh `main` đại diện cho sản phẩm ổn định nhất (production-ready).
* Tất cả mọi công việc phát triển, chỉnh sửa cấu trúc hay viết tài liệu đều phải được thực hiện trên một nhánh tính năng (**Feature Branch**) riêng biệt.
* Định dạng tên nhánh: `feature/issue-<number>-<description>` (ví dụ: `feature/issue-12-setup-sqlite-db`).

---

## 📋 2. Quy Tắc Sử Dụng GitHub Issues
* **BẮT ĐẦU:** Trước khi triển khai bất kỳ tính năng, chỉnh sửa lỗi (bugfix) hay nâng cấp cấu hình nào, Agent phải:
  1. Kiểm tra xem đã có GitHub Issue tương ứng hay chưa.
  2. Nếu chưa có, sử dụng CLI hoặc yêu cầu người dùng tạo một GitHub Issue để ghi nhận nhiệm vụ.
  3. Lấy mã số Issue (`<number>`) và tạo nhánh phát triển tương ứng từ `main`.
* **KẾT THÚC:** Khi hoàn thành nhiệm vụ, Agent phải kiểm tra tính đúng đắn của code và tạo một **Pull Request (PR)** từ feature branch về `main`. Chỉ khi PR được merge (bởi người dùng hoặc hệ thống CI), mã nguồn trên `main` mới được cập nhật.

---

## 💬 3. Quy Tắc Commit & Đóng Gói
* Các thông điệp commit phải tuân thủ chuẩn Conventional Commits (ví dụ: `feat(agent): add semantic search core`, `fix(ui): correct editor line height`).
* Luôn liên kết mã số Issue trong nội dung commit hoặc PR (ví dụ: `Closes #12`).
* Trong quá trình làm việc, hãy tạo các commit nhỏ và liên tục thay vì gom tất cả thay đổi vào một commit duy nhất. Điều này giúp dễ dàng `git revert` khi xảy ra lỗi.

---

## 🤖 4. Quy Tắc Tác Vụ Tự Động (Automated Agent Operations)

Để duy trì tính đồng bộ và chất lượng tài liệu, một số tác vụ được tự động hóa bởi các AI Agent:

### 4.1. Document Sync Agent (`agent/sync_docs.py`)
*   **Chức năng:** Tự động phân tích `git diff` của mỗi commit và cập nhật các tài liệu kiến trúc (`docs/ARCHITECTURE.md`) và quy tắc agent (`.agents/AGENTS.md`) nếu phát hiện thay đổi về kiến trúc, cấu hình, phụ thuộc, cấu trúc thư mục hoặc lược đồ cơ sở dữ liệu.
*   **Cơ chế:** Hoạt động như một Git Hook (hoặc tương đương), sử dụng LLM để đánh giá và tạo nội dung cập nhật.
*   **Cam kết Commit:** Khi tài liệu được cập nhật tự động, Agent sẽ tạo một commit mới với thông điệp theo định dạng `docs(auto): sync architecture and workspace rules`.
*   **Cơ chế chống lặp:** Agent được cấu hình để tự động thoát nếu commit cuối cùng là một commit `docs(auto):` do chính nó tạo ra, nhằm ngăn chặn vòng lặp vô hạn.