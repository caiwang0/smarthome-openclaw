import { useState } from "react";

interface ChatInputProps {
  onSend: (message: string) => void;
  disabled: boolean;
}

export default function ChatInput({ onSend, disabled }: ChatInputProps) {
  const [value, setValue] = useState("");

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    const trimmed = value.trim();
    if (!trimmed || disabled) return;
    onSend(trimmed);
    setValue("");
  }

  function handleKeyDown(e: React.KeyboardEvent) {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSubmit(e);
    }
  }

  return (
    <form onSubmit={handleSubmit} className="flex gap-2 p-3 border-t border-[#E8E2D9]">
      <input
        type="text"
        value={value}
        onChange={(e) => setValue(e.target.value)}
        onKeyDown={handleKeyDown}
        disabled={disabled}
        placeholder={disabled ? "Thinking..." : "Ask OpenClaw..."}
        className="flex-1 bg-white border border-[#E8E2D9] text-[#2C2520] text-sm px-3 py-2 rounded focus:outline-none focus:border-[#E8913A] disabled:opacity-50 placeholder:text-[#B8ADA2]"
      />
      <button
        type="submit"
        disabled={disabled || !value.trim()}
        className="px-3 py-2 bg-[#E8913A] text-white text-sm font-semibold rounded hover:bg-[#D4802E] disabled:opacity-30 disabled:cursor-not-allowed transition-colors"
      >
        Send
      </button>
    </form>
  );
}
