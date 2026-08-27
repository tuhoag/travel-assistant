interface ChatHeaderProps {
  title: string;
  onToggleSidebar: () => void;
}

export function ChatHeader({ title, onToggleSidebar }: ChatHeaderProps) {
  return (
    <header className="flex items-center gap-3 border-b border-zinc-200 px-4 py-3 dark:border-zinc-800">
      <button
        onClick={onToggleSidebar}
        aria-label="Toggle sidebar"
        className="rounded-md p-1.5 text-zinc-500 hover:bg-zinc-100 dark:text-zinc-400 dark:hover:bg-zinc-800"
      >
        ☰
      </button>
      <h1 className="text-sm font-medium text-zinc-900 dark:text-zinc-100">{title}</h1>
    </header>
  );
}
