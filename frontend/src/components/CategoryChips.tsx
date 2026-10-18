"use client";

import { cn } from "@/lib/utils";

export interface CategoryOption {
  id: string;
  label: string;
  tag: string;
  backendValue: "Мнение" | "Учителя" | "Ищу тебя" | "Мем" | "Сплетня";
  emoji: string;
  gradient: string;
}

export const CATEGORIES: CategoryOption[] = [
  {
    id: "opinion",
    label: "Мнение",
    tag: "#мнение",
    backendValue: "Мнение",
    emoji: "💬",
    gradient: "from-blue-500 to-indigo-600",
  },
  {
    id: "teachers",
    label: "Учителя",
    tag: "#учителя",
    backendValue: "Учителя",
    emoji: "👨‍🏫",
    gradient: "from-amber-500 to-orange-600",
  },
  {
    id: "crush",
    label: "Краш",
    tag: "#краш",
    backendValue: "Ищу тебя",
    emoji: "💌",
    gradient: "from-pink-500 to-rose-600",
  },
  {
    id: "meme",
    label: "Мем",
    tag: "#мем",
    backendValue: "Мем",
    emoji: "🎭",
    gradient: "from-violet-500 to-purple-600",
  },
  {
    id: "gossip",
    label: "Сплетня",
    tag: "#сплетня",
    backendValue: "Сплетня",
    emoji: "👀",
    gradient: "from-emerald-500 to-teal-600",
  },
];

interface CategoryChipsProps {
  selectedCategory: string;
  onSelect: (category: CategoryOption) => void;
}

export function CategoryChips({ selectedCategory, onSelect }: CategoryChipsProps) {
  return (
    <div className="space-y-1.5">
      <label className="text-xs font-medium text-zinc-300 flex items-center justify-between">
        <span>Категория сообщения:</span>
        <span className="text-[11px] text-zinc-500 font-normal">Выбери тег</span>
      </label>
      <div className="flex flex-wrap gap-2">
        {CATEGORIES.map((cat) => {
          const isSelected = selectedCategory === cat.backendValue;
          return (
            <button
              key={cat.id}
              type="button"
              onClick={() => onSelect(cat)}
              className={cn(
                "flex items-center gap-1.5 px-3 py-1.5 rounded-full text-xs font-medium transition-all duration-150 active:scale-95",
                isSelected
                  ? `bg-gradient-to-r ${cat.gradient} text-white shadow-lg shadow-indigo-500/20 ring-2 ring-white/30 scale-100`
                  : "bg-white/5 hover:bg-white/10 text-zinc-300 border border-white/10"
              )}
            >
              <span>{cat.emoji}</span>
              <span>{cat.tag}</span>
            </button>
          );
        })}
      </div>
    </div>
  );
}
