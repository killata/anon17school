"use client";

import { useState } from "react";
import { ShieldCheck, ChevronDown, ChevronUp, AlertCircle, CheckCircle2, Lock } from "lucide-react";

export function LegalDisclaimer() {
  const [isOpen, setIsOpen] = useState(false);

  return (
    <div className="rounded-2xl border border-white/10 bg-white/5 backdrop-blur-md overflow-hidden transition-all duration-200">
      <button
        type="button"
        onClick={() => setIsOpen(!isOpen)}
        className="w-full flex items-center justify-between p-3.5 text-left hover:bg-white/5 transition-colors"
      >
        <div className="flex items-center gap-2.5">
          <div className="p-1.5 rounded-lg bg-emerald-500/10 text-emerald-400">
            <ShieldCheck className="w-4 h-4" />
          </div>
          <div>
            <div className="text-xs font-semibold text-white tracking-wide flex items-center gap-1.5">
              Свобода слова & Закон РК
              <span className="text-[10px] px-1.5 py-0.5 rounded-full bg-emerald-500/20 text-emerald-300 font-medium">
                100% Анонимно
              </span>
            </div>
            <p className="text-[11px] text-zinc-400">
              Короткий чек-лист того, что разрешено и запрещено
            </p>
          </div>
        </div>
        <div className="text-zinc-400">
          {isOpen ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
        </div>
      </button>

      {isOpen && (
        <div className="px-3.5 pb-3.5 pt-1 space-y-3 text-xs border-t border-white/5">
          {/* Разрешено */}
          <div className="p-2.5 rounded-xl bg-emerald-950/30 border border-emerald-500/20">
            <div className="flex items-center gap-1.5 text-emerald-400 font-semibold mb-1">
              <CheckCircle2 className="w-3.5 h-3.5" />
              <span>Разрешено (Свобода мнений):</span>
            </div>
            <p className="text-[11px] text-zinc-300 leading-relaxed">
              Любое <b>субъективное мнение</b>, критика преподавания, сарказм, школьные мемы, романтические признания и личные оценки. Оценочные суждения не являются нарушением закона.
            </p>
          </div>

          {/* Запрещено */}
          <div className="p-2.5 rounded-xl bg-rose-950/30 border border-rose-500/20">
            <div className="flex items-center gap-1.5 text-rose-400 font-semibold mb-1">
              <AlertCircle className="w-3.5 h-3.5" />
              <span>Запрещено законодательством РК:</span>
            </div>
            <ul className="text-[11px] text-zinc-300 space-y-1 list-disc list-inside">
              <li>
                <b>Слив личных данных:</b> номера телефонов, адреса, ИИН (ст. 147 УК РК).
              </li>
              <li>
                <b>Клевета:</b> ложные утверждения о совершении преступлений (ст. 73-3 КоАП РК).
              </li>
              <li>
                <b>Оскорбления:</b> нецензурное унижение конкретных лиц (ст. 131 УК РК).
              </li>
              <li>
                <b>Травля & буллинг:</b> травля несовершеннолетних (ст. 127-2 КоАП РК).
              </li>
            </ul>
          </div>

          {/* Гарантия безопасности */}
          <div className="flex items-center gap-2 text-[10px] text-zinc-400 pt-1">
            <Lock className="w-3 h-3 text-zinc-500 flex-shrink-0" />
            <span>
              Даже если базу запросят, в ней <b>нет</b> твоего Telegram ID — только односторонний хэш.
            </span>
          </div>
        </div>
      )}
    </div>
  );
}
