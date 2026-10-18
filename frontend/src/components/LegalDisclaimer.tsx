"use client";

import { useState } from "react";
import { Shield, ChevronDown, ChevronUp } from "lucide-react";

export function LegalDisclaimer() {
  const [isOpen, setIsOpen] = useState(false);

  return (
    <div className="rounded-xl border border-zinc-800/80 bg-zinc-900/40 overflow-hidden text-xs">
      <button
        type="button"
        onClick={() => setIsOpen(!isOpen)}
        className="w-full flex items-center justify-between px-3 py-2 text-zinc-400 hover:text-zinc-200 transition-colors"
      >
        <div className="flex items-center gap-2">
          <Shield className="w-3.5 h-3.5 text-zinc-400" />
          <span className="text-[11px] font-medium">Правила и анонимность (Закон РК)</span>
        </div>
        <div>
          {isOpen ? <ChevronUp className="w-3.5 h-3.5 text-zinc-500" /> : <ChevronDown className="w-3.5 h-3.5 text-zinc-500" />}
        </div>
      </button>

      {isOpen && (
        <div className="px-3 pb-3 pt-1 space-y-2 text-[11px] text-zinc-400 border-t border-zinc-800/60 leading-relaxed">
          <div>
            <span className="text-zinc-200 font-medium">Разрешено: </span>
            любое субъективное мнение, критика уроков и учителей, сарказм и личные оценки.
          </div>
          <div>
            <span className="text-zinc-200 font-medium">Запрещено: </span>
            слив контактов и ИИН (ст. 147 УК РК), клевета (ст. 73-3 КоАП) и нецензурные оскорбления (ст. 131 УК).
          </div>
          <div className="text-[10px] text-zinc-500 pt-0.5">
            100% анонимность: в базе нет твоего аккаунта или имени — только односторонний хэш.
          </div>
        </div>
      )}
    </div>
  );
}
