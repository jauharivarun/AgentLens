import { Fragment, type ReactNode } from "react";

function preprocess(text: string): string {
  return text
    .replace(/<think>[\s\S]*?<\/think>/gi, "")
    .replace(/<\/?think>/gi, "")
    .replace(/\r\n/g, "\n")
    .trim();
}

function isHr(line: string): boolean {
  return /^\s*([-*_])\1{2,}\s*$/.test(line);
}

function headingText(line: string): string | null {
  const match = line.match(/^\s{0,3}#{1,6}\s*(.*)$/);
  if (!match) return null;
  const text = match[1].replace(/\s+#+\s*$/, "").trim();
  return text || null;
}

function unorderedItem(line: string): string | null {
  const match = line.match(/^\s*[-*+]\s+(.*)$/);
  return match ? match[1] : null;
}

function orderedItem(line: string): { n: number; text: string } | null {
  const match = line.match(/^\s*(\d+)[.)]\s+(.*)$/);
  if (!match) return null;
  return { n: Number(match[1]), text: match[2] };
}

function nextContent(lines: string[], index: number): number {
  let cursor = index;
  while (cursor < lines.length && (!lines[cursor].trim() || isHr(lines[cursor]))) {
    cursor += 1;
  }
  return cursor;
}

function unwrapBold(text: string): string {
  const match = text.match(/^\*\*(.+)\*\*$/);
  return match ? match[1] : text;
}

function renderInline(text: string): ReactNode[] {
  const nodes: ReactNode[] = [];
  const pattern = /(`[^`]+`)|(\*\*[^*]+?\*\*)|(\*[^*\n]+?\*)|(_[^_\n]+?_)/g;
  let last = 0;
  let index = 0;
  let match: RegExpExecArray | null;
  while ((match = pattern.exec(text)) !== null) {
    if (match.index > last) {
      nodes.push(<Fragment key={`t-${index}`}>{cleanLeftover(text.slice(last, match.index))}</Fragment>);
    }
    const token = match[0];
    if (token.startsWith("`")) {
      nodes.push(
        <code key={`c-${index}`} className="rounded bg-black/30 px-1 py-0.5 font-mono text-[12px]">
          {token.slice(1, -1)}
        </code>,
      );
    } else if (token.startsWith("**")) {
      nodes.push(
        <strong key={`b-${index}`} className="font-semibold text-[var(--text)]">
          {token.slice(2, -2)}
        </strong>,
      );
    } else {
      nodes.push(
        <em key={`i-${index}`} className="italic">
          {token.slice(1, -1)}
        </em>,
      );
    }
    last = match.index + token.length;
    index += 1;
  }
  if (last < text.length) {
    nodes.push(<Fragment key="t-end">{cleanLeftover(text.slice(last))}</Fragment>);
  }
  return nodes;
}

function cleanLeftover(text: string): string {
  return text.replaceAll("**", "").replaceAll("__", "").replace(/(^|\s)#+\s?/g, "$1");
}

type Block =
  | { type: "heading"; text: string }
  | { type: "paragraph"; text: string }
  | { type: "ul"; items: string[] }
  | { type: "ol"; start: number; items: string[] }
  | { type: "section"; number: number; title: string; items: string[] }
  | { type: "code"; text: string };

function collectBullets(lines: string[], start: number): { items: string[]; next: number } {
  let index = start;
  const items: string[] = [];
  while (index < lines.length && unorderedItem(lines[index]) !== null) {
    items.push(unorderedItem(lines[index]) as string);
    index += 1;
  }
  return { items, next: index };
}

function parseBlocks(text: string): Block[] {
  const lines = preprocess(text).split("\n");
  const blocks: Block[] = [];
  let index = 0;
  while (index < lines.length) {
    const line = lines[index];
    if (!line.trim() || isHr(line)) {
      index += 1;
      continue;
    }
    if (line.trim().startsWith("```")) {
      index += 1;
      const code: string[] = [];
      while (index < lines.length && !lines[index].trim().startsWith("```")) {
        code.push(lines[index]);
        index += 1;
      }
      if (index < lines.length) index += 1;
      blocks.push({ type: "code", text: code.join("\n") });
      continue;
    }
    const heading = headingText(line);
    if (heading) {
      blocks.push({ type: "heading", text: heading });
      index += 1;
      continue;
    }
    if (unorderedItem(line) !== null) {
      const collected = collectBullets(lines, index);
      blocks.push({ type: "ul", items: collected.items });
      index = collected.next;
      continue;
    }
    const numbered = orderedItem(line);
    if (numbered) {
      const after = nextContent(lines, index + 1);
      const followedByBullets = after < lines.length && unorderedItem(lines[after]) !== null;
      if (followedByBullets) {
        const collected = collectBullets(lines, after);
        blocks.push({
          type: "section",
          number: numbered.n,
          title: unwrapBold(numbered.text),
          items: collected.items,
        });
        index = collected.next;
        continue;
      }
      const items: { n: number; text: string }[] = [];
      while (index < lines.length) {
        const item = orderedItem(lines[index]);
        if (!item) break;
        const nestedAt = nextContent(lines, index + 1);
        if (nestedAt < lines.length && unorderedItem(lines[nestedAt]) !== null) break;
        items.push(item);
        index += 1;
      }
      if (items.length) {
        blocks.push({
          type: "ol",
          start: items[0].n,
          items: items.map((item) => unwrapBold(item.text)),
        });
      }
      continue;
    }
    const parts: string[] = [line];
    index += 1;
    while (
      index < lines.length &&
      lines[index].trim() &&
      !isHr(lines[index]) &&
      !lines[index].trim().startsWith("```") &&
      !headingText(lines[index]) &&
      unorderedItem(lines[index]) === null &&
      orderedItem(lines[index]) === null
    ) {
      parts.push(lines[index]);
      index += 1;
    }
    blocks.push({ type: "paragraph", text: parts.join(" ") });
  }
  return renumberRepeatedSections(blocks);
}

function renumberRepeatedSections(blocks: Block[]): Block[] {
  const sections = blocks.filter((block): block is Extract<Block, { type: "section" }> => block.type === "section");
  if (sections.length < 2 || !sections.every((block) => block.number === 1)) return blocks;
  let next = 1;
  return blocks.map((block) => (block.type === "section" ? { ...block, number: next++ } : block));
}

export function MarkdownText({ text }: { text: string }) {
  const blocks = parseBlocks(text);
  if (!blocks.length) return null;
  return (
    <div className="space-y-2 text-sm leading-6">
      {blocks.map((block, index) => {
        if (block.type === "heading") {
          return (
            <p key={index} className="mt-3 font-semibold text-[var(--text)] first:mt-0">
              {renderInline(block.text)}
            </p>
          );
        }
        if (block.type === "section") {
          return (
            <div key={index} className="space-y-2">
              <p className="mt-3 font-semibold text-[var(--text)] first:mt-0">
                {block.number}. {renderInline(block.title)}
              </p>
              {block.items.length ? (
                <ul className="list-disc space-y-1 pl-5">
                  {block.items.map((item, itemIndex) => (
                    <li key={itemIndex}>{renderInline(item)}</li>
                  ))}
                </ul>
              ) : null}
            </div>
          );
        }
        if (block.type === "ul") {
          return (
            <ul key={index} className="list-disc space-y-1 pl-5">
              {block.items.map((item, itemIndex) => (
                <li key={itemIndex}>{renderInline(item)}</li>
              ))}
            </ul>
          );
        }
        if (block.type === "ol") {
          return (
            <ol key={index} start={block.start} className="list-decimal space-y-1 pl-5">
              {block.items.map((item, itemIndex) => (
                <li key={itemIndex}>{renderInline(item)}</li>
              ))}
            </ol>
          );
        }
        if (block.type === "code") {
          return (
            <pre key={index} className="overflow-x-auto rounded-lg bg-black/30 p-3 font-mono text-[12px] leading-5">
              {block.text}
            </pre>
          );
        }
        return <p key={index}>{renderInline(block.text)}</p>;
      })}
    </div>
  );
}
