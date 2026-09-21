import { redirect } from "next/navigation";

// L'ancien dashboard en panneaux a été fusionné dans la page d'accueil
// (interface chat façon v0.dev/emergent.sh) — on garde cette route en
// redirection pour ne pas casser un lien existant.
export default function DashboardRedirect() {
  redirect("/");
}
