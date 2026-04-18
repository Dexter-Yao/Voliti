// ABOUTME: Intervention Layout 槽位分派纯函数测试
// ABOUTME: 覆盖 findFirstByKind / splitFirstTextAsAnchor / findVerdictTextAfterProto / isIfThenText

import { describe, it, expect } from "vitest";
import type { Component } from "@/lib/a2ui";
import {
  findFirstByKind,
  splitFirstTextAsAnchor,
  findVerdictTextAfterProto,
  isIfThenText,
} from "./slot-mapping";

// ---------------------------------------------------------------------------
// Fixtures
// ---------------------------------------------------------------------------

const memoryText: Component = { kind: "text", text: "你说过：我想变清晰。" };
const verdictText: Component = { kind: "text", text: "这句话其实在说……" };
const anotherText: Component = { kind: "text", text: "附加说明" };

const proto: Component = {
  kind: "protocol_prompt",
  observation: "你刚说了一句",
  question: "你签下了这个等号吗？",
};

const textInput: Component = {
  kind: "text_input",
  key: "reply",
  label: "你的回应",
  placeholder: "",
  value: "",
};

const select: Component = {
  kind: "select",
  key: "pick",
  label: "还有一些读法",
  options: [
    { label: "一次 = 一次", value: "once" },
    { label: "一次 = 一个信息", value: "info" },
  ],
  value: "",
};

// ---------------------------------------------------------------------------
// findFirstByKind
// ---------------------------------------------------------------------------

describe("findFirstByKind", () => {
  it("returns the first component matching the kind", () => {
    const result = findFirstByKind(
      [memoryText, proto, textInput],
      "protocol_prompt",
    );
    expect(result).toBe(proto);
  });

  it("returns only the first when multiple match", () => {
    const result = findFirstByKind([memoryText, verdictText, proto], "text");
    expect(result).toBe(memoryText);
  });

  it("returns undefined when no component matches", () => {
    const result = findFirstByKind([memoryText, textInput], "image");
    expect(result).toBeUndefined();
  });

  it("returns undefined for an empty component list", () => {
    const result = findFirstByKind([], "text");
    expect(result).toBeUndefined();
  });

  it("narrows the return type so callers can access kind-specific fields", () => {
    const result = findFirstByKind([proto, textInput], "text_input");
    // Type narrowing: result?.key is accessible without extra cast
    expect(result?.key).toBe("reply");
  });
});

// ---------------------------------------------------------------------------
// splitFirstTextAsAnchor
// ---------------------------------------------------------------------------

describe("splitFirstTextAsAnchor", () => {
  it("promotes the first TextComponent to the anchor slot", () => {
    const { anchor, rest } = splitFirstTextAsAnchor([
      memoryText,
      proto,
      textInput,
    ]);
    expect(anchor).toBe(memoryText);
    expect(rest).toEqual([proto, textInput]);
  });

  it("leaves anchor as null when the first component is not text", () => {
    const { anchor, rest } = splitFirstTextAsAnchor([proto, memoryText]);
    expect(anchor).toBeNull();
    expect(rest).toEqual([proto, memoryText]);
  });

  it("handles empty components gracefully", () => {
    const { anchor, rest } = splitFirstTextAsAnchor([]);
    expect(anchor).toBeNull();
    expect(rest).toEqual([]);
  });

  it("only splits the first component, not subsequent text entries", () => {
    // Scenario: scene anchor + later inline text should not be merged
    const { anchor, rest } = splitFirstTextAsAnchor([
      memoryText,
      verdictText,
      anotherText,
    ]);
    expect(anchor).toBe(memoryText);
    expect(rest).toEqual([verdictText, anotherText]);
  });
});

// ---------------------------------------------------------------------------
// findVerdictTextAfterProto
// ---------------------------------------------------------------------------

describe("findVerdictTextAfterProto", () => {
  it("returns the first TextComponent after ProtocolPrompt", () => {
    const result = findVerdictTextAfterProto([proto, verdictText, textInput]);
    expect(result).toBe(verdictText);
  });

  it("ignores text components that appear before ProtocolPrompt", () => {
    const result = findVerdictTextAfterProto([memoryText, proto, verdictText]);
    expect(result).toBe(verdictText);
  });

  it("returns undefined when ProtocolPrompt has no trailing text", () => {
    const result = findVerdictTextAfterProto([memoryText, proto, textInput]);
    expect(result).toBeUndefined();
  });

  it("returns undefined when no ProtocolPrompt is present", () => {
    const result = findVerdictTextAfterProto([memoryText, verdictText]);
    expect(result).toBeUndefined();
  });

  it("returns undefined for empty components", () => {
    const result = findVerdictTextAfterProto([]);
    expect(result).toBeUndefined();
  });

  it("picks the first eligible text even with multiple trailing texts", () => {
    const result = findVerdictTextAfterProto([
      proto,
      verdictText,
      anotherText,
    ]);
    expect(result).toBe(verdictText);
  });
});

// ---------------------------------------------------------------------------
// isIfThenText
// ---------------------------------------------------------------------------

describe("isIfThenText", () => {
  it("matches canonical IF ... → THEN ... pattern", () => {
    expect(isIfThenText("IF 胸口发紧 → THEN 放下酒杯")).toBe(true);
  });

  it("matches pattern with trailing question mark (open-ended THEN)", () => {
    expect(isIfThenText("IF 胸口发紧 → THEN ?")).toBe(true);
  });

  it("requires leading IF token", () => {
    expect(isIfThenText("if foo → THEN bar")).toBe(false);
  });

  it("requires the → THEN separator with space", () => {
    expect(isIfThenText("IF foo THEN bar")).toBe(false);
    expect(isIfThenText("IF foo→THEN bar")).toBe(false);
  });

  it("non-matching regular text falls through", () => {
    expect(isIfThenText("今晚聚餐你先吃饱")).toBe(false);
    expect(isIfThenText("")).toBe(false);
  });
});

// ---------------------------------------------------------------------------
// Zero-parse contract: functions operate on component kind + structure only
// ---------------------------------------------------------------------------

describe("zero-parse contract", () => {
  it("findVerdictTextAfterProto does not inspect text content", () => {
    // Even if the text looks like a question or contains special chars,
    // it is always picked as the verdict slot when positioned after proto.
    const weirdText: Component = {
      kind: "text",
      text: "?\n= nothing == anything",
    };
    const result = findVerdictTextAfterProto([proto, weirdText]);
    expect(result).toBe(weirdText);
  });

  it("splitFirstTextAsAnchor does not inspect text content", () => {
    // Any TextComponent, regardless of its text content, is eligible as anchor.
    const oddText: Component = { kind: "text", text: "" };
    const { anchor } = splitFirstTextAsAnchor([oddText, proto]);
    expect(anchor).toBe(oddText);
  });
});

// ---------------------------------------------------------------------------
// Presence smoke tests: select and input slots co-exist cleanly in Reframing
// ---------------------------------------------------------------------------

describe("Reframing slot presence", () => {
  it("findFirstByKind returns select and text_input independently", () => {
    const components: Component[] = [proto, verdictText, select, textInput];
    expect(findFirstByKind(components, "select")).toBe(select);
    expect(findFirstByKind(components, "text_input")).toBe(textInput);
  });

  it("handles missing verdict gracefully (frontend falls back to placeholder)", () => {
    // Coach may fail to send the second TextComponent; verdict slot should
    // return undefined and the Layout's UI handles the fallback.
    const components: Component[] = [proto, select, textInput];
    expect(findVerdictTextAfterProto(components)).toBeUndefined();
  });
});
