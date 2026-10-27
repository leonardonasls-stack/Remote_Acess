import React, { useState } from "react";
import { X, KeyRound, AlertCircle, ShieldAlert } from "lucide-react";

interface RemoteUnattendedModalProps {
  isOpen: boolean;
  onClose: () => void;
  onRequestSetup: (newPassword: string) => void;
  status: "idle" | "pending_approval" | "success" | "blocked" | "error";
  statusMessage?: string;
}

export const RemoteUnattendedModal: React.FC<RemoteUnattendedModalProps> = ({
  isOpen,
  onClose,
  onRequestSetup,
  status,
  statusMessage,
}) => {
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [validationErr, setValidationErr] = useState("");

  if (!isOpen) return null;

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (password.length < 8) {
      setValidationErr("A senha deve ter no mínimo 8 caracteres.");
      return;
    }
    if (password !== confirmPassword) {
      setValidationErr("As senhas não coincidem.");
      return;
    }
    setValidationErr("");
    onRequestSetup(password);
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 backdrop-blur-sm p-4">
      <div className="w-full max-w-md bg-slate-900 border border-slate-700 rounded-xl shadow-2xl overflow-hidden animate-in fade-in zoom-in-95 duration-150">
        <div className="flex items-center justify-between px-5 py-4 border-b border-slate-800">
          <div className="flex items-center space-x-2 text-slate-100 font-semibold text-sm">
            <KeyRound className="w-4 h-4 text-indigo-400" />
            <span>Criar Senha Fixa no Computador Remoto</span>
          </div>
          <button
            onClick={onClose}
            className="p-1 rounded-md text-slate-400 hover:text-slate-100 hover:bg-slate-800 transition-colors"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        <div className="p-5 space-y-4">
          {status === "idle" && (
            <form onSubmit={handleSubmit} className="space-y-4">
              <div className="p-3 rounded-lg bg-indigo-950/40 border border-indigo-800/60 text-indigo-200 text-xs flex items-start space-x-2">
                <ShieldAlert className="w-4 h-4 flex-shrink-0 text-indigo-400 mt-0.5" />
                <span>
                  <strong>Regra de Segurança Física:</strong> Para sua proteção e do cliente,
                  após solicitar a criação desta senha, um modal aparecerá na tela do cliente exigindo
                  um <strong>clique físico no mouse local</strong> para aprovar.
                </span>
              </div>

              {validationErr && (
                <div className="p-2.5 rounded bg-red-950/80 border border-red-800 text-red-300 text-xs">
                  {validationErr}
                </div>
              )}

              <div className="space-y-1.5">
                <label className="text-xs font-medium text-slate-300">Nova Senha Permanente</label>
                <input
                  type="password"
                  placeholder="Mínimo 8 caracteres"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  required
                  className="w-full bg-slate-950 border border-slate-600 rounded-lg px-3 py-2 text-sm text-slate-50 focus:outline-none focus:ring-2 focus:ring-indigo-500"
                />
              </div>

              <div className="space-y-1.5">
                <label className="text-xs font-medium text-slate-300">Confirmar Senha</label>
                <input
                  type="password"
                  placeholder="Digite novamente"
                  value={confirmPassword}
                  onChange={(e) => setConfirmPassword(e.target.value)}
                  required
                  className="w-full bg-slate-950 border border-slate-600 rounded-lg px-3 py-2 text-sm text-slate-50 focus:outline-none focus:ring-2 focus:ring-indigo-500"
                />
              </div>

              <div className="flex justify-end space-x-2 pt-2">
                <button
                  type="button"
                  onClick={onClose}
                  className="px-3 py-2 rounded-lg text-xs font-medium text-slate-300 hover:bg-slate-800 border border-slate-700"
                >
                  Cancelar
                </button>
                <button
                  type="submit"
                  className="px-4 py-2 rounded-lg text-xs font-semibold bg-indigo-600 hover:bg-indigo-500 text-white shadow"
                >
                  Solicitar Criação de Senha
                </button>
              </div>
            </form>
          )}

          {status === "pending_approval" && (
            <div className="py-6 text-center space-y-3">
              <div className="w-10 h-10 border-4 border-indigo-500 border-t-transparent rounded-full animate-spin mx-auto" />
              <h4 className="text-sm font-semibold text-slate-100">
                Aguardando Aprovação Física no Host Remoto...
              </h4>
              <p className="text-xs text-slate-400 max-w-xs mx-auto">
                Peça ao usuário local no computador remoto para clicar no botão "Permitir" usando o mouse físico.
              </p>
            </div>
          )}

          {status === "blocked" && (
            <div className="p-4 rounded-lg bg-red-950/80 border border-red-800 text-center space-y-2">
              <AlertCircle className="w-6 h-6 text-red-400 mx-auto" />
              <h4 className="text-sm font-bold text-red-200">
                Ação Bloqueada pela Guarda Física!
              </h4>
              <p className="text-xs text-red-300">
                {statusMessage ||
                  "O sistema detectou uma tentativa de auto-aprovação ou ausência de clique físico recente no mouse do cliente."}
              </p>
              <button
                onClick={onClose}
                className="mt-3 px-4 py-1.5 rounded-lg bg-red-800 hover:bg-red-700 text-white text-xs font-semibold"
              >
                Fechar
              </button>
            </div>
          )}

          {status === "success" && (
            <div className="p-4 rounded-lg bg-emerald-950/80 border border-emerald-800 text-center space-y-2">
              <ShieldAlert className="w-6 h-6 text-emerald-400 mx-auto" />
              <h4 className="text-sm font-bold text-emerald-200">
                Senha Permanente Gravada com Sucesso!
              </h4>
              <p className="text-xs text-emerald-300">
                Agora você pode acessar este computador a qualquer momento utilizando esta senha fixa.
              </p>
              <button
                onClick={onClose}
                className="mt-3 px-4 py-1.5 rounded-lg bg-emerald-800 hover:bg-emerald-700 text-white text-xs font-semibold"
              >
                Concluir
              </button>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
