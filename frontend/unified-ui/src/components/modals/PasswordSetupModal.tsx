import React, { useState } from "react";
import { X, ShieldCheck, KeyRound } from "lucide-react";

interface PasswordSetupModalProps {
  isOpen: boolean;
  unattendedEnabled: boolean;
  onClose: () => void;
  onSavePassword: (newPassword: string) => void;
  onDisable: () => void;
}

export const PasswordSetupModal: React.FC<PasswordSetupModalProps> = ({
  isOpen,
  unattendedEnabled,
  onClose,
  onSavePassword,
  onDisable,
}) => {
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [error, setError] = useState("");

  if (!isOpen) return null;

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (password.length < 8) {
      setError("A senha deve ter no mínimo 8 caracteres.");
      return;
    }
    if (password !== confirmPassword) {
      setError("As senhas não coincidem.");
      return;
    }
    setError("");
    onSavePassword(password);
    setPassword("");
    setConfirmPassword("");
    onClose();
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 backdrop-blur-sm p-4">
      <div className="w-full max-w-md bg-slate-900 border border-slate-700 rounded-xl shadow-2xl overflow-hidden animate-in fade-in zoom-in-95 duration-150">
        <div className="flex items-center justify-between px-5 py-4 border-b border-slate-800">
          <div className="flex items-center space-x-2 text-slate-100 font-semibold text-sm">
            <KeyRound className="w-4 h-4 text-indigo-400" />
            <span>Configurar Senha Fixa (Acesso Não Supervisionado)</span>
          </div>
          <button
            onClick={onClose}
            className="p-1 rounded-md text-slate-400 hover:text-slate-100 hover:bg-slate-800 transition-colors"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="p-5 space-y-4">
          <p className="text-xs text-slate-300">
            A senha fixa permite que você acerte este computador a qualquer momento sem precisar
            confirmar na tela. Ela é armazenada como hash seguro (PBKDF2-HMAC-SHA256).
          </p>

          {error && (
            <div className="p-2.5 rounded bg-red-950/80 border border-red-800 text-red-300 text-xs">
              {error}
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
              placeholder="Digite a mesma senha"
              value={confirmPassword}
              onChange={(e) => setConfirmPassword(e.target.value)}
              required
              className="w-full bg-slate-950 border border-slate-600 rounded-lg px-3 py-2 text-sm text-slate-50 focus:outline-none focus:ring-2 focus:ring-indigo-500"
            />
          </div>

          <div className="flex items-center justify-between pt-2">
            {unattendedEnabled ? (
              <button
                type="button"
                onClick={() => {
                  onDisable();
                  onClose();
                }}
                className="text-xs text-red-400 hover:text-red-300 underline"
              >
                Desativar acesso permanente
              </button>
            ) : <div />}

            <div className="flex items-center space-x-2">
              <button
                type="button"
                onClick={onClose}
                className="px-3 py-2 rounded-lg text-xs font-medium text-slate-300 hover:bg-slate-800 border border-slate-700 transition-colors"
              >
                Cancelar
              </button>
              <button
                type="submit"
                className="px-4 py-2 rounded-lg text-xs font-semibold bg-indigo-600 hover:bg-indigo-500 text-white shadow transition-colors flex items-center space-x-1.5"
              >
                <ShieldCheck className="w-3.5 h-3.5" />
                <span>Salvar Senha</span>
              </button>
            </div>
          </div>
        </form>
      </div>
    </div>
  );
};
