"use client";

import { useState, useEffect, useRef } from "react";
import Image from "next/image";
import { Paperclip, X, EyeOff, Loader2 } from "lucide-react";
import { useTelegram } from "@/hooks/useTelegram";
import { CategoryChips, CATEGORIES, CategoryOption } from "@/components/CategoryChips";
import { LegalDisclaimer } from "@/components/LegalDisclaimer";
import { SuccessView } from "@/components/SuccessView";

const MAX_CHARS = 2000;

export function PostForm() {
  const {
    webApp,
    initDataRaw,
    triggerHaptic,
    triggerNotificationHaptic,
    setMainButton,
    hideMainButton,
  } = useTelegram();

  const [category, setCategory] = useState<CategoryOption>(CATEGORIES[0]);
  const [content, setContent] = useState("");
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);
  const [isSpoiler, setIsSpoiler] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [isSuccess, setIsSuccess] = useState(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  const fileInputRef = useRef<HTMLInputElement>(null);
  const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";

  useEffect(() => {
    return () => {
      if (previewUrl) URL.revokeObjectURL(previewUrl);
    };
  }, [previewUrl]);

  // Synchronize native Telegram MainButton
  useEffect(() => {
    if (isSuccess) {
      hideMainButton();
      return;
    }

    const canSubmit = content.trim().length >= 3 && !isSubmitting;

    setMainButton({
      text: isSubmitting ? "Отправка..." : "Отправить анонимно",
      isVisible: canSubmit,
      isActive: canSubmit,
      isLoading: isSubmitting,
      onClick: handleSubmit,
    });

    return () => {
      hideMainButton();
    };
  }, [content, isSubmitting, isSuccess, category, selectedFile, isSpoiler]);

  const handleCategorySelect = (cat: CategoryOption) => {
    triggerHaptic("light");
    setCategory(cat);
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    if (!file.type.startsWith("image/")) {
      setErrorMsg("Поддерживаются только фотографии");
      triggerNotificationHaptic("error");
      return;
    }

    if (file.size > 10 * 1024 * 1024) {
      setErrorMsg("Максимальный размер фото — 10 МБ");
      triggerNotificationHaptic("error");
      return;
    }

    triggerHaptic("light");
    setSelectedFile(file);
    setErrorMsg(null);
    setPreviewUrl(URL.createObjectURL(file));
  };

  const removePhoto = () => {
    triggerHaptic("light");
    setSelectedFile(null);
    if (previewUrl) URL.revokeObjectURL(previewUrl);
    setPreviewUrl(null);
    setIsSpoiler(false);
    if (fileInputRef.current) fileInputRef.current.value = "";
  };

  const handleSubmit = async () => {
    if (content.trim().length < 3) {
      setErrorMsg("Минимум 3 символа");
      triggerNotificationHaptic("error");
      return;
    }

    triggerHaptic("medium");
    setIsSubmitting(true);
    setErrorMsg(null);

    try {
      const authHeader = initDataRaw
        ? `tma ${initDataRaw}`
        : "tma demo_dev_session";

      let mediaFileId: string | undefined = undefined;

      if (selectedFile) {
        const formData = new FormData();
        formData.append("file", selectedFile);

        const uploadRes = await fetch(`${apiUrl}/posts/upload-media`, {
          method: "POST",
          headers: { Authorization: authHeader },
          body: formData,
        });

        if (!uploadRes.ok) {
          const errData = await uploadRes.json().catch(() => ({}));
          throw new Error(errData.detail || "Ошибка загрузки фото");
        }

        const uploadData = await uploadRes.json();
        mediaFileId = uploadData.file_id;
      }

      const submitRes = await fetch(`${apiUrl}/posts/submit`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: authHeader,
        },
        body: JSON.stringify({
          content: content.trim(),
          category: category.backendValue,
          media_file_id: mediaFileId,
        }),
      });

      if (!submitRes.ok) {
        const errData = await submitRes.json().catch(() => ({}));
        throw new Error(errData.detail || `Ошибка сервера: ${submitRes.status}`);
      }

      triggerNotificationHaptic("success");
      setIsSuccess(true);
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : "Произошла ошибка";
      setErrorMsg(message);
      triggerNotificationHaptic("error");
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleReset = () => {
    triggerHaptic("light");
    setContent("");
    removePhoto();
    setIsSuccess(false);
    setErrorMsg(null);
  };

  if (isSuccess) {
    return (
      <SuccessView
        categoryTag={category.tag}
        onReset={handleReset}
        onClose={() => webApp?.close()}
      />
    );
  }

  return (
    <div className="space-y-3 pb-16">
      {/* Header */}
      <div className="flex items-center justify-between pt-1">
        <div>
          <h1 className="text-base font-semibold text-zinc-100 tracking-tight">
            Анонимка 17
          </h1>
          <p className="text-[11px] text-zinc-500">
            Предложка гимназии
          </p>
        </div>
        <span className="text-[10px] text-zinc-500 font-mono">
          100% anon
        </span>
      </div>

      {/* Legal Rules */}
      <LegalDisclaimer />

      {/* Category selector */}
      <div className="space-y-1">
        <CategoryChips
          selectedCategory={category.backendValue}
          onSelect={handleCategorySelect}
        />
      </div>

      {/* Textarea */}
      <div className="space-y-1">
        <div className="relative rounded-xl bg-zinc-900/60 border border-zinc-800 focus-within:border-zinc-600 transition-colors">
          <textarea
            value={content}
            onChange={(e) => setContent(e.target.value)}
            placeholder="Напиши всё, что думаешь..."
            rows={6}
            maxLength={MAX_CHARS}
            className="w-full bg-transparent p-3 text-xs text-zinc-100 placeholder-zinc-500 focus:outline-none resize-none leading-relaxed"
          />
          <div className="flex items-center justify-between px-3 py-1.5 border-t border-zinc-800/40 text-[10px] text-zinc-500">
            <span>{category.tag}</span>
            <span className={content.length >= MAX_CHARS ? "text-rose-400 font-semibold" : ""}>
              {content.length}/{MAX_CHARS}
            </span>
          </div>
        </div>
      </div>

      {/* Attach Media */}
      <div>
        <input
          type="file"
          ref={fileInputRef}
          onChange={handleFileChange}
          accept="image/*"
          className="hidden"
        />

        {!selectedFile ? (
          <button
            type="button"
            onClick={() => {
              triggerHaptic("light");
              fileInputRef.current?.click();
            }}
            className="flex items-center gap-1.5 text-[11px] text-zinc-400 hover:text-zinc-200 transition-colors py-1 px-1"
          >
            <Paperclip className="w-3.5 h-3.5" />
            <span>Прикрепить фото (без метаданных)</span>
          </button>
        ) : (
          <div className="rounded-xl bg-zinc-900/60 border border-zinc-800 p-2.5 flex items-center justify-between gap-3">
            <div className="flex items-center gap-2.5 min-w-0">
              {previewUrl && (
                <div className="relative w-10 h-10 rounded-lg overflow-hidden flex-shrink-0 bg-black/40 border border-zinc-700/60">
                  <Image
                    src={previewUrl}
                    alt="preview"
                    fill
                    unoptimized
                    className={`object-cover ${isSpoiler ? "blur-sm" : ""}`}
                  />
                </div>
              )}
              <div className="min-w-0">
                <p className="text-[11px] text-zinc-200 truncate">
                  {selectedFile.name}
                </p>
                <button
                  type="button"
                  onClick={() => setIsSpoiler(!isSpoiler)}
                  className="flex items-center gap-1 text-[10px] text-zinc-400 hover:text-zinc-200"
                >
                  <EyeOff className="w-3 h-3 text-zinc-400" />
                  <span>{isSpoiler ? "Спойлер включен" : "Скрыть спойлером"}</span>
                </button>
              </div>
            </div>

            <button
              type="button"
              onClick={removePhoto}
              className="p-1 rounded-md text-zinc-400 hover:text-rose-400 hover:bg-zinc-800 transition-colors"
            >
              <X className="w-4 h-4" />
            </button>
          </div>
        )}
      </div>

      {/* Error alert */}
      {errorMsg && (
        <div className="p-2.5 rounded-lg bg-rose-950/40 border border-rose-900 text-rose-300 text-[11px]">
          {errorMsg}
        </div>
      )}

      {/* In-page action button */}
      <div className="pt-1">
        <button
          type="button"
          onClick={handleSubmit}
          disabled={content.trim().length < 3 || isSubmitting}
          className="w-full py-2.5 px-4 rounded-xl bg-white hover:bg-zinc-200 disabled:opacity-30 disabled:cursor-not-allowed text-zinc-950 text-xs font-semibold active:scale-98 transition-all flex items-center justify-center gap-2"
        >
          {isSubmitting ? (
            <>
              <Loader2 className="w-3.5 h-3.5 animate-spin" />
              <span>Отправка...</span>
            </>
          ) : (
            <span>Отправить анонимно</span>
          )}
        </button>
      </div>
    </div>
  );
}
