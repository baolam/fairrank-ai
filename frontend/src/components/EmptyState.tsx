export function EmptyState({ message }: { message: string }) {
  return (
    <div className="rounded-md border border-fr-line bg-white p-4 text-sm text-fr-ink-soft">
      {message}
    </div>
  )
}
