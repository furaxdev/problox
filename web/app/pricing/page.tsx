"use client";

const TIERS = [
  {
    name: "Free",
    price: "0€",
    period: "",
    desc: "Pour essayer l'agent et builder en dry-run.",
    features: [
      "Design starter kit (sans clé Claude)",
      "Génération Luau + build Rojo illimités",
      "Téléchargement du .rbxlx",
      "1 run à la fois, cooldown 15s",
    ],
    cta: "Plan actuel",
    highlighted: false,
    disabled: true,
  },
  {
    name: "Pro",
    price: "—",
    period: "/mois",
    desc: "Designs générés par Claude, publication directe, plus de runs.",
    features: [
      "Tout Free",
      "Design créatif via Claude (pas de starter kit)",
      "Mode autonome multi-itérations",
      "Publication directe sur Roblox (OAuth)",
      "Cooldown réduit entre les runs",
    ],
    cta: "Bientôt disponible",
    highlighted: true,
    disabled: true,
  },
  {
    name: "Team",
    price: "—",
    period: "/mois",
    desc: "Plusieurs projets, plusieurs expériences Roblox, priorité.",
    features: [
      "Tout Pro",
      "Projets illimités avec contexte partagé",
      "Plusieurs expériences Roblox gérées",
      "Support prioritaire",
    ],
    cta: "Bientôt disponible",
    highlighted: false,
    disabled: true,
  },
];

export default function Pricing() {
  return (
    <div className="simple-page">
      <div className="topbar">
        <a className="brand" href="/">
          <img src="/icon.svg" alt="" />
          <span>
            Problox<b>Dev</b>
          </span>
        </a>
        <a className="account-chip" href="/">
          ← Retour au chat
        </a>
      </div>

      <div className="pricing-wrap">
        <div className="pricing-header">
          <h1>Tarifs</h1>
          <p className="sub">
            ProbloxDev est gratuit et en bêta pour l&apos;instant — la facturation par crédits
            n&apos;est pas encore branchée (pas de Stripe configuré). Cette page montre ce qui
            arrive, honnêtement: aucun bouton ici ne débite quoi que ce soit.
          </p>
        </div>

        <div className="pricing-grid">
          {TIERS.map((tier) => (
            <div key={tier.name} className={`pricing-card ${tier.highlighted ? "highlighted" : ""}`}>
              {tier.highlighted && <div className="pricing-badge">Le plus demandé</div>}
              <h3>{tier.name}</h3>
              <div className="pricing-price">
                {tier.price}
                <span className="muted">{tier.period}</span>
              </div>
              <p className="muted">{tier.desc}</p>
              <ul className="pricing-features">
                {tier.features.map((f) => (
                  <li key={f}>✓ {f}</li>
                ))}
              </ul>
              <button className={`btn ${tier.highlighted ? "btn-primary" : "btn-secondary"}`} disabled={tier.disabled} style={{ width: "100%" }}>
                {tier.cta}
              </button>
            </div>
          ))}
        </div>

        <p className="muted" style={{ textAlign: "center", marginTop: 28 }}>
          Une idée de fonctionnalité payante qui te ferait passer à l&apos;abonnement ? Écris-le
          dans une issue GitHub sur{" "}
          <a href="https://github.com/furaxdev/problox" target="_blank" rel="noreferrer">
            furaxdev/problox
          </a>
          .
        </p>
      </div>
    </div>
  );
}
