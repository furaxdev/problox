"use client";

import { Suspense } from "react";
import { useSearchParams } from "next/navigation";
import { ChatApp } from "@/components/ChatApp";

function DashboardInner() {
  const searchParams = useSearchParams();
  const theme = searchParams.get("theme") || undefined;
  return <ChatApp initialTheme={theme} />;
}

export default function DashboardPage() {
  return (
    <Suspense fallback={null}>
      <DashboardInner />
    </Suspense>
  );
}
