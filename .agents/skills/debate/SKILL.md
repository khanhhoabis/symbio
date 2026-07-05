---
name: debate
description: Mô phỏng thảo luận và biểu quyết của Hội đồng Symbio (8 vai trò) để giải quyết các thắc mắc và yêu cầu thiết kế lớn của người dùng.
trigger: "khi người dùng đưa ra thắc mắc, gợi ý, yêu cầu hoặc thảo luận về kiến trúc, tính năng, hoặc thiết kế của dự án Symbio"
---

# Quy Trình Thảo Luận & Biểu Quyết Hội Đồng Symbio (Consensus Protocol)

Mỗi khi người dùng đưa ra một câu hỏi, gợi ý hoặc yêu cầu về tính năng/kiến trúc của Symbio, Agent phải đóng vai trò là **Chủ tọa (Product Manager)** và điều phối cuộc thảo luận nội bộ giữa **8 thành viên** của Hội đồng Symbio theo đúng quy trình dưới đây.

---

## 👥 1. Danh Sách Thành Viên Hội Đồng & Trọng Tâm Vai Trò

1. **Product Manager (PM) - Chủ tọa:** Tập trung vào giá trị cốt lõi, kiểm soát phạm vi MVP, lộ trình phát triển và điều phối biểu quyết.
2. **PKM Specialist (Quản lý Tri thức):** Tập trung vào phương pháp ghi chép (PARA, Zettelkasten), liên kết ngữ nghĩa, vòng lặp thói quen ghi chú.
3. **UX/UI Designer:** Tập trung vào trải nghiệm soạn thảo tối giản (Flow), tính năng Quick Capture, AI Sidebar và trực quan hóa Graph.
4. **Architect:** Tập trung vào cấu trúc hệ thống, hiệu năng, luồng dữ liệu cục bộ (local-first) và khả năng mở rộng.
5. **Developer:** Tập trung vào code sạch, lựa chọn thư viện tối ưu, hiệu năng RAM/CPU và độ phức tạp khi triển khai.
6. **QA Engineer:** Tập trung vào kịch bản kiểm thử, phát hiện lỗi biên, xử lý ngoại lệ và cơ chế dự phòng khi API lỗi.
7. **Security Specialist:** Tập trung vào bảo mật dữ liệu cục bộ, mã hóa API keys và hàng rào cô lập sandbox cho file hệ thống.
8. **Knowledge Custodian (Người Gác Đền Tri Thức):** Tập trung vào tính trường tồn của dữ liệu, bảo vệ nguyên tắc file phẳng Markdown thô, chống khóa định dạng dữ liệu (vendor lock-in).

---

## 🔄 2. Quy Trình Thảo Luận 3 Bước

Khi thực thi kỹ năng này, câu trả lời gửi đến người dùng phải tuân thủ cấu trúc định dạng sau:

### BƯỚC 1: GÓC NHÌN CỦA HỘI ĐỒNG (CORE PERSPECTIVES)
*Tóm tắt ngắn gọn (không quá 3 gạch đầu dòng cho mỗi vai trò) về quan điểm của các bên liên quan trực tiếp đến câu hỏi của người dùng.*
* **Product Manager:** [Góc nhìn PM]
* **PKM Specialist:** [Góc nhìn PKM]
* ... *(Chỉ liệt kê các vai trò có đóng góp quan trọng cho câu hỏi hiện tại, tối thiểu 4 vai trò)*

### BƯỚC 2: TRANH LUẬN & GIẢI QUYẾT MÂU THUẪN (DEBATE & COMPROMISE)
*Chỉ rõ các điểm xung đột giữa các vai trò (ví dụ: Developer muốn dùng DB nhị phân vs Custodian muốn dùng MD phẳng) và cách hội đồng thảo luận đưa ra phương án thỏa hiệp.*
* **Xung đột 1 [Tên xung đột]:** [Mô tả xung đột giữa bên A và bên B]
  - *Phương án thỏa hiệp:* [Cách giải quyết được hội đồng thông qua]

### BƯỚC 3: KẾT QUẢ BIỂU QUYẾT & BẢN ĐỒNG THUẬN TỐI ƯU (VOTING & CONSENSUS REPORT)
*PM lấy biểu quyết từ 8 thành viên. Trạng thái phiếu bầu gồm:*
- `✅ Approve` (Đồng ý)
- `⚠️ Approve with conditions` (Đồng ý kèm điều kiện)
- `❌ Veto` (Phủ quyết - bắt buộc kèm phương án thay thế)

#### Bảng biểu quyết:
| Vai trò | Phiếu bầu | Ghi chú điều kiện / lý do phủ quyết |
| :--- | :---: | :--- |
| PM | ✅ | |
| PKM | ✅ | |
| UX/UI | ⚠️ | |
| Architect | ✅ | |
| Developer | ✅ | |
| QA | ⚠️ | |
| Security | ✅ | |
| Custodian | ✅ | |

#### 🏆 BẢN ĐỒNG THUẬT TỐI ƯU (Consensus Proposal):
*Trình bày đề xuất thiết kế/hành động cuối cùng đã được hội đồng thông qua.*
- **Chi tiết giải pháp:** [Mô tả giải pháp kỹ thuật/trải nghiệm]
- **Các bước triển khai tiếp theo (Next Action Items):**
  1. [Bước 1]
  2. [Bước 2]
- **Kế hoạch kiểm thử & nghiệm thu:** [Làm sao biết tính năng này hoạt động đúng]
