import { useCallback, useEffect, useRef } from "react";

const NEAR_BOTTOM_PX = 100;
const STREAM_SCROLL_MS = 150;

/**
 * Keeps the chat pinned to the bottom only when the user is already near the bottom.
 * Uses instant scroll during streaming (throttled) to avoid smooth-scroll jitter.
 */
export function useChatScroll(messageCount: number, streamingContentLength: number, isStreaming: boolean) {
  const containerRef = useRef<HTMLDivElement>(null);
  const pinnedRef = useRef(true);
  const lastScrollAtRef = useRef(0);

  const isNearBottom = useCallback((el: HTMLElement) => {
    return el.scrollHeight - el.scrollTop - el.clientHeight <= NEAR_BOTTOM_PX;
  }, []);

  const scrollToBottom = useCallback((behavior: ScrollBehavior = "auto") => {
    const el = containerRef.current;
    if (!el || !pinnedRef.current) return;

    const now = performance.now();
    if (behavior === "auto" && now - lastScrollAtRef.current < STREAM_SCROLL_MS) {
      return;
    }
    lastScrollAtRef.current = now;
    el.scrollTo({ top: el.scrollHeight, behavior });
  }, []);

  useEffect(() => {
    const el = containerRef.current;
    if (!el) return;

    const onScroll = () => {
      pinnedRef.current = isNearBottom(el);
    };

    el.addEventListener("scroll", onScroll, { passive: true });
    return () => el.removeEventListener("scroll", onScroll);
  }, [isNearBottom]);

  // New message row added — pin and scroll once smoothly.
  useEffect(() => {
    pinnedRef.current = true;
    const el = containerRef.current;
    if (!el) return;
    lastScrollAtRef.current = performance.now();
    el.scrollTo({ top: el.scrollHeight, behavior: "smooth" });
  }, [messageCount]);

  // Streaming text growth — instant, throttled, only if pinned.
  useEffect(() => {
    if (!isStreaming) return;
    scrollToBottom("auto");
  }, [streamingContentLength, isStreaming, scrollToBottom]);

  const pinToBottom = useCallback(() => {
    pinnedRef.current = true;
    scrollToBottom("auto");
  }, [scrollToBottom]);

  return { containerRef, pinToBottom };
}
