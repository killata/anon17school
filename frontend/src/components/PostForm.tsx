"use client";

import { useState, useEffect, useRef } from "react";
import Image from "next/image";
import { ImagePlus, X, EyeOff, Send, Loader2, Sparkles, AlertCircle } from "lucide-react";
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

  // Cleanup object URL
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
      setErrorMsg("Размер фото не должен превышать 10 МБ");
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
      setErrorMsg("Текст сообщения слишком короткий (минимум 3 символа)");
      triggerNotificationHaptic("error");
      return;
    }

    if (content.length > MAX_CHARS) {
      setErrorMsg(`Текст превышает лимит в ${MAX_CHARS} символов`);
      triggerNotificationHaptic("error");
      return;
    }

    // Trigger medium vibration when clicking Send
    triggerHaptic("medium");
    setIsSubmitting(true);
    setErrorMsg(null);

    try {
      const authHeader = initDataRaw
        ? `tma ${initDataRaw}`
        : "tma demo_dev_session";

      let mediaFileId: string | undefined = undefined;

      // 1. Upload photo if selected
      if (selectedFile) {
        const formData = new FormData();
        formData.append("file", selectedFile);

        const uploadRes = await fetch(`${apiUrl}/posts/upload-media`, {
          method: "POST",
          headers: {
            Authorization: authHeader,
          },
          body: formData,
        });

        if (!uploadRes.ok) {
          const errData = await uploadRes.json().catch(() => ({}));
          throw new Error(errData.detail || "Не удалось загрузить и очистить фото");
        }

        const uploadData = await uploadRes.json();
        mediaFileId = uploadData.file_id;
      }

      // 2. Submit anonymous post
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
      const message = err instanceof Error ? err.message : "Произошла неизвестная ошибка";
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
    <div className="space-y-4 pb-20">
      {/* Header Banner */}
      <div className="flex items-center justify-between pt-1">
        <div>
          <h1 className="text-lg font-bold text-white flex items-center gap-1.5">
            <span>Анонимная предложка</span>
            <Sparkles className="w-4 h-4 text-amber-400" />
          </h1>
          <p className="text-[11px] text-zinc-400">
            17 гимназия • Полная свобода без цензуры
          </p>
        </div>
        <div className="text-[10px] px-2 py-1 rounded-full bg-white/10 text-zinc-300 font-mono">
          ID: Защищен
        </div>
      </div>

      {/* Accordion Disclaimer */}
      <LegalDisclaimer />

      {/* Category Chips */}
      <CategoryChips
        selectedCategory={category.backendValue}
        onSelect={handleCategorySelect}
      />

      {/* Main Text Input */}
      <div className="space-y-1.5">
        <label className="text-xs font-medium text-zinc-300 flex items-center justify-between">
          <span>Текст сообщения:</span>
          <span
            className={`text-[11px] font-mono ${
              content.length > MAX_CHARS ? "text-rose-400 font-bold" : "text-zinc-500"
            }`}
          >
            {content.length}/{MAX_CHARS}
          </span>
        </label>
        <div className="relative">
          <textarea
            value={content}
            onChange={(e) => setContent(e.target.value)}
            placeholder="Поделись признанием, мнением об уроке, историей или мемом..."
            rows={5}
            maxLength={MAX_CHARS}
            className="w-full rounded-2xl bg-white/5 border border-white/10 p-3.5 text-xs text-white placeholder-zinc-500 focus:outline-none focus:ring-2 focus:ring-indigo-500/50 focus:border-indigo-500/50 resize-none transition-all leading-relaxed"
          />
        </div>
      </div>

      {/* Media Attachment & Spoiler Toggle */}
      <div className="space-y-2">
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
            className="w-full py-2.5 px-3 rounded-xl border border-dashed border-white/20 bg-white/[0.02] hover:bg-white/5 text-zinc-400 text-xs font-medium flex items-center justify-center gap-2 transition-colors active:scale-98"
          >
            <ImagePlus className="w-4 h-4 text-zinc-400" />
            <span>Прикрепить фото (EXIF очищается автоматически)</span>
          </button>
        ) : (
          <div className="p-3 rounded-2xl bg-white/5 border border-white/10 space-y-3">
            <div className="flex items-center justify-between">
              <span className="text-xs font-medium text-zinc-300">Прикрепленное фото:</span>
              <button
                type="button"
                onClick={removePhoto}
                className="text-xs text-rose-400 hover:text-rose-300 flex items-center gap-1 active:scale-95"
              >
                <X className="w-3.5 h-3.5" />
                <span>Удалить</span>
              </button>
            </div>

            {/* Photo Preview & Spoiler Overlay */}
            {previewUrl && (
              <div className="relative w-full h-40 rounded-xl overflow-hidden bg-black/40 border border-white/10 flex items-center justify-center">
                <Image
                  src={previewUrl}
                  alt="Предпросмотр"
                  fill
                  unoptimized
                  className={`object-cover transition-all duration-200 ${
                    isSpoiler ? "blur-xl scale-110 opacity-70" : ""
                  }`}
                />
                {isSpoiler && (
                  <div className="absolute inset-0 flex flex-col items-center justify-center text-white/90 bg-black/30 backdrop-blur-sm">
                    <EyeOff className="w-6 h-6 mb-1 text-amber-300" />
                    <span className="text-xs font-semibold">Скрыто спойлером</span>
                  </div>
                )}
              </div>
            )}

            {/* Spoiler Toggle */}
            <label className="flex items-center justify-between cursor-pointer pt-1">
              <div className="flex items-center gap-2">
                <div className="p-1 rounded bg-amber-500/10 text-amber-400">
                  <EyeOff className="w-3.5 h-3.5" />
                </div>
                <div>
                  <div className="text-xs font-medium text-zinc-200">
                    Скрыть фото спойлером
                  </div>
                  <div className="text-[10px] text-zinc-500">
                    Фото заблюрится в канале до клика
                  </div>
                </div>
              </div>
              <input
                type="checkbox"
                checked={isSpoiler}
                onChange={(e) => {
                  triggerHaptic("light");
                  setIsSpoiler(e.target.checked);
                }}
                className="w-4 h-4 rounded text-indigo-500 bg-white/10 border-white/20 focus:ring-0 cursor-pointer"
              />
            </label>
          </div>
        )}
      </div>

      {/* Error Alert */}
      {errorMsg && (
        <div className="p-3 rounded-xl bg-rose-500/10 border border-rose-500/30 text-rose-300 text-xs flex items-center gap-2 animate-in fade-in">
          <AlertCircle className="w-4 h-4 flex-shrink-0 text-rose-400" />
          <span>{errorMsg}</span>
        </div>
      )}

      {/* In-Page Fallback Submit Button */}
      <div className="pt-2">
        <button
          type="button"
          onClick={handleSubmit}
          disabled={content.trim().length < 3 || isSubmitting}
          className="w-full py-3.5 px-4 rounded-2xl bg-gradient-to-r from-indigo-500 via-purple-500 to-pink-500 hover:opacity-95 disabled:opacity-40 disabled:cursor-not-allowed text-white text-xs font-bold shadow-xl shadow-indigo-500/25 active:scale-98 transition-all flex items-center justify-center gap-2"
        >
          {isSubmitting ? (
            <>
              <Loader2 className="w-4 h-4 animate-spin" />
              <span>Отправка на модерацию...</span>
            </>
          ) : (
            <>
              <Send className="w-4 h-4" />
              <span>Отправить анонимно</span>
            </>
          )}
        </button>
        <p className="text-center text-[10px] text-zinc-500 pt-2">
          Нажатие кнопки в Telegram также передаст команду боту
        </p>
      </div>
    </div>
  );
}
