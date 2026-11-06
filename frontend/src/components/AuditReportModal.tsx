import { useState } from "react";
import { generateMonthlyAuditReport } from "../api/client";
import { useAuth } from "../auth/AuthContext";
import { maskCnpj } from "../lib/car";

export default function AuditReportModal({
  isOpen,
  onClose,
}: {
  isOpen: boolean;
  onClose: () => void;
}) {
  const { producer } = useAuth();
  const [loading, setLoading] = useState(false);
  const [report, setReport] = useState<any | null>(null);
  const [error, setError] = useState<string | null>(null);

  if (!isOpen) return null;

  const handleGenerate = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await generateMonthlyAuditReport("2026-10");
      setReport(res);
    } catch (e: any) {
      setError(
        e?.message || "Erro ao gerar relatório com o motor de auditoria",
      );
    } finally {
      setLoading(false);
    }
  };

  return (
    <div
      className="modal-backdrop"
      style={{
        position: "fixed",
        top: 0,
        left: 0,
        right: 0,
        bottom: 0,
        backgroundColor: "rgba(0, 0, 0, 0.65)",
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        zIndex: 1000,
        padding: "20px",
      }}
    >
      <div
        className="card"
        style={{
          maxWidth: "800px",
          width: "100%",
          maxHeight: "90vh",
          overflowY: "auto",
          backgroundColor: "#fff",
          borderRadius: "12px",
          padding: "24px",
          boxShadow: "0 20px 25px -5px rgba(0,0,0,0.3)",
        }}
      >
        <div
          style={{
            display: "flex",
            justifyContent: "space-between",
            alignItems: "center",
            marginBottom: "16px",
          }}
        >
          <h2 style={{ margin: 0 }}>Auditoria & Consultor ESG (NFs x CARs)</h2>
          <button
            className="btn btn-ghost btn-sm"
            onClick={onClose}
            style={{ fontSize: "18px" }}
          >
            ✕
          </button>
        </div>

        <p className="muted" style={{ marginBottom: "16px" }}>
          Produtor: <strong>{producer?.email}</strong> (CNPJ:{" "}
          {producer ? maskCnpj(producer.cnpj) : ""})
        </p>

        {!report && !loading && (
          <div style={{ textAlign: "center", padding: "30px 10px" }}>
            <p
              style={{
                fontSize: "15px",
                color: "#4b5563",
                marginBottom: "20px",
              }}
            >
              O Consultor ESG cruzará o lote de Notas Fiscais emitidas no mês
              anterior com a capacidade volumétrica e os alertas/embargos de
              todos os CARs cadastrados no seu CNPJ.
            </p>
            <button
              className="btn btn-primary"
              onClick={handleGenerate}
              style={{ padding: "10px 24px", fontSize: "16px" }}
            >
              ⚡ Disparar Auditoria Mensal do Produtor
            </button>
          </div>
        )}

        {loading && (
          <div style={{ textAlign: "center", padding: "40px" }}>
            <p className="muted" style={{ fontSize: "16px" }}>
              Processando inteligência de auditoria e cruzando saldos
              volumétricos...
            </p>
          </div>
        )}

        {error && (
          <div className="card error-box" style={{ marginTop: "16px" }}>
            <p>{error}</p>
          </div>
        )}

        {report && (
          <div style={{ marginTop: "16px" }}>
            <div
              style={{
                display: "flex",
                justifyContent: "space-between",
                alignItems: "center",
                padding: "16px",
                borderRadius: "8px",
                backgroundColor:
                  report.status === "legal" ? "#ecfdf5" : "#fef2f2",
                border: `1px solid ${report.status === "legal" ? "#10b981" : "#ef4444"}`,
                marginBottom: "16px",
              }}
            >
              <div>
                <span
                  style={{
                    fontSize: "13px",
                    textTransform: "uppercase",
                    fontWeight: 600,
                    color: "#6b7280",
                  }}
                >
                  Status do Período ({report.reference_period})
                </span>
                <h3
                  style={{
                    margin: "4px 0 0 0",
                    color: report.status === "legal" ? "#047857" : "#b91c1c",
                  }}
                >
                  {report.status === "legal"
                    ? "✓ REGULAR / APTO"
                    : "⚠ IRREGULAR / NÃO APTO"}
                </h3>
              </div>
              <div style={{ textAlign: "right" }}>
                <span style={{ fontSize: "13px", color: "#6b7280" }}>
                  Score de Transparência
                </span>
                <div
                  style={{
                    fontSize: "28px",
                    fontWeight: "bold",
                    color: report.score >= 70 ? "#047857" : "#b91c1c",
                  }}
                >
                  {report.score}/100
                </div>
              </div>
            </div>

            <div
              style={{
                display: "grid",
                gridTemplateColumns: "repeat(auto-fit, minmax(180px, 1fr))",
                gap: "12px",
                marginBottom: "16px",
              }}
            >
              <div
                style={{
                  background: "#f9fafb",
                  padding: "12px",
                  borderRadius: "8px",
                  border: "1px solid #e5e7eb",
                }}
              >
                <span className="muted small">CARs Cadastrados</span>
                <strong style={{ display: "block", fontSize: "18px" }}>
                  {report.total_cars_registered}
                </strong>
              </div>
              <div
                style={{
                  background: "#f9fafb",
                  padding: "12px",
                  borderRadius: "8px",
                  border: "1px solid #e5e7eb",
                }}
              >
                <span className="muted small">CARs Evidenciados em NFs</span>
                <strong
                  style={{
                    display: "block",
                    fontSize: "18px",
                    color: "#2563eb",
                  }}
                >
                  {report.cars_evidenced_count}
                </strong>
              </div>
              <div
                style={{
                  background: "#f9fafb",
                  padding: "12px",
                  borderRadius: "8px",
                  border: "1px solid #e5e7eb",
                }}
              >
                <span className="muted small">CARs Omitidos no Mês</span>
                <strong
                  style={{
                    display: "block",
                    fontSize: "18px",
                    color:
                      report.cars_omitted_count > 0 ? "#dc2626" : "#059669",
                  }}
                >
                  {report.cars_omitted_count}
                </strong>
              </div>
              <div
                style={{
                  background: "#f9fafb",
                  padding: "12px",
                  borderRadius: "8px",
                  border: "1px solid #e5e7eb",
                }}
              >
                <span className="muted small">Volume Total Faturado</span>
                <strong style={{ display: "block", fontSize: "18px" }}>
                  {report.total_volume_extracted_m3} m³
                </strong>
              </div>
            </div>

            <div style={{ marginBottom: "16px" }}>
              <h4 style={{ margin: "0 0 8px 0" }}>
                Parecer Técnico da Auditoria
              </h4>
              <p
                style={{
                  background: "#f8fafc",
                  padding: "14px",
                  borderRadius: "8px",
                  borderLeft: "4px solid #3b82f6",
                  margin: 0,
                  fontSize: "14px",
                  lineHeight: 1.5,
                }}
              >
                {report.justification}
              </p>
            </div>

            {report.suggestions && report.suggestions.length > 0 && (
              <div style={{ marginBottom: "16px" }}>
                <h4 style={{ margin: "0 0 8px 0" }}>
                  Recomendações do Consultor ESG:
                </h4>
                <ul
                  style={{
                    margin: 0,
                    paddingLeft: "20px",
                    fontSize: "14px",
                    color: "#374151",
                    lineHeight: 1.6,
                  }}
                >
                  {report.suggestions.map((sug: string, i: number) => (
                    <li key={i} style={{ marginBottom: "4px" }}>
                      {sug}
                    </li>
                  ))}
                </ul>
              </div>
            )}

            <div style={{ textAlign: "right", marginTop: "20px" }}>
              <button className="btn btn-ghost" onClick={() => setReport(null)}>
                Nova Análise
              </button>
              <button
                className="btn btn-primary"
                onClick={onClose}
                style={{ marginLeft: "8px" }}
              >
                Fechar
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
