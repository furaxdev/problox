import type { Metadata } from "next";
import "./globals.css";

const DESCRIPTION =
  "Décris le jeu Roblox que tu veux, l'agent le conçoit, l'écrit et le publie sur ton compte.";

export const metadata: Metadata = {
  title: "ProbloxDev",
  description: DESCRIPTION,
  openGraph: {
    title: "ProbloxDev",
    description: DESCRIPTION,
    type: "website",
  },
  twitter: {
    card: "summary",
    title: "ProbloxDev",
    description: DESCRIPTION,
  },
};

export const viewport = {
  themeColor: "#09090b",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="fr">
      <body>{children}</body>
    </html>
  );
}
