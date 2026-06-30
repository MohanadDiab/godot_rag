import { isValidElement, useState } from "react";
import type { Components } from "react-markdown";
import type { Element } from "hast";
import { Prism as SyntaxHighlighter } from "react-syntax-highlighter";
import { oneDark } from "react-syntax-highlighter/dist/esm/styles/prism";
import { looksLikeGdscript } from "../utils/repairMarkdown";

const LANGUAGE_ALIASES: Record<string, string> = {
  gdscript: "python",
  godot: "python",
};

function classNameFrom(value: unknown): string {
  if (Array.isArray(value)) return value.join(" ");
  if (typeof value === "string") return value;
  return "";
}

function codeText(children: React.ReactNode): string {
  if (typeof children === "string") return children.replace(/\n$/, "");
  if (Array.isArray(children)) {
    return children
      .map((child) => (typeof child === "string" ? child : ""))
      .join("")
      .replace(/\n$/, "");
  }
  return String(children).replace(/\n$/, "");
}

function languageFrom(className?: string, node?: Element): string | null {
  const match = /language-([\w-]+)/.exec(classNameFrom(className || node?.properties?.className));
  return match?.[1] ?? null;
}

interface CodeBlockProps {
  language?: string | null;
  code: string;
}

export function CodeBlock({ language, code }: CodeBlockProps) {
  const [copied, setCopied] = useState(false);
  const label = language ?? "code";
  const highlighterLanguage = language ? (LANGUAGE_ALIASES[language] ?? language) : undefined;

  const copy = async () => {
    await navigator.clipboard.writeText(code);
    setCopied(true);
    setTimeout(() => setCopied(false), 1500);
  };

  return (
    <div className="code-block">
      <div className="code-block-header">
        <span>{label}</span>
        <button type="button" className="btn small" onClick={copy}>
          {copied ? "Copied!" : "Copy"}
        </button>
      </div>
      {highlighterLanguage ? (
        <SyntaxHighlighter
          key={code}
          style={oneDark}
          language={highlighterLanguage}
          PreTag="div"
          customStyle={{
            margin: 0,
            borderRadius: "0 0 8px 8px",
            fontSize: "0.85rem",
          }}
        >
          {code}
        </SyntaxHighlighter>
      ) : (
        <pre className="code-block-body">
          <code>{code}</code>
        </pre>
      )}
    </div>
  );
}

function isBlockCode(
  className: string | undefined,
  node: Element | undefined,
  children: React.ReactNode,
): boolean {
  if (languageFrom(className, node)) return true;
  if (codeText(children).includes("\n")) return true;
  return false;
}

export const markdownComponents: Components = {
  code({ className, children, node, ...props }) {
    const text = codeText(children);
    if (!isBlockCode(className, node, children)) {
      return (
        <code className="inline-code" {...props}>
          {children}
        </code>
      );
    }

    return <CodeBlock language={languageFrom(className, node) ?? (looksLikeGdscript(text) ? "gdscript" : null)} code={text} />;
  },
  pre({ children }) {
    if (isValidElement(children)) {
      return <>{children}</>;
    }
    return <pre className="code-block-body">{children}</pre>;
  },
};
