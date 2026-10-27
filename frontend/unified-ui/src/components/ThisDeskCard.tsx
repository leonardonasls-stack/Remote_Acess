import React, { useState } from "react";
import { Copy, Check, RefreshCw, KeyRound, ShieldCheck } from "lucide-react";

interface ThisDeskCardProps {
  hostId: string;
  tempPin: string;
  pinExpiresInSec: number;
  unattendedEnabled: boolean;
  onRotatePin: () => void;
  onOpenPasswordModal: () => void;
}

export const ThisDeskCard: React.FC<ThisDeskCardProps> = ({
  hostId,
  tempPin,
  pinExpiresInSec,
  unattendedEnabled,
  onRotatePin,
  onOpenPasswordModal,
}) => {
  const [copied, setCopied] = useState(false);

  // Formata o ID como XXX XXX XXX para facilitar a leitura
  const formattedId = hostId.length === 9
    ? `${hostId.slice(0, 3)} ${hostId.slice(3, 6)} ${hostId.slice(6, 9)}`
    : hostId || "--- --- ---";

  const formatTimer = (sec: number) => {
    const m = Math.floor(sec / 60);
    const s = sec % 60;
    return `${m.toString().padStart(2, "0")}:${s.toString().padStart(2, "0")}`;
  };

  const handleCopyId = () => {
    if (hostId) {
      navigator.clipboard.writeText(hostId.replace(/\s+/g, ""));
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  };

  return (
    <div className="bg-slate-800/60 border border-slate-700/80 rounded-xl p-6 flex flex-col justify-between shadow-lg">
      <div className="space-y-6">
        {/* Cabeçalho */}
        <div>
          <h2 className="text-sm font-semibold tracking-wider text-slate-400 uppercase">
            Este Computador
          </h2>
          <p className="text-xs text-slate-300 mt-1">
            Passe estes dados para quem for acessar esta máquina.
          </p>
        </div>

        {/* Campo Seu ID */}
        <div className="space-y-1.5">
          <label className="text-xs font-medium text-slate-300">Seu ID</label>
          <div className="bg-slate-950 border border-slate-600 rounded-lg p-3 flex items-center justify-between">
            <span className="font-mono-tabular text-xl md:text-2xl font-bold tracking-wider text-slate-50">
              {formattedId}
            </span>
            <button
              onClick={handleCopyId}
              className="flex items-center space-x-1.5 px-3 py-1.5 rounded-md text-xs font-semibold bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-600 transition-colors"
              title="Copiar ID"
            >
              {copied ? (
                <>
                  <Check className="w-3.5 h-3.5 text-emerald-400" />
                  <span className="text-emerald-400">Copiado</span>
                </>
              ) : (
                <>
                  <Copy className="w-3.5 h-3.5" />
                  <span>Copiar</span>
                </>
              )}
            </button>
          </div>
        </div>

        {/* Campo PIN Temporário com Cronômetro */}
        <div className="space-y-1.5">
          <div className="flex items-center justify-between">
            <label className="text-xs font-medium text-slate-300">PIN Temporário</label>
            <span className="font-mono-tabular text-xs text-slate-400">
              Expira em: <strong className="text-slate-200">{formatTimer(pinExpiresInSec)}</strong>
            </span>
          </div>

          <div className="bg-slate-950 border border-slate-600 rounded-lg p-3 flex items-center justify-between">
            <span className="font-mono-tabular text-xl font-bold tracking-widest text-indigo-400">
              {tempPin || "••••••"}
            </span>
            <button
              onClick={onRotatePin}
              className="flex items-center space-x-1.5 px-3 py-1.5 rounded-md text-xs font-semibold bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-600 transition-colors"
              title="Gerar novo PIN"
            >
              <RefreshCw className="w-3.5 h-3.5" />
              <span>Atualizar</span>
            </button>
          </div>
        </div>
      </div>

      {/* Rodapé: Senha Fixa Não Supervisionada */}
      <div className="mt-6 pt-4 border-t border-slate-700/80 flex items-center justify-between">
        <div className="flex items-center space-x-2 text-xs">
          {unattendedEnabled ? (
            <div className="flex items-center space-x-1.5 text-emerald-400 font-medium">
              <ShieldCheck className="w-4 h-4" />
              <span>Senha fixa ativa</span>
            </div>
          ) : (
            <div className="flex items-center space-x-1.5 text-slate-400">
              <KeyRound className="w-4 h-4" />
              <span>Acesso permanente desativado</span>
            </div>
          )}
        </div>

        <button
          onClick={onOpenPasswordModal}
          className="text-xs text-indigo-400 hover:text-indigo-300 font-medium underline underline-offset-2 transition-colors"
        >
          {unattendedEnabled ? "Alterar senha" : "Configurar senha fixa"}
        </button>
      </div>
    </div>
  );
};
