"use client";

import { useState, type FormEvent, type KeyboardEvent } from "react";

interface ChatInputProps {
  disabled: boolean;
  onSend: (message: string) => void;
}

export function ChatInput({ disabled, onSend }: ChatInputProps) {
  const [input, setInput] = useState("");

  function submit() {
    if (!input.trim() || disabled) return;
    onSend(input);
    setInput("");
  }

  function handleSubmit(e: FormEvent) {
    e.preventDefault();
    submit();
  }

  function handleKeyDown(e: KeyboardEvent<HTMLTextAreaElement>) {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      submit();
    }
  }

  return (
    <form onSubmit={handleSubmit} className="border-t border-zinc-200 px-4 py-4 dark:border-zinc-800">
      <div className="mx-auto flex max-w-3xl items-end gap-2 rounded-3xl border border-zinc-300 bg-white px-4 py-2.5 shadow-sm dark:border-zinc-700 dark:bg-zinc-800">
        <textarea
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="Ask about a city..."
          rows={1}
          disabled={disabled}
          className="max-h-40 flex-1 resize-none bg-transparent text-[15px] text-zinc-900 placeholder:text-zinc-400 outline-none dark:text-zinc-100"
        />
        <button
          type="submit"
          disabled={disabled || !input.trim()}
          className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-zinc-900 text-white disabled:opacity-30 dark:bg-zinc-100 dark:text-zinc-900"
        >
          ↑
        </button>
      </div>
    </form>
  );
}
