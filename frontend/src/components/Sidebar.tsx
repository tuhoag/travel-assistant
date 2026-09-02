import type { Conversation } from "@/lib/chat";

interface SidebarProps {
  open: boolean;
  conversations: Conversation[];
  activeConversationId: string;
  onNewChat: () => void;
  onSelectConversation: (id: string) => void;
}

export function Sidebar({
  open,
  conversations,
  activeConversationId,
  onNewChat,
  onSelectConversation,
}: SidebarProps) {
  return (
    <aside
      className={`${
        open ? "w-64" : "w-0"
      } shrink-0 overflow-hidden bg-zinc-900 text-zinc-100 transition-[width] duration-200`}
    >
      <div className="flex h-full w-64 flex-col p-2">
        <button
          onClick={onNewChat}
          className="mb-2 flex items-center gap-2 rounded-lg border border-zinc-700 px-3 py-2 text-sm hover:bg-zinc-800"
        >
          <span className="text-lg leading-none">+</span> New chat
        </button>

        <div className="flex-1 space-y-1 overflow-y-auto">
          {conversations.map((c) => (
            <button
              key={c.id}
              onClick={() => onSelectConversation(c.id)}
              className={`block w-full truncate rounded-lg px-3 py-2 text-left text-sm ${
                c.id === activeConversationId ? "bg-zinc-800" : "hover:bg-zinc-800/60"
              }`}
            >
              {c.title}
            </button>
          ))}
        </div>
      </div>
    </aside>
  );
}
