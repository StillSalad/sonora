import { useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import { PageTitle } from "../components/Pieces";
import { TrackRow } from "../components/TrackParts";
import { api, ApiError, type Track } from "../lib/api";
import NotFound from "./NotFound";

export default function Artist() {
  const { id = "" } = useParams();
  const [data, setData] = useState<{ name: string; tracks: Track[] } | null>(null);
  const [error, setError] = useState<ApiError | null>(null);
  useEffect(() => {
    setData(null); setError(null);
    api<{ name: string; tracks: Track[] }>(`/artists/${id}`).then(setData).catch((e) => setError(e instanceof ApiError ? e : new ApiError(0, "error", "Errore")));
  }, [id]);
  if (error?.status === 404) return <NotFound />;
  return (
    <>
      <PageTitle back sub={data ? `${data.tracks.length} brani nel catalogo di SONORA` : undefined}>{data?.name ?? " "}</PageTitle>
      {error && <p role="alert" className="text-danger">{error.message}</p>}
      <ul className="flex flex-col">{data?.tracks.map((t) => <TrackRow key={t.id} t={t} surface="artist" />)}</ul>
    </>
  );
}
