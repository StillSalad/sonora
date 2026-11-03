import { ButtonLink, PageTitle } from "../components/Pieces";

export default function NotFound() {
  return (
    <>
      <PageTitle sub="Il link potrebbe essere sbagliato o la pagina è stata spostata.">Pagina non trovata</PageTitle>
      <ButtonLink to="/">Torna a Per te</ButtonLink>
    </>
  );
}
