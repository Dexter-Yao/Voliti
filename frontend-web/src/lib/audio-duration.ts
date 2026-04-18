// ABOUTME: 服务端音频时长提取
// ABOUTME: 基于音频文件本身调用 ffprobe 计算权威录音时长，并在失败时返回空值

import { execFile } from "node:child_process";
import { mkdtemp, rm, writeFile } from "node:fs/promises";
import { tmpdir } from "node:os";
import { extname, join } from "node:path";
import { promisify } from "node:util";

const execFileAsync = promisify(execFile);
type FfprobeExecutor = (filePath: string) => Promise<string>;

function inferAudioExtension(file: File): string {
  const nameExtension = extname(file.name);
  if (nameExtension) return nameExtension;

  switch (file.type) {
    case "audio/wav":
    case "audio/x-wav":
      return ".wav";
    case "audio/mp4":
      return ".mp4";
    case "audio/mpeg":
    case "audio/mp3":
    case "audio/mpga":
      return ".mp3";
    case "audio/ogg":
    case "audio/ogg;codecs=opus":
      return ".ogg";
    default:
      return ".webm";
  }
}

export function parseFfprobeDurationMs(rawValue: string): number | null {
  const parsed = Number.parseFloat(rawValue.trim());
  if (!Number.isFinite(parsed) || parsed < 0) {
    return null;
  }
  return Math.round(parsed * 1000);
}

async function runFfprobeDuration(filePath: string): Promise<string> {
  const { stdout } = await execFileAsync("ffprobe", [
    "-v",
    "error",
    "-show_entries",
    "format=duration",
    "-of",
    "default=noprint_wrappers=1:nokey=1",
    filePath,
  ]);

  return stdout;
}

export async function detectAudioDurationMs(
  file: File,
  runFfprobe: FfprobeExecutor = runFfprobeDuration,
): Promise<number | null> {
  const tempDirectory = await mkdtemp(join(tmpdir(), "voliti-voice-"));
  const tempPath = join(tempDirectory, `recording${inferAudioExtension(file)}`);

  try {
    const buffer = Buffer.from(await file.arrayBuffer());
    await writeFile(tempPath, buffer);
    const stdout = await runFfprobe(tempPath);
    return parseFfprobeDurationMs(stdout);
  } catch {
    return null;
  } finally {
    await rm(tempDirectory, { recursive: true, force: true });
  }
}
