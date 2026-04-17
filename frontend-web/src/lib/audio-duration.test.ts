// ABOUTME: 音频时长提取测试
// ABOUTME: 校验 ffprobe 输出解析与服务端权威时长计算边界

import { describe, expect, it } from "vitest";

import {
  detectAudioDurationMs,
  parseFfprobeDurationMs,
} from "./audio-duration";

function createWavFile(durationMs: number): File {
  const sampleRate = 16000;
  const channelCount = 1;
  const bitsPerSample = 16;
  const byteRate = sampleRate * channelCount * (bitsPerSample / 8);
  const blockAlign = channelCount * (bitsPerSample / 8);
  const sampleCount = Math.round((sampleRate * durationMs) / 1000);
  const dataSize = sampleCount * blockAlign;
  const buffer = new ArrayBuffer(44 + dataSize);
  const view = new DataView(buffer);

  const writeAscii = (offset: number, value: string) => {
    for (let index = 0; index < value.length; index += 1) {
      view.setUint8(offset + index, value.charCodeAt(index));
    }
  };

  writeAscii(0, "RIFF");
  view.setUint32(4, 36 + dataSize, true);
  writeAscii(8, "WAVE");
  writeAscii(12, "fmt ");
  view.setUint32(16, 16, true);
  view.setUint16(20, 1, true);
  view.setUint16(22, channelCount, true);
  view.setUint32(24, sampleRate, true);
  view.setUint32(28, byteRate, true);
  view.setUint16(32, blockAlign, true);
  view.setUint16(34, bitsPerSample, true);
  writeAscii(36, "data");
  view.setUint32(40, dataSize, true);

  return new File([buffer], "voice-test.wav", { type: "audio/wav" });
}

describe("audio duration helpers", () => {
  it("parses ffprobe duration text into rounded milliseconds", () => {
    expect(parseFfprobeDurationMs("1.234500\n")).toBe(1235);
  });

  it("returns null when ffprobe output is not a number", () => {
    expect(parseFfprobeDurationMs("not-a-number")).toBeNull();
  });

  it("detects audio duration from the uploaded file itself", async () => {
    const durationMs = await detectAudioDurationMs(createWavFile(1000));

    expect(durationMs).not.toBeNull();
    expect(durationMs).toBeGreaterThanOrEqual(950);
    expect(durationMs).toBeLessThanOrEqual(1050);
  });
});
