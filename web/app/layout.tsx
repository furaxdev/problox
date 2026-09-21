import type { Metadata } from "next";
import "./globals.css";

const DESCRIPTION =
  "Agent IA autonome qui crée des jeux Roblox — connecte ton compte, lance-le.";

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
  themeColor: "#0b0d12",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="fr">
      <body>
        <header>
          <h1>Problox<span>Dev</span></h1>
          <span className="tag">agent IA pour la création de jeux Roblox</span>
        </header>
        {children}
      </body>
    </html>
  );
}
