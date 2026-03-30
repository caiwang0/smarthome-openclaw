import { useState, useRef, useEffect, useCallback } from "react";
import type { ChatMessage as ChatMessageType } from "../types";
import { sendChatMessage } from "../api";
import ChatMessage from "./ChatMessage";
import ChatInput from "./ChatInput";

function uuid() {
  if (typeof crypto !== "undefined" && crypto.randomUUID) {
    try { return crypto.randomUUID(); } catch {}
  }
  return "xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx".replace(/[xy]/g, (c) => {
    const r = (Math.random() * 16) | 0;
    return (c === "x" ? r : (r & 0x3) | 0x8).toString(16);
  });
}

const WELCOME_MESSAGE: ChatMessageType = {
  id: "welcome",
  role: "assistant",
  content:
    "Hi! I'm OpenClaw. I can control your devices and help manage your smart home. Try:\n\n" +
    '- "What devices do I have?"\n' +
    '- "Turn off the living room lights"\n' +
    '- "What\'s the temperature?"',
};

export default function ChatPanel() {
  const [messages, setMessages] = useState<ChatMessageType[]>([WELCOME_MESSAGE]);
  const [streaming, setStreaming] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const abortRef = useRef<AbortController | null>(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  function stopStreaming() {
    abortRef.current?.abort();
    abortRef.current = null;
    setStreaming(false);
    setMessages((prev) =>
      prev.map((m) => (m.isStreaming ? { ...m, isStreaming: false } : m))
    );
  }

  const handleSend = useCallback(async (text: string) => {
    const userMsg: ChatMessageType = {
      id: uuid(),
      role: "user",
      content: text,
    };

    const assistantId = uuid();
    const assistantMsg: ChatMessageType = {
      id: assistantId,
      role: "assistant",
      content: "",
      isStreaming: true,
    };

    setMessages((prev) => [...prev, userMsg, assistantMsg]);
    setStreaming(true);

    const abort = new AbortController();
    abortRef.current = abort;

    function updateAssistant(updater: (msg: ChatMessageType) => ChatMessageType) {
      setMessages((prev) =>
        prev.map((m) => (m.id === assistantId ? updater(m) : m))
      );
    }

    try {
      await sendChatMessage(
        text,
        (delta) => {
          updateAssistant((m) => ({ ...m, content: m.content + delta }));
        },
        () => {
          updateAssistant((m) => ({ ...m, isStreaming: false }));
          setStreaming(false);
        },
        (error) => {
          updateAssistant((m) => ({
            ...m,
            content: m.content || error,
            isStreaming: false,
          }));
          setStreaming(false);
        },
        abort.signal
      );
    } catch (err: any) {
      if (err?.name === "AbortError") return;
      updateAssistant((m) => ({
        ...m,
        content: m.content || "Connection failed. Is the API running?",
        isStreaming: false,
      }));
    } finally {
      setStreaming(false);
      abortRef.current = null;
    }
  }, []);

  return (
    <div className="flex flex-col h-full bg-[#FAF8F5] border-l border-[#E8E2D9]">
      <div className="px-3 py-3 border-b border-[#E8E2D9]">
        <div className="flex items-center justify-between">
          <span className="text-xs font-bold uppercase tracking-[0.15em] text-[#E8913A]">
            OpenClaw
          </span>
          <span className="text-[10px] text-[#B8ADA2] uppercase">
            AI Assistant
          </span>
        </div>
      </div>

      <div className="flex-1 overflow-y-auto p-3 space-y-3">
        {messages.map((msg) => (
          <ChatMessage key={msg.id} message={msg} />
        ))}
        <div ref={messagesEndRef} />
      </div>

      <ChatInput
        onSend={handleSend}
        onStop={streaming ? stopStreaming : undefined}
        disabled={streaming}
      />
    </div>
  );
}
