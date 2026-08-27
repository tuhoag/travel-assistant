"use client";

import { useState } from "react";
import { ChatHeader } from "@/components/ChatHeader";
import { ChatInput } from "@/components/ChatInput";
import { MessageList } from "@/components/MessageList";
import { Sidebar } from "@/components/Sidebar";
import { WELCOME_MESSAGE, type ChatMessage, type Conversation } from "@/lib/chat";
import { backendClient } from "@/lib/backendClient";

export function ChatLayout() {
  const [conversations, setConversations] = useState<Conversation[]>([
    { id: "1", title: "New chat" },
  ]);
  const [activeConversationId, setActiveConversationId] = useState("1");
  const [messages, setMessages] = useState<ChatMessage[]>([WELCOME_MESSAGE]);
  const [isSending, setIsSending] = useState(false);
  const [sidebarOpen, setSidebarOpen] = useState(true);

  function startNewChat() {
    const id = crypto.randomUUID();
    setConversations((prev) => [{ id, title: "New chat" }, ...prev]);
    setActiveConversationId(id);
    setMessages([WELCOME_MESSAGE]);
  }

  async function sendMessage(text: string) {
    const trimmed = text.trim();
    if (!trimmed || isSending) return;

    setMessages((prev) => [...prev, { id: crypto.randomUUID(), role: "user", content: trimmed }]);
    setIsSending(true);

    // Give the active conversation a title from the first message.
    setConversations((prev) =>
      prev.map((c) =>
        c.id === activeConversationId && c.title === "New chat"
          ? { ...c, title: trimmed.slice(0, 40) }
          : c,
      ),
    );

    try {
      const result = await backendClient.chat(activeConversationId, trimmed);
      setMessages((prev) => [
        ...prev,
        { id: crypto.randomUUID(), role: "assistant", content: result.answer ?? "No response from agent." },
      ]);
    } catch {
      setMessages((prev) => [
        ...prev,
        { id: crypto.randomUUID(), role: "assistant", content: "Something went wrong. Please try again." },
      ]);
    } finally {
      setIsSending(false);
    }
  }

  return (
    <div className="flex min-h-screen w-full bg-white dark:bg-[#212121]">
      <Sidebar
        open={sidebarOpen}
        conversations={conversations}
        activeConversationId={activeConversationId}
        onNewChat={startNewChat}
        onSelectConversation={setActiveConversationId}
      />

      <div className="flex min-w-0 flex-1 flex-col">
        <ChatHeader title="Travel Assistant" onToggleSidebar={() => setSidebarOpen((v) => !v)} />
        <MessageList messages={messages} isSending={isSending} />
        <ChatInput disabled={isSending} onSend={sendMessage} />
      </div>
    </div>
  );
}
