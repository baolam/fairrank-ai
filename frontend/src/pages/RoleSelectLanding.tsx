import { Link } from 'react-router-dom'

const ROLES = [
  {
    to: '/recruiter',
    icon: '🧑‍💼',
    title: 'Nhà Tuyển Dụng (Enterprise ATS)',
    description: 'Quản lý tin tuyển dụng, bảng Kanban 7 bước, chấm Scorecard, lên lịch phỏng vấn & gửi email.',
  },
  {
    to: '/talent-pool',
    icon: '👥',
    title: 'Kho Tài Năng (Central Talent Pool)',
    description: 'Tra cứu, lọc ứng viên toàn hệ thống theo kỹ năng, kinh nghiệm và lịch sử ứng tuyển.',
  },
  {
    to: '/apply',
    icon: '📝',
    title: 'Cổng Ứng Viên (Candidate Portal)',
    description: 'Xem các vị trí đang mở, nộp hồ sơ CV với tính năng tự động trích xuất kỹ năng qua AI.',
  },
  {
    to: '/quick-demo',
    icon: '⚡',
    title: 'Mô Phỏng Kiểm Toán (AI Audit Simulator)',
    description: 'Trực quan hóa đường cong Pareto, kiểm toán phản thực tế 160 biến thể tên & xuất chứng nhận tuân thủ.',
  },
]

export function RoleSelectLanding() {
  return (
    <div className="flex min-h-screen items-center justify-center bg-[#f6f5fb] px-4 py-12">
      <div className="w-full max-w-5xl">
        <div className="mb-10 text-center">
          <div className="inline-flex items-center gap-2 rounded-full bg-brand-50 px-3.5 py-1 text-xs font-semibold text-brand-700 mb-3 border border-brand-200">
            🛡️ Enterprise Algorithmic Fairness &amp; ATS Platform
          </div>
          <h1 className="text-3xl sm:text-4xl font-extrabold text-gray-900">
            FairRank-AI · Hệ Thống ATS Doanh Nghiệp Toàn Diện
          </h1>
          <p className="mt-2 text-base text-gray-600 max-w-2xl mx-auto">
            Hệ sinh thái tuyển dụng tích hợp bóc tách CV, tự động hóa quy trình tuyển dụng đa giai đoạn và kiểm toán chống thiên vị thuật toán (EEOC &amp; EU AI Act).
          </p>
        </div>
        <div className="grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-4">
          {ROLES.map((role) => (
            <Link
              key={role.to}
              to={role.to}
              className="flex flex-col justify-between rounded-2xl border border-gray-200 bg-white p-6 shadow-xs transition-all hover:-translate-y-1 hover:border-brand-500 hover:shadow-lg"
            >
              <div>
                <span className="text-4xl block mb-3">{role.icon}</span>
                <span className="text-base font-bold text-gray-900 block mb-2">{role.title}</span>
                <span className="text-xs text-gray-500 leading-relaxed block">{role.description}</span>
              </div>
              <div className="mt-4 pt-3 border-t border-gray-100 text-xs font-semibold text-brand-600">
                Truy cập ngay →
              </div>
            </Link>
          ))}
        </div>
      </div>
    </div>
  )
}
