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
