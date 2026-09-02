"use client";

import { useState } from "react";
import { ChatHeader } from "@/components/ChatHeader";
import { ChatInput } from "@/components/ChatInput";
import { MessageList } from "@/components/MessageList";
import { Sidebar } from "@/components/Sidebar";
import { WELCOME_MESSAGE, type ChatMessage, type Conversation } from "@/lib/chat";
import type { ChatResult } from "@/lib/backendClient";

// crypto.randomUUID() only exists in secure contexts (HTTPS or localhost) —
// this app is served over plain HTTP (no custom domain/ACM cert set up yet),
// so it's undefined there and throws. These ids are just React keys / thread
// ids, not security tokens, so a non-crypto generator is fine.
function generateId(): string {
  return `${Date.now().toString(36)}-${Math.random().toString(36).slice(2)}`;
}

export function ChatLayout() {
  const [conversations, setConversations] = useState<Conversation[]>([
    { id: "1", title: "New chat" },
  ]);
  const [activeConversationId, setActiveConversationId] = useState("1");
  const [messages, setMessages] = useState<ChatMessage[]>([WELCOME_MESSAGE]);
  const [isSending, setIsSending] = useState(false);
  const [sidebarOpen, setSidebarOpen] = useState(true);

  function startNewChat() {
    const id = generateId();
    setConversations((prev) => [{ id, title: "New chat" }, ...prev]);
    setActiveConversationId(id);
    setMessages([WELCOME_MESSAGE]);
  }

  async function sendMessage(text: string) {
    const trimmed = text.trim();
    if (!trimmed || isSending) return;

    setMessages((prev) => [...prev, { id: generateId(), role: "user", content: trimmed }]);
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
      const res = await fetch("/api/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ threadId: activeConversationId, query: trimmed }),
      });

      if (!res.ok) {
        throw new Error(`chat request failed: ${res.status}`);
      }
      const result: ChatResult = await res.json();
      setMessages((prev) => [
        ...prev,
        {
          id: generateId(),
          role: "assistant",
          content: result.answer ?? "No response from agent.",
          hotels: result.hotels,
        },
      ]);
    } catch {
      setMessages((prev) => [
        ...prev,
        { id: generateId(), role: "assistant", content: "Something went wrong. Please try again." },
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
