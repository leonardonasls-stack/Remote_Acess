import React, { useEffect, useState } from "react";
import { UserCheck, Shield } from "lucide-react";

interface ConsentModalProps {
  isOpen: boolean;
  clientIp: string;
  timeoutSec: number;
  onAccept: () => void;
  onReject: () => void;
}

export const ConsentModal: React.FC<ConsentModalProps> = ({
  isOpen,
  clientIp,
  timeoutSec,
  onAccept,
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
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 backdrop-blur-md p-4 animate-in fade-in duration-150">
      <div className="w-full max-w-md bg-slate-900 border border-slate-700 rounded-xl shadow-2xl p-6 space-y-5">
        <div className="flex items-center space-x-3 text-indigo-400">
          <Shield className="w-7 h-7 flex-shrink-0" />
          <div>
            <h3 className="text-base font-bold text-slate-100">
              Permitir Acesso Remoto Supervisionado?
            </h3>
            <p className="text-xs text-slate-400">
              Solicitação recebida de <strong className="text-slate-200">[{clientIp}]</strong>
            </p>
          </div>
        </div>

        <p className="text-xs text-slate-300">
          Uma pessoa conectou utilizando o seu <strong>PIN Temporário</strong> e solicitou visualizar e controlar a sua tela.
          Você pode encerrar esta sessão a qualquer momento clicando em "Desconectar" no topo da tela ou pelo atalho físico <kbd className="bg-slate-800 px-1 py-0.5 rounded text-slate-200">Ctrl+Alt+Shift+Q</kbd>.
        </p>

        <div className="flex items-center justify-between pt-2">
          <span className="text-xs text-slate-400 font-mono-tabular">
            Expira em: <strong className="text-slate-200">{remaining}s</strong>
          </span>

          <div className="flex items-center space-x-3">
            <button
              onClick={onReject}
              className="px-4 py-2 rounded-lg text-xs font-semibold bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-600 transition-colors"
            >
              Recusar
            </button>
            <button
              onClick={onAccept}
              className="px-5 py-2 rounded-lg text-xs font-bold bg-indigo-600 hover:bg-indigo-500 text-white shadow-lg flex items-center space-x-1.5 transition-colors"
            >
              <UserCheck className="w-4 h-4" />
              <span>Aceitar Conexão</span>
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};
