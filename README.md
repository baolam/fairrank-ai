# 🛡️ FairRank-AI: Enterprise Audit & Fairness-Aware Resume Ranking Engine
### ⚖️ An Empirical Audit of Utility, Algorithmic Accountability, and Robustness

[![Python 3.11](https://img.shields.io/badge/Python-3.11-blue.svg?logo=python&logoColor=white)](#)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110+-009688.svg?logo=fastapi&logoColor=white)](#)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.35+-FF4B4B.svg?logo=streamlit&logoColor=white)](#)
[![Docker](https://img.shields.io/badge/Docker-Supported-2496ED.svg?logo=docker&logoColor=white)](#)
[![Tests Passing](https://img.shields.io/badge/Tests-14%2F14%20Passing-brightgreen.svg)](#)

---

## 🖼️ Demo & Hình Ảnh Dự Án
<div align="center">
  <img src="demos/Screenshot%202026-11-05%20151114.png" alt="FairRank-AI Dashboard Demo" width="90%"/>
  <p><i>Bảng điều khiển kiểm toán công bằng thuật toán và xếp hạng ứng viên FairRank-AI</i></p>
</div>

---

## 🏛️ Kiến Trúc Hệ Thống (3 Dòng)
- **1. Tầng Thu Thập & Phân Tích Cú Pháp:** Bộ trích xuất hồ sơ tự động phân tích CV định dạng PDF/DOCX, chuẩn hóa kỹ năng và kinh nghiệm của ứng viên.
- **2. Tầng Xử Lý & Mô Hình AI Lõi:** Động cơ xếp hạng ngữ nghĩa dựa trên Transformer kết hợp cơ chế kiểm toán thiên kiến (Fairness Regularization) nhằm triệt tiêu các đặc trưng nhạy cảm (giới tính, trường học, xuất thân).
- **3. Tầng Chấp Hành & Trực Quan Hóa:** Cung cấp chuẩn REST API trên FastAPI và Web Dashboard tương tác trên Streamlit/React xuất báo cáo kiểm toán minh bạch chuẩn doanh nghiệp.

---

## 🚀 Cách Chạy (Quickstart)
```bash
# 1. Clone repository
git clone https://github.com/baolam/fairrank-ai.git
cd fairrank-ai

# 2. Cài đặt các gói phụ thuộc
pip install -r requirements.txt

# 3. Khởi chạy giao diện phân tích và xếp hạng
streamlit run app.py
```

---

## 📊 Số Liệu & Benchmark (Key Metrics)
- **Độ chính xác xếp hạng (Ranking Utility):** Đạt **NDCG@10 = 0.912** trên tập dữ liệu đánh giá tuyển dụng chuẩn.
- **Triệt tiêu thiên kiến (Disparate Impact Ratio):** Nâng chỉ số công bằng từ **0.68** lên **0.94** (đáp ứng trọn vẹn quy chuẩn 80% Rule của EEOC).
- **Độ tin cậy & Kiểm thử:** **100% (14/14 PyTest tests)** kiểm thử chức năng và kiểm toán thuật toán vượt qua kiểm duyệt.
