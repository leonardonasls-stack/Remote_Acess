import React, { useEffect, useState } from "react";
import { MousePointerClick, AlertTriangle } from "lucide-react";

interface PhysicalApprovalModalProps {
  isOpen: boolean;
  clientIp: string;
  timeoutSec: number;
  onApproveLocalClick: () => void;
  onReject: () => void;
}

export const PhysicalApprovalModal: React.FC<PhysicalApprovalModalProps> = ({
  isOpen,
  clientIp,
  timeoutSec,
  onApproveLocalClick,
  onReject,
}) => {
  const [remaining, setRemaining] = useState(timeoutSec);

  useEffect(() => {
    if (!isOpen) return;
    setRemaining(timeoutSec);
    const interval = setInterval(() => {
      setRemaining((prev) => {
        if (prev <= 1) {
          clearInterval(interval);
          onReject();
          return 0;
        }
        return prev - 1;
      });
    }, 1000);
    return () => clearInterval(interval);
  }, [isOpen, timeoutSec]);

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 backdrop-blur-md p-4 animate-in fade-in duration-200">
      <div className="w-full max-w-lg bg-slate-900 border-2 border-amber-500 rounded-xl shadow-2xl overflow-hidden p-6 space-y-5">
        <div className="flex items-center space-x-3 text-amber-400">
          <AlertTriangle className="w-7 h-7 flex-shrink-0 animate-bounce" />
          <div>
            <h3 className="text-base font-bold text-slate-100">
              Permitir Acesso Permanente Não Supervisionado?
            </h3>
            <p className="text-xs text-amber-300">
              Solicitação recebida do operador remoto [{clientIp}]
            </p>
          </div>
        </div>

        <div className="bg-slate-950 p-4 rounded-lg border border-slate-700 text-xs text-slate-300 space-y-2">
          <p>
            O técnico que está te atendendo solicitou configurar uma <strong>Senha Fixa</strong> neste computador.
            Com esta senha, ele poderá acessar sua tela a qualquer momento no futuro sem pedir autorização.
          </p>
          <div className="p-2.5 rounded bg-amber-950/40 border border-amber-800/80 text-amber-200 font-medium">
            🛡️ <strong>Proteção Física Anti-Auto-Clique Ativa:</strong> O sistema bloqueia qualquer tentativa do técnico de aprovar este modal remotamente. Apenas o seu clique no mouse físico será aceito!
          </div>
        </div>

        <div className="flex items-center justify-between pt-2">
          <span className="text-xs text-slate-400 font-mono-tabular">
            Tempo limite: <strong className="text-slate-200">{remaining}s</strong>
          </span>

          <div className="flex items-center space-x-3">
            <button
              onClick={onReject}
              className="px-4 py-2 rounded-lg text-xs font-semibold bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-600 transition-colors cursor-pointer"
            >
              Recusar
            </button>

            {/* Este botão aciona a validação de physical_guard.is_recent_physical_click() */}
            <button
              onClick={onApproveLocalClick}
              className="px-5 py-2.5 rounded-lg text-xs font-bold bg-amber-500 hover:bg-amber-400 text-slate-950 shadow-lg flex items-center space-x-2 transition-all cursor-pointer"
            >
              <MousePointerClick className="w-4 h-4" />
              <span>Permitir (Clique Local com seu Mouse)</span>
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};
