import { useMemo } from "react";
import type { ChatMessage as ChatMessageType } from "../types";

// Lightweight markdown renderer — handles links, bold, inline code, and lists
function renderMarkdown(text: string, isUser: boolean): React.ReactNode[] {
  const lines = text.split("\n");
  const result: React.ReactNode[] = [];
  let key = 0;

  for (let i = 0; i < lines.length; i++) {
    if (i > 0) result.push(<br key={`br-${key++}`} />);
    const line = lines[i];

    // List items
    const listMatch = line.match(/^(\s*[-*]\s+)(.*)/);
    const prefix = listMatch ? listMatch[1] : "";
    const content = listMatch ? listMatch[2] : line;

    const parts = renderInline(content, isUser, key);
    key += parts.length + 1;

    if (listMatch) {
      result.push(
        <span key={`li-${key++}`}>
          {prefix.replace(/-|\*/, "\u2022")}
          {parts}
        </span>
      );
    } else {
      result.push(...parts);
    }
  }
  return result;
}

function renderInline(text: string, isUser: boolean, startKey: number, depth = 0): React.ReactNode[] {
  const parts: React.ReactNode[] = [];
  let key = startKey;

  // Match: markdown links [text](url), bold **text**, inline code `text`, raw URLs
  const regex = /\[([^\]]+)\]\((https?:\/\/[^)]+)\)|\*\*([\s\S]+?)\*\*|`([^`]+)`|(https?:\/\/\S+)/g;
  let lastIndex = 0;
  let match;

  while ((match = regex.exec(text)) !== null) {
    if (match.index > lastIndex) {
      parts.push(text.slice(lastIndex, match.index));
    }

    if (match[1] && match[2]) {
      // Markdown link [text](url)
      parts.push(
        <a
          key={`a-${key++}`}
          href={match[2]}
          target="_blank"
          rel="noopener noreferrer"
          className={`underline ${isUser ? "text-white font-semibold" : "text-[#E8913A] hover:text-[#D4802E]"}`}
        >
          {match[1]}
        </a>
      );
    } else if (match[3] != null) {
      // Bold **text** — recurse to handle links/code inside bold
      const inner = depth < 2 ? renderInline(match[3], isUser, key, depth + 1) : [match[3]];
      key += inner.length + 1;
      parts.push(<strong key={`b-${key++}`}>{inner}</strong>);
    } else if (match[4]) {
      // Inline code `text`
      parts.push(
        <code
          key={`c-${key++}`}
          className={`px-1 rounded text-xs font-mono ${isUser ? "bg-[#D4802E]" : "bg-[#E8E2D9]"}`}
        >
          {match[4]}
        </code>
      );
    } else if (match[5]) {
      // Raw URL
      parts.push(
        <a
          key={`a-${key++}`}
          href={match[5]}
          target="_blank"
          rel="noopener noreferrer"
          className={`underline break-all ${isUser ? "text-white font-semibold" : "text-[#E8913A] hover:text-[#D4802E]"}`}
        >
          {match[5]}
        </a>
      );
    }
    lastIndex = match.index + match[0].length;
  }

  if (lastIndex < text.length) {
    parts.push(text.slice(lastIndex));
  }

  return parts;
}

export default function ChatMessage({ message }: { message: ChatMessageType }) {
  const isUser = message.role === "user";
  const rendered = useMemo(
    () => renderMarkdown(message.content, isUser),
    [message.content, isUser]
  );

  return (
    <div className={`flex ${isUser ? "justify-end" : "justify-start"}`}>
      <div
        className={`max-w-[85%] px-3 py-2 text-sm leading-relaxed ${
          isUser
            ? "bg-[#E8913A] text-white rounded-t-lg rounded-bl-lg"
            : "bg-[#F0EBE4] text-[#2C2520] border border-[#E8E2D9] rounded-t-lg rounded-br-lg"
        }`}
      >
        <div className="break-words">{rendered}</div>
        {message.isStreaming && (
          <span className="inline-block w-2 h-4 bg-[#E8913A] animate-pulse ml-0.5" />
        )}
      </div>
    </div>
  );
}
