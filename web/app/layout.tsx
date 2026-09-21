import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "ProbloxDev",
  description: "Agent IA autonome qui crée des jeux Roblox — connecte ton compte, lance-le.",
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
