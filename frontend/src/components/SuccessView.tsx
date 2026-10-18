"use client";

import { CheckCircle2, ShieldCheck, ArrowRight, X } from "lucide-react";

interface SuccessViewProps {
  onReset: () => void;
  onClose?: () => void;
  categoryTag?: string;
}

export function SuccessView({ onReset, onClose, categoryTag }: SuccessViewProps) {
  return (
    <div className="flex flex-col items-center justify-center py-10 px-4 text-center space-y-6 animate-in fade-in zoom-in-95 duration-300">
      {/* Animated Icon Circle */}
      <div className="relative">
        <div className="w-20 h-20 rounded-full bg-emerald-500/10 border border-emerald-500/30 flex items-center justify-center text-emerald-400 shadow-xl shadow-emerald-500/10">
          <CheckCircle2 className="w-10 h-10 animate-bounce" />
        </div>
        <div className="absolute -bottom-1 -right-1 p-1 rounded-full bg-zinc-900 border border-emerald-500/40 text-emerald-300">
          <ShieldCheck className="w-4 h-4" />
        </div>
      </div>

      <div className="space-y-2 max-w-xs">
        <h2 className="text-xl font-bold text-white tracking-tight">
          Отправлено на модерацию!
        </h2>
        <p className="text-xs text-zinc-400 leading-relaxed">
          Твое сообщение{categoryTag ? ` в категорию ${categoryTag}` : ""} передано модераторам. После проверки пост появится в основном канале.
        </p>
      </div>

      {/* OpSec Assurance Card */}
      <div className="w-full max-w-xs p-3 rounded-2xl bg-white/5 border border-white/10 text-left space-y-1.5">
        <div className="text-[11px] font-semibold text-emerald-400 flex items-center gap-1.5">
          <ShieldCheck className="w-3.5 h-3.5" />
          Полная конфиденциальность
        </div>
        <p className="text-[10px] text-zinc-400 leading-normal">
          Твой Telegram ID был мгновенно захэширован в односторонний ключ. В базе нет твоего имени, юзернейма или IP.
        </p>
      </div>

      {/* Action Buttons */}
      <div className="w-full max-w-xs space-y-2 pt-2">
        <button
          type="button"
          onClick={onReset}
          className="w-full py-3 px-4 rounded-xl bg-gradient-to-r from-indigo-500 to-purple-600 hover:from-indigo-600 hover:to-purple-700 text-white text-xs font-semibold shadow-lg shadow-indigo-500/20 active:scale-98 transition-all flex items-center justify-center gap-2"
        >
          <span>Написать еще одно сообщение</span>
          <ArrowRight className="w-3.5 h-3.5" />
        </button>

        {onClose && (
          <button
            type="button"
            onClick={onClose}
            className="w-full py-2.5 px-4 rounded-xl bg-white/5 hover:bg-white/10 text-zinc-400 text-xs font-medium active:scale-98 transition-colors flex items-center justify-center gap-1.5"
          >
            <X className="w-3.5 h-3.5" />
            <span>Закрыть предложку</span>
          </button>
        )}
      </div>
    </div>
  );
}
