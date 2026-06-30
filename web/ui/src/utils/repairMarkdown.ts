/**
 * Repairs assistant markdown when the model omits fences or splits code awkwardly.
 * Wraps GDScript-like prose in fenced blocks and normalizes ``` markers.
 */

const FENCE = "```";

const GDSCRIPT_LINE =
  /^\s*(extends\s+\w+|class_name\s+\w+|@(?:onready|export|icon)|func\s+\w+|var\s+\w+|const\s+\w+|if\s+|elif\s+|else:|for\s+|while\s+|return\b|pass\b|#|move_and_slide|velocity\.|animated_sprite\.|is_on_floor|Input\.)/;

function normalizeFences(content: string): string {
  return (
    content
      // Ensure newline after opening fence + optional language
      .replace(/```([\w-]*)\s*([^\n`])/g, `${FENCE}$1\n$2`)
      // Strip stray lone "code" lines sometimes echoed from UI labels
      .replace(/^\s*code\s*$/gim, "")
  );
}

export function looksLikeGdscript(text: string): boolean {
  const t = text.trim();
  if (!t) return false;

  if (/^(extends|class_name)\s+\w+/m.test(t)) return true;
  if (/\bfunc\s+_?(?:ready|physics_process|process)\s*\(/.test(t)) return true;
  if (/^\s*func\s+\w+.*->\s*[\w.?]+/m.test(t)) return true;
  if ((t.match(/\bfunc\s+\w+/g)?.length ?? 0) >= 2) return true;
  if (/\bmove_and_slide\s*\(/.test(t)) return true;
  if ((t.match(/\bconst\s+\w+/g)?.length ?? 0) >= 2) return true;
  if ((t.match(/\bvar\s+\w+/g)?.length ?? 0) >= 2) return true;
  if (/@onready\b/.test(t) && /\bfunc\s+\w+/.test(t)) return true;
  if (/\bInput\.is_action/.test(t) && /\bfunc\s+\w+/.test(t)) return true;

  const lines = t.split(/\n/).filter((line) => line.trim());
  if (lines.length < 2) return false;

  const codeLines = lines.filter(
    (line) => GDSCRIPT_LINE.test(line) || /^\s*#/.test(line) || line.includes("-> void:"),
  );
  return codeLines.length / lines.length >= 0.35;
}

function mergeAdjacentGdscriptFences(content: string): string {
  let prev = "";
  let current = content;
  const adjacentRe =
    /```gdscript\n([\s\S]*?)```(?:[ \t]*\n+)[ \t]*```gdscript\n([\s\S]*?)```/g;

  while (prev !== current) {
    prev = current;
    current = current.replace(adjacentRe, (_m, a, b) => {
      const body = `${String(a).replace(/\n$/, "")}\n${String(b).replace(/^\n/, "")}`;
      return `\`\`\`gdscript\n${body}\n\`\`\``;
    });
  }

  // Absorb code-like gaps between gdscript fences (broken model fences mid-script)
  const gapRe = /```gdscript\n([\s\S]*?)```[ \t]*\n+([\s\S]*?)\n+```gdscript\n([\s\S]*?)```/g;
  prev = "";
  while (prev !== current) {
    prev = current;
    current = current.replace(gapRe, (_m, a, gap, b) => {
      const middle = String(gap).trim();
      if (!middle || !looksLikeGdscript(middle)) {
        return _m;
      }
      const body = `${String(a).replace(/\n$/, "")}\n${middle}\n${String(b).replace(/^\n/, "")}`;
      return `\`\`\`gdscript\n${body}\n\`\`\``;
    });
  }

  return current;
}

function wrapIfCode(text: string): string {
  const trimmed = text.trim();
  if (!trimmed) return text;
  if (looksLikeGdscript(trimmed)) {
    return `${FENCE}gdscript\n${trimmed}\n${FENCE}`;
  }
  return text;
}

function inferFenceLanguage(body: string, lang: string): string {
  if (lang && lang !== "code") return lang;
  if (looksLikeGdscript(body)) return "gdscript";
  return lang || "gdscript";
}

/**
 * Split on complete fenced blocks, wrap code-like gaps, normalize languages.
 */
export function repairMarkdown(content: string, streaming = false): string {
  if (!content.trim()) return content;

  let normalized = normalizeFences(content);
  const parts: string[] = [];
  const fenceRe = /```([\w-]*)\n?([\s\S]*?)```/g;
  let lastIndex = 0;
  let match: RegExpExecArray | null;

  while ((match = fenceRe.exec(normalized)) !== null) {
    const before = normalized.slice(lastIndex, match.index);
    if (before.trim()) {
      parts.push(wrapIfCode(before));
    }

    const lang = inferFenceLanguage(match[2], match[1].trim());
    const body = match[2].replace(/\n$/, "");
    parts.push(`${FENCE}${lang}\n${body}\n${FENCE}`);
    lastIndex = match.index + match[0].length;
  }

  const tail = normalized.slice(lastIndex);
  if (tail.trim()) {
    // Streaming: trailing ``` opens a fence — keep content inside until closed
    const openIdx = tail.indexOf(FENCE);
    if (openIdx >= 0 && streaming) {
      const beforeOpen = tail.slice(0, openIdx);
      if (beforeOpen.trim()) {
        parts.push(wrapIfCode(beforeOpen));
      }
      const openTail = tail.slice(openIdx + FENCE.length);
      const langMatch = /^([\w-]*)\n?/.exec(openTail);
      const lang = langMatch?.[1]?.trim() ?? "";
      const body = langMatch ? openTail.slice(langMatch[0].length) : openTail;
      const useLang = inferFenceLanguage(body, lang);
      parts.push(`${FENCE}${useLang}\n${body}`);
    } else {
      parts.push(wrapIfCode(tail));
    }
  }

  let result = parts.join("\n\n");

  const fenceCount = (result.match(/```/g) ?? []).length;
  if (streaming && fenceCount % 2 === 1) {
    result += `\n${FENCE}`;
  }

  return mergeAdjacentGdscriptFences(result);
}
