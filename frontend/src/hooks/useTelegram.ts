"use client";

import { useEffect, useState, useCallback, useRef } from "react";
import { TelegramWebApp } from "@/types/telegram";

export function useTelegram() {
  const [webApp, setWebApp] = useState<TelegramWebApp | null>(null);
  const [initDataRaw, setInitDataRaw] = useState<string>("");
  const [isReady, setIsReady] = useState(false);
  const clickHandlerRef = useRef<(() => void) | null>(null);

  useEffect(() => {
    if (typeof window !== "undefined" && window.Telegram?.WebApp) {
      const app = window.Telegram.WebApp;
      setWebApp(app);
      setInitDataRaw(app.initData || "");
      try {
        app.ready();
        app.expand();
      } catch (err) {
        console.warn("Telegram WebApp expand error:", err);
      }
      setIsReady(true);
    } else {
      // Mock for standard browser development
      setIsReady(true);
    }
  }, []);

  const triggerHaptic = useCallback(
    (style: "light" | "medium" | "heavy" | "rigid" | "soft" = "medium") => {
      try {
        if (webApp?.HapticFeedback) {
          webApp.HapticFeedback.impactOccurred(style);
        }
      } catch (err) {
        console.warn("Haptic error:", err);
      }
    },
    [webApp]
  );

  const triggerNotificationHaptic = useCallback(
    (type: "error" | "success" | "warning") => {
      try {
        if (webApp?.HapticFeedback) {
          webApp.HapticFeedback.notificationOccurred(type);
        }
      } catch (err) {
        console.warn("Notification Haptic error:", err);
      }
    },
    [webApp]
  );

  const setMainButton = useCallback(
    (options: {
      text: string;
      onClick: () => void;
      isVisible?: boolean;
      isActive?: boolean;
      isLoading?: boolean;
    }) => {
      if (!webApp?.MainButton) return;

      const mb = webApp.MainButton;
      mb.setText(options.text);

      if (clickHandlerRef.current) {
        mb.offClick(clickHandlerRef.current);
      }

      clickHandlerRef.current = options.onClick;
      mb.onClick(options.onClick);

      if (options.isVisible ?? true) {
        mb.show();
      } else {
        mb.hide();
      }

      if (options.isActive ?? true) {
        mb.enable();
      } else {
        mb.disable();
      }

      if (options.isLoading) {
        mb.showProgress(false);
      } else {
        mb.hideProgress();
      }
    },
    [webApp]
  );

  const hideMainButton = useCallback(() => {
    if (!webApp?.MainButton) return;
    if (clickHandlerRef.current) {
      webApp.MainButton.offClick(clickHandlerRef.current);
      clickHandlerRef.current = null;
    }
    webApp.MainButton.hide();
  }, [webApp]);

  return {
    webApp,
    initDataRaw,
    isReady,
    isTelegram: Boolean(webApp && initDataRaw),
    triggerHaptic,
    triggerNotificationHaptic,
    setMainButton,
    hideMainButton,
    theme: webApp?.themeParams || {},
    colorScheme: webApp?.colorScheme || "dark",
  };
}
