import type { ChatMessage as ChatMessageType } from "../types";

export default function ChatMessage({ message }: { message: ChatMessageType }) {
  const isUser = message.role === "user";

  return (
    <div className={`flex ${isUser ? "justify-end" : "justify-start"}`}>
      <div
        className={`max-w-[85%] px-3 py-2 text-sm ${
          isUser
            ? "bg-[#E8913A] text-white rounded-t-lg rounded-bl-lg"
            : "bg-[#F0EBE4] text-[#2C2520] border border-[#E8E2D9] rounded-t-lg rounded-br-lg"
        }`}
      >
        <p className="whitespace-pre-wrap break-words">{message.content}</p>
        {message.isStreaming && (
          <span className="inline-block w-2 h-4 bg-[#E8913A] animate-pulse ml-0.5" />
        )}
      </div>
    </div>
  );
}
