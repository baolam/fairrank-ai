export function EmptyState({ message }: { message: string }) {
  return (
    <div className="rounded-xl border border-blue-200 bg-blue-50 p-4 text-sm text-blue-800">
      💡 {message}
    </div>
  )
}
