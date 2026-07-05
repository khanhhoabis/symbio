---
name: github-workflow
description: Tự động hóa quy trình làm việc với GitHub, bao gồm tạo Issue, tạo nhánh tính năng (Feature Branch) và mở Pull Request để bảo vệ nhánh main.
---

# Quy Trình Tự Động Hóa GitHub & Nhánh Tính Năng

Tài liệu này hướng dẫn Agent các lệnh cụ thể để làm việc với GitHub CLI (`gh`) và `git` nhằm thực thi đúng quy tắc phân nhánh của dự án Symbio.

---

## 🛠️ 1. Kiểm tra trạng thái xác thực GitHub
Trước khi thực hiện bất kỳ lệnh GitHub nào, Agent cần kiểm tra xem GitHub CLI đã được cài đặt và đăng nhập hay chưa:
```bash
gh auth status
```
*Nếu chưa đăng nhập, Agent cần nhắc người dùng chạy lệnh `gh auth login`.*

---

## 📋 2. Quy trình tạo mới một nhiệm vụ (Task Initialization)

Khi bắt đầu một nhiệm vụ mới, Agent thực hiện tuần tự các bước sau:

### Bước 2.1: Tạo GitHub Issue
Tạo một issue mới để mô tả công việc sẽ làm:
```bash
gh issue create --title "[Feature/Fix] Tên nhiệm vụ ngắn gọn" --body "Mô tả chi tiết công việc cần hoàn thành."
```
*Lưu ý: Lưu lại mã số Issue (`#<number>`) trả về từ terminal.*

### Bước 2.2: Đồng bộ nhánh main và tạo Feature Branch
Quay lại nhánh `main`, lấy cập nhật mới nhất và tạo nhánh tính năng liên kết với Issue:
```bash
git checkout main
git pull
git checkout -b feature/issue-<number>-<slug-tên-nhiệm-vụ>
```
*(Ví dụ: `git checkout -b feature/issue-5-setup-lancedb-agent`)*

---

## 🚀 3. Quy trình gửi yêu cầu kiểm duyệt (Pull Request)

Khi hoàn thành công việc và đã chạy thử thành công, Agent chuẩn bị hợp nhất code:

### Bước 3.1: Commit các thay đổi
Đảm bảo tất cả code đã được lưu trữ cục bộ:
```bash
git add .
git commit -m "feat(scope): completed task description Closes #<number>"
```

### Bước 3.2: Push nhánh lên Remote và Tạo PR
Đẩy nhánh mới lên GitHub và tạo một Pull Request tự động:
```bash
git push -u origin feature/issue-<number>-<slug-tên-nhiệm-vụ>
gh pr create --title "[PR] Hoàn thành Issue #<number>" --body "Mô tả các thay đổi đã thực hiện và kết quả kiểm thử. Closes #<number>"
```
*Sau khi PR được tạo, Agent báo cáo link PR cho người dùng kiểm duyệt.*

---

## ⚠️ 4. Quy trình Revert (Khắc phục khi có lỗi xảy ra)

Nếu mã nguồn trên nhánh làm việc bị lỗi nghiêm trọng hoặc người dùng muốn hủy bỏ các thay đổi gần nhất:

### Trường hợp 1: Huỷ bỏ commit chưa đẩy lên remote (Local Undo)
Nếu chưa push, bạn chỉ cần reset nhánh về trạng thái trước đó:
```bash
# Quay lại 1 commit trước đó và giữ nguyên file đã sửa
git reset --soft HEAD~1

# Hoặc xóa bỏ hoàn toàn tất cả thay đổi chưa commit để làm lại sạch sẽ
git reset --hard HEAD
```

### Trường hợp 2: Hợp nhất (Merge) PR bị lỗi trên main và cần Revert gấp
Nếu PR đã merge vào `main` nhưng gây lỗi trên môi trường chạy:
1. Quay lại nhánh `main` và cập nhật:
   ```bash
   git checkout main
   git pull
   ```
2. Tìm commit hash của đợt merge lỗi bằng `git log -n 5`.
3. Tạo commit revert:
   ```bash
   git revert -m 1 <commit-hash-merge>
   ```
4. Push trực tiếp commit revert lên main (đây là trường hợp khẩn cấp được phép) hoặc tạo một PR revert khẩn cấp.
