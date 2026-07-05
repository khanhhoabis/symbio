# 🛠️ Thư Mục Kỹ Năng Tự Tiến Hóa (Symbio Agent Skills)

Thư mục này chứa các kỹ năng tự động học hỏi hoặc các kỹ năng được thiết lập sẵn của **Symbio Agent**.

## 📌 Cách thức hoạt động
1. Mỗi tệp tin `.md` trong thư mục này đại diện cho một kỹ năng (Skill).
2. Tệp tin được viết theo định dạng Markdown với phần **YAML frontmatter** ở đầu để khai báo tên, mô tả và trigger (điều kiện kích hoạt).
3. Động cơ Hermes Agent sẽ quét thư mục này bằng tìm kiếm ngữ nghĩa (Semantic Search) mỗi khi nhận được yêu cầu từ người dùng để tìm kỹ năng phù hợp nhất.

## ✍️ Ví dụ cấu hình một Kỹ năng (`example_skill.md`)

```markdown
---
name: "Clean Inbox"
description: "Dọn dẹp hòm thư Inbox bằng cách tự động gắn tag và di chuyển các ghi chú cũ vào Archive."
trigger: "khi người dùng yêu cầu dọn dẹp hoặc sắp xếp thư mục Inbox"
---

# Hướng dẫn hành động (Instructions)
1. Đọc danh sách các file trong thư mục `vault/Inbox/`.
2. Kiểm tra ngày chỉnh sửa cuối cùng. Nếu file có tuổi thọ > 7 ngày và chưa có liên kết mới, đề xuất di chuyển vào thư mục `vault/Archive/`.
3. Gợi ý gắn tag chủ đề cho từng file trước khi di chuyển.
```
