// ABOUTME: Witness Card 本地存储，localStorage 缓存最近 20 张
// ABOUTME: A2UI image 组件产出的卡片图片存入此处供回看

const STORAGE_KEY = "voliti_witness_cards";
const MAX_CARDS = 20;

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

export function addWitnessCard(card: Omit<WitnessCard, "id" | "createdAt">): void {
  const cards = getWitnessCards();
  const newCard: WitnessCard = {
    id: `wc_${Date.now()}`,
    src: card.src,
    alt: card.alt,
    createdAt: new Date().toISOString(),
  };
  cards.unshift(newCard);
  // Keep only the most recent cards
  const trimmed = cards.slice(0, MAX_CARDS);
  localStorage.setItem(STORAGE_KEY, JSON.stringify(trimmed));
}

export function clearWitnessCards(): void {
  localStorage.removeItem(STORAGE_KEY);
}
