import { Link } from 'react-router-dom'

const ROLES = [
  {
    to: '/apply',
    icon: '📝',
    title: 'Ứng viên',
    description: 'Chọn một job đang mở và nộp CV ứng tuyển.',
  },
  {
    to: '/recruiter',
    icon: '🧑‍💼',
    title: 'Nhà tuyển dụng',
    description: 'Tạo job posting, xem hồ sơ đã nộp, chạy xếp hạng & audit công bằng.',
  },
  {
    to: '/quick-demo',
    icon: '🧪',
    title: 'Demo nhanh',
    description: 'Dữ liệu mẫu có sẵn, không cần đóng vai — xem thẳng pipeline xếp hạng & audit.',
  },
]

export function RoleSelectLanding() {
  return (
    <div className="flex min-h-screen items-center justify-center bg-[#f6f5fb] px-4 py-12">
      <div className="w-full max-w-4xl">
        <div className="mb-10 text-center">
          <h1 className="text-3xl font-bold text-gray-900">🛡️ FairRank-AI</h1>
          <p className="mt-2 text-base text-gray-600">
            Nền tảng kiểm toán công bằng &amp; xếp hạng CV. Bạn muốn vào với vai trò nào?
          </p>
        </div>
        <div className="grid grid-cols-1 gap-5 sm:grid-cols-3">
          {ROLES.map((role) => (
            <Link
              key={role.to}
              to={role.to}
              className="flex flex-col gap-2 rounded-2xl border border-gray-200 bg-white p-6 text-center shadow-sm transition-transform hover:-translate-y-0.5 hover:border-brand-400 hover:shadow-md"
            >
              <span className="text-4xl">{role.icon}</span>
              <span className="text-lg font-semibold text-gray-900">{role.title}</span>
              <span className="text-sm text-gray-500">{role.description}</span>
            </Link>
          ))}
        </div>
      </div>
    </div>
  )
}
