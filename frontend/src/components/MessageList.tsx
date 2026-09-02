"use client";

import { useEffect, useRef } from "react";
import { HotelResults } from "@/components/HotelResults";
import type { ChatMessage } from "@/lib/chat";

interface MessageListProps {
  messages: ChatMessage[];
  isSending: boolean;
}

export function MessageList({ messages, isSending }: MessageListProps) {
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight, behavior: "smooth" });
  }, [messages, isSending]);

  return (
    <div ref={scrollRef} className="flex-1 overflow-y-auto">
      <div className="mx-auto flex max-w-3xl flex-col gap-6 px-4 py-6">
        {messages.map((m) =>
          m.role === "user" ? (
            <div key={m.id} className="flex justify-end">
              <div className="max-w-[75%] rounded-2xl bg-zinc-100 px-4 py-2.5 text-[15px] leading-relaxed text-zinc-900 dark:bg-zinc-700 dark:text-zinc-50">
                {m.content}
              </div>
            </div>
          ) : (
            <div key={m.id} className="flex gap-3">
              <div className="mt-0.5 flex h-7 w-7 shrink-0 items-center justify-center rounded-full bg-emerald-600 text-xs font-semibold text-white">
                TA
              </div>
              <div className="flex min-w-0 flex-1 flex-col gap-3">
                <div className="whitespace-pre-wrap pt-1 text-[15px] leading-relaxed text-zinc-800 dark:text-zinc-100">
                  {m.content}
                </div>
                {m.hotels && m.hotels.length > 0 && <HotelResults hotels={m.hotels} />}
              </div>
            </div>
          ),
        )}
        {isSending && (
          <div className="flex gap-3">
            <div className="mt-0.5 flex h-7 w-7 shrink-0 items-center justify-center rounded-full bg-emerald-600 text-xs font-semibold text-white">
              TA
            </div>
            <div className="flex items-center gap-1 pt-3">
              <span className="h-1.5 w-1.5 animate-pulse rounded-full bg-zinc-400 [animation-delay:-0.3s]" />
              <span className="h-1.5 w-1.5 animate-pulse rounded-full bg-zinc-400 [animation-delay:-0.15s]" />
              <span className="h-1.5 w-1.5 animate-pulse rounded-full bg-zinc-400" />
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
