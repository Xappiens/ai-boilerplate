/**
 * Dashboard Page
 * ===============
 * Protected page showing documents and AI processing controls.
 */

import { useEffect, useState, useCallback } from "react";
import { useNavigate } from "react-router-dom";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { authApi, documentsApi, type Document, type UserProfile } from "@/lib/api";

const STATUS_MAP: Record<string, { label: string; variant: "default" | "secondary" | "destructive" | "outline" }> = {
  pending: { label: "Pendiente", variant: "outline" },
  queued: { label: "En cola", variant: "secondary" },
  processing: { label: "Procesando", variant: "default" },
  completed: { label: "Completado", variant: "default" },
  failed: { label: "Fallido", variant: "destructive" },
};

export default function DashboardPage() {
  const navigate = useNavigate();
  const [user, setUser] = useState<UserProfile | null>(null);
  const [documents, setDocuments] = useState<Document[]>([]);
  const [loading, setLoading] = useState(true);
  const [newTitle, setNewTitle] = useState("");
  const [newContent, setNewContent] = useState("");
  const [creating, setCreating] = useState(false);

  const loadData = useCallback(async () => {
    try {
      const [profile, docs] = await Promise.all([
        authApi.getProfile(),
        documentsApi.list(),
      ]);
      setUser(profile);
      setDocuments(docs);
    } catch {
      navigate("/login");
    } finally {
      setLoading(false);
    }
  }, [navigate]);

  useEffect(() => {
    loadData();
  }, [loadData]);

  const handleCreateDocument = async () => {
    if (!newTitle.trim()) {
      toast.error("El título es obligatorio");
      return;
    }
    setCreating(true);
    try {
      const doc = await documentsApi.create(newTitle, newContent);
      setDocuments((prev) => [doc, ...prev]);
      setNewTitle("");
      setNewContent("");
      toast.success("Documento creado");
    } catch {
      toast.error("Error al crear documento");
    } finally {
      setCreating(false);
    }
  };

  const handleProcess = async (docId: string) => {
    try {
      const result = await documentsApi.process(docId);
      toast.info(result.message);
      // Update local state
      setDocuments((prev) =>
        prev.map((d) =>
          d.id === docId ? { ...d, status: "queued" as const } : d
        )
      );
    } catch (err: unknown) {
      const error = err as { response?: { data?: { detail?: string } } };
      toast.error(error.response?.data?.detail || "Error al procesar");
    }
  };

  const handleDelete = async (docId: string) => {
    try {
      await documentsApi.delete(docId);
      setDocuments((prev) => prev.filter((d) => d.id !== docId));
      toast.success("Documento eliminado");
    } catch {
      toast.error("Error al eliminar");
    }
  };

  const handleRefresh = async () => {
    setLoading(true);
    await loadData();
    toast.info("Datos actualizados");
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-background">
        <div className="flex flex-col items-center gap-4">
          <svg className="animate-spin h-8 w-8 text-primary" viewBox="0 0 24 24">
            <circle
              className="opacity-25"
              cx="12"
              cy="12"
              r="10"
              stroke="currentColor"
              strokeWidth="4"
              fill="none"
            />
            <path
              className="opacity-75"
              fill="currentColor"
              d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"
            />
          </svg>
          <p className="text-muted-foreground">Cargando dashboard...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-background">
      {/* Navigation Bar */}
      <nav className="border-b bg-card/50 backdrop-blur-sm sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            <div className="flex items-center gap-3">
              <div className="w-9 h-9 rounded-lg bg-primary flex items-center justify-center">
                <svg
                  xmlns="http://www.w3.org/2000/svg"
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="currentColor"
                  strokeWidth="2"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  className="w-5 h-5 text-primary-foreground"
                >
                  <path d="M12 2L2 7l10 5 10-5-10-5z" />
                  <path d="M2 17l10 5 10-5" />
                  <path d="M2 12l10 5 10-5" />
                </svg>
              </div>
              <h1 className="text-lg font-heading font-semibold">
                AI Boilerplate
              </h1>
            </div>
            <div className="flex items-center gap-4">
              <span className="text-sm text-muted-foreground hidden sm:block">
                {user?.email}
              </span>
              <Button
                id="logout-btn"
                variant="outline"
                size="sm"
                onClick={() => authApi.logout()}
              >
                Cerrar Sesión
              </Button>
            </div>
          </div>
        </div>
      </nav>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8">
        {/* Welcome Section */}
        <div>
          <h2 className="text-3xl font-heading font-bold tracking-tight">
            Dashboard
          </h2>
          <p className="text-muted-foreground mt-1">
            Gestiona tus documentos y procéelos con IA
          </p>
        </div>

        {/* Create Document */}
        <Card>
          <CardHeader>
            <CardTitle>Nuevo Documento</CardTitle>
            <CardDescription>
              Crea un documento para procesarlo con inteligencia artificial
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="flex flex-col sm:flex-row gap-4">
              <Input
                id="new-doc-title"
                placeholder="Título del documento"
                value={newTitle}
                onChange={(e) => setNewTitle(e.target.value)}
                className="flex-1"
              />
              <Input
                id="new-doc-content"
                placeholder="Contenido (texto)"
                value={newContent}
                onChange={(e) => setNewContent(e.target.value)}
                className="flex-[2]"
              />
              <Button
                id="create-doc-btn"
                onClick={handleCreateDocument}
                disabled={creating}
              >
                {creating ? "Creando..." : "Crear"}
              </Button>
            </div>
          </CardContent>
        </Card>

        {/* Documents List */}
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <h3 className="text-xl font-heading font-semibold">
              Mis Documentos ({documents.length})
            </h3>
            <Button
              id="refresh-btn"
              variant="outline"
              size="sm"
              onClick={handleRefresh}
            >
              ↻ Actualizar
            </Button>
          </div>

          {documents.length === 0 ? (
            <Card>
              <CardContent className="flex flex-col items-center justify-center py-12 text-center">
                <svg
                  xmlns="http://www.w3.org/2000/svg"
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="currentColor"
                  strokeWidth="1.5"
                  className="w-12 h-12 text-muted-foreground mb-4"
                >
                  <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
                  <polyline points="14 2 14 8 20 8" />
                  <line x1="12" y1="18" x2="12" y2="12" />
                  <line x1="9" y1="15" x2="15" y2="15" />
                </svg>
                <p className="text-muted-foreground text-lg">
                  No hay documentos aún
                </p>
                <p className="text-sm text-muted-foreground mt-1">
                  Crea tu primer documento para comenzar
                </p>
              </CardContent>
            </Card>
          ) : (
            <div className="grid gap-4">
              {documents.map((doc) => {
                const statusInfo = STATUS_MAP[doc.status] || STATUS_MAP.pending;
                return (
                  <Card key={doc.id} className="hover:shadow-md transition-shadow">
                    <CardContent className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 py-5">
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-2 mb-1">
                          <h4 className="font-semibold truncate">{doc.title}</h4>
                          <Badge variant={statusInfo.variant}>
                            {statusInfo.label}
                          </Badge>
                        </div>
                        <p className="text-sm text-muted-foreground line-clamp-1">
                          {doc.content || "Sin contenido"}
                        </p>
                        {doc.ai_summary && (
                          <div className="mt-2 p-3 bg-muted rounded-lg">
                            <p className="text-xs font-medium text-muted-foreground mb-1">
                              Resumen IA ({doc.ai_model_used}):
                            </p>
                            <p className="text-sm">{doc.ai_summary}</p>
                          </div>
                        )}
                        <p className="text-xs text-muted-foreground mt-2">
                          Creado: {new Date(doc.created_at).toLocaleString("es-ES")}
                        </p>
                      </div>
                      <div className="flex gap-2 shrink-0">
                        <Button
                          id={`process-${doc.id}`}
                          size="sm"
                          onClick={() => handleProcess(doc.id)}
                          disabled={
                            doc.status === "processing" || doc.status === "queued"
                          }
                        >
                          {doc.status === "processing"
                            ? "Procesando..."
                            : doc.status === "queued"
                            ? "En cola..."
                            : "Procesar con IA"}
                        </Button>
                        <Button
                          id={`delete-${doc.id}`}
                          size="sm"
                          variant="destructive"
                          onClick={() => handleDelete(doc.id)}
                        >
                          Eliminar
                        </Button>
                      </div>
                    </CardContent>
                  </Card>
                );
              })}
            </div>
          )}
        </div>
      </main>
    </div>
  );
}
