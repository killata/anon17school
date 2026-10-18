"use client";

import { cn } from "@/lib/utils";

export interface CategoryOption {
  id: string;
  tag: string;
  backendValue: "Мнение" | "Учителя" | "Ищу тебя" | "Мем" | "Сплетня" | null;
}

export const CATEGORIES: CategoryOption[] = [
  { id: "none", tag: "Без тега", backendValue: null },
  { id: "opinion", tag: "#мнение", backendValue: "Мнение" },
  { id: "teachers", tag: "#учителя", backendValue: "Учителя" },
  { id: "crush", tag: "#краш", backendValue: "Ищу тебя" },
  { id: "meme", tag: "#мем", backendValue: "Мем" },
  { id: "gossip", tag: "#сплетня", backendValue: "Сплетня" },
];

interface CategoryChipsProps {
  selectedCategory: string | null;
  onSelect: (category: CategoryOption) => void;
}

export function CategoryChips({ selectedCategory, onSelect }: CategoryChipsProps) {
  return (
    <div className="flex items-center gap-1.5 overflow-x-auto no-scrollbar py-0.5">
      {CATEGORIES.map((cat) => {
        const isSelected = selectedCategory === cat.backendValue;
        return (
          <button
            key={cat.id}
            type="button"
            onClick={() => onSelect(cat)}
            className={cn(
              "px-3 py-1.5 rounded-full text-xs transition-colors whitespace-nowrap active:scale-95",
              isSelected
                ? "bg-white text-zinc-950 font-semibold shadow-sm"
                : "bg-zinc-900 text-zinc-400 hover:text-zinc-200 hover:bg-zinc-800/80 border border-zinc-800/80"
            )}
          >
            {cat.tag}
          </button>
        );
      })}
    </div>
  );
}
