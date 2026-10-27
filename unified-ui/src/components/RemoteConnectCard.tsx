import React, { useState } from "react";
import { ArrowRight, Monitor, Clock } from "lucide-react";
import type { RecentHost } from "../types/protocol";

interface RemoteConnectCardProps {
  onConnect: (hostId: string, credential: string) => void;
  recentHosts: RecentHost[];
  onSelectRecent: (hostId: string) => void;
}

export const RemoteConnectCard: React.FC<RemoteConnectCardProps> = ({
  onConnect,
  recentHosts,
  onSelectRecent,
}) => {
  const [targetId, setTargetId] = useState("");
  const [credential, setCredential] = useState("");

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    const cleanId = targetId.replace(/\s+/g, "");
    if (cleanId.length >= 6 && credential.trim().length > 0) {
      onConnect(cleanId, credential.trim());
    }
  };

  // Aplica máscara automática de ID (XXX XXX XXX)
  const handleIdChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const raw = e.target.value.replace(/\D/g, "").slice(0, 9);
    let formatted = raw;
    if (raw.length > 6) {
      formatted = `${raw.slice(0, 3)} ${raw.slice(3, 6)} ${raw.slice(6)}`;
    } else if (raw.length > 3) {
      formatted = `${raw.slice(0, 3)} ${raw.slice(3)}`;
    }
    setTargetId(formatted);
  };

  return (
    <div className="bg-slate-800/60 border border-slate-700/80 rounded-xl p-6 flex flex-col justify-between shadow-lg">
      <div className="space-y-6">
        <div>
          <h2 className="text-sm font-semibold tracking-wider text-slate-400 uppercase">
            Controlar Outro Computador
          </h2>
          <p className="text-xs text-slate-300 mt-1">
            Digite o ID e o PIN (ou senha fixa) da máquina parceira.
          </p>
        </div>

        {/* Formulário de Conexão */}
        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="grid grid-cols-1 sm:grid-cols-12 gap-3">
            {/* Input ID Remoto */}
            <div className="sm:col-span-7 space-y-1.5">
              <label className="text-xs font-medium text-slate-300">ID do Computador</label>
              <input
                type="text"
                placeholder="Ex: 482 910 384"
                value={targetId}
                onChange={handleIdChange}
                required
                className="w-full bg-slate-950 border border-slate-600 rounded-lg px-3.5 py-2.5 font-mono-tabular text-sm font-semibold text-slate-50 placeholder:text-slate-500 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 transition-all"
              />
            </div>

            {/* Input PIN ou Senha */}
            <div className="sm:col-span-5 space-y-1.5">
              <label className="text-xs font-medium text-slate-300">PIN ou Senha</label>
              <input
                type="password"
                placeholder="PIN (6d) ou Senha"
                value={credential}
                onChange={(e) => setCredential(e.target.value)}
                required
                className="w-full bg-slate-950 border border-slate-600 rounded-lg px-3.5 py-2.5 text-sm font-semibold text-slate-50 placeholder:text-slate-500 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 transition-all"
              />
            </div>
          </div>

          <button
            type="submit"
            className="w-full bg-indigo-600 hover:bg-indigo-500 active:bg-indigo-700 text-white font-semibold text-sm py-2.5 px-4 rounded-lg flex items-center justify-center space-x-2 shadow-md transition-all duration-150 cursor-pointer"
          >
            <span>Conectar</span>
            <ArrowRight className="w-4 h-4" />
          </button>
        </form>

        {/* Acessados Recentemente */}
        {recentHosts.length > 0 && (
          <div className="pt-2">
            <div className="flex items-center space-x-1.5 text-xs text-slate-400 mb-2.5">
              <Clock className="w-3.5 h-3.5" />
              <span className="font-medium">Acessados Recentemente</span>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
              {recentHosts.map((item) => (
                <button
                  key={item.hostId}
                  onClick={() => {
                    setTargetId(item.hostId);
                    onSelectRecent(item.hostId);
                  }}
                  className="flex items-center justify-between p-2.5 rounded-lg bg-slate-900/80 hover:bg-slate-900 border border-slate-700 hover:border-slate-600 text-left transition-colors group cursor-pointer"
                >
                  <div className="flex items-center space-x-2 truncate">
                    <Monitor className="w-4 h-4 text-slate-400 group-hover:text-indigo-400 flex-shrink-0" />
                    <div className="truncate">
                      <div className="text-xs font-semibold text-slate-200 truncate">
                        {item.label}
                      </div>
                      <div className="text-[11px] font-mono-tabular text-slate-400 truncate">
                        {item.hostId}
                      </div>
                    </div>
                  </div>
                  <ArrowRight className="w-3.5 h-3.5 text-slate-500 group-hover:text-slate-300 flex-shrink-0 ml-1" />
                </button>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
};
