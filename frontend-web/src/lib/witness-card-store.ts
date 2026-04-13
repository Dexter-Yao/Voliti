// ABOUTME: Witness Card 本地存储，localStorage 缓存最近 20 张
// ABOUTME: A2UI image 组件产出的卡片图片存入此处供回看

const STORAGE_KEY = "voliti_witness_cards";

export interface WitnessCard {
  id: string;
  src: string;
  alt: string;
  createdAt: string;
}

export function getWitnessCards(): WitnessCard[] {
  if (typeof window === "undefined") return [];
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    return raw ? (JSON.parse(raw) as WitnessCard[]) : [];
  } catch {
    return [];
  }
}

