"use client";

import { Check, X } from "lucide-react";

interface SuccessViewProps {
  onReset: () => void;
  onClose?: () => void;
  categoryTag?: string;
}

export function SuccessView({ onReset, onClose, categoryTag }: SuccessViewProps) {
  return (
    <div className="flex flex-col items-center justify-center py-16 px-4 text-center space-y-5 animate-in fade-in duration-200">
      <div className="w-12 h-12 rounded-full bg-zinc-900 border border-zinc-700/80 flex items-center justify-center text-zinc-100">
        <Check className="w-6 h-6 stroke-[2.5]" />
      </div>

      <div className="space-y-1.5 max-w-xs">
        <h2 className="text-base font-semibold text-zinc-100">
          Сообщение отправлено
        </h2>
        <p className="text-xs text-zinc-400 leading-relaxed">
          Пост{categoryTag ? ` ${categoryTag}` : ""} передан модераторам и появится в канале после проверки.
        </p>
      </div>

      <p className="text-[10px] text-zinc-500 font-mono">
        100% анонимно • id не сохранен
      </p>

      <div className="w-full max-w-xs space-y-2 pt-4">
        <button
          type="button"
          onClick={onReset}
          className="w-full py-2.5 px-4 rounded-xl bg-white hover:bg-zinc-200 text-zinc-950 text-xs font-semibold active:scale-98 transition-colors"
        >
          Написать ещё
        </button>

        {onClose && (
          <button
            type="button"
            onClick={onClose}
            className="w-full py-2 px-4 rounded-xl text-zinc-500 hover:text-zinc-300 text-xs transition-colors flex items-center justify-center gap-1"
          >
            <X className="w-3.5 h-3.5" />
            <span>Закрыть</span>
          </button>
        )}
      </div>
    </div>
  );
}
