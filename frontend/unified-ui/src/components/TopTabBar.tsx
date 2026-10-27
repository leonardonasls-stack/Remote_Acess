import React from "react";
import { Plus, X, Monitor, Home, Wifi, WifiOff } from "lucide-react";
import type { RemoteSession } from "../types/protocol";

interface TopTabBarProps {
  activeTab: string; // "home" ou session.id
  sessions: RemoteSession[];
  signalingConnected: boolean;
  onSelectTab: (tabId: string) => void;
  onNewSessionClick: () => void;
  onCloseSession: (sessionId: string, e: React.MouseEvent) => void;
}

export const TopTabBar: React.FC<TopTabBarProps> = ({
  activeTab,
  sessions,
  signalingConnected,
  onSelectTab,
  onNewSessionClick,
  onCloseSession,
}) => {
  return (
    <header className="h-11 bg-slate-950 border-b border-slate-800 flex items-center justify-between px-3 select-none">
      {/* Abas */}
      <div className="flex items-center space-x-1.5 overflow-x-auto no-scrollbar py-1">
        {/* Aba Início */}
        <button
          onClick={() => onSelectTab("home")}
          className={`flex items-center space-x-2 px-3 py-1.5 rounded-md text-xs font-medium transition-colors ${
            activeTab === "home"
              ? "bg-slate-800 text-slate-50 border border-slate-700 shadow-sm"
              : "text-slate-400 hover:text-slate-200 hover:bg-slate-900"
          }`}
          title="Página Inicial de Conexão"
        >
          <Home className="w-3.5 h-3.5" />
          <span>Início</span>
        </button>

        {/* Abas de Sessões Remotas Conectadas */}
        {sessions.map((sess) => {
          const isActive = activeTab === sess.id;
          const isConnected = sess.status === "connected";

          return (
            <div
              key={sess.id}
              onClick={() => onSelectTab(sess.id)}
              className={`group flex items-center space-x-2 px-3 py-1.5 rounded-md text-xs font-medium cursor-pointer transition-colors border ${
                isActive
                  ? "bg-slate-800 text-slate-50 border-slate-700 shadow-sm"
                  : "bg-slate-900/60 text-slate-400 hover:text-slate-200 hover:bg-slate-900 border-transparent"
              }`}
              title={`Sessão Remota: ${sess.hostId}`}
            >
              <div className="flex items-center space-x-1.5">
                <span
                  className={`w-2 h-2 rounded-full ${
                    isConnected
                      ? "bg-emerald-400 shadow-[0_0_8px_rgba(52,211,153,0.6)]"
                      : "bg-amber-400 animate-pulse"
                  }`}
                />
                <Monitor className="w-3.5 h-3.5 text-slate-400" />
                <span className="font-mono-tabular tracking-wide">{sess.label}</span>
              </div>

              {/* Botão Fechar Aba */}
              <button
                onClick={(e) => onCloseSession(sess.id, e)}
                className="p-0.5 rounded hover:bg-slate-700 text-slate-400 hover:text-slate-100 transition-colors ml-1"
                title="Desconectar sessão"
              >
                <X className="w-3 h-3" />
              </button>
            </div>
          );
        })}

        {/* Botão [ + ] para abrir nova conexão */}
        <button
          onClick={onNewSessionClick}
          className="flex items-center justify-center w-7 h-7 rounded-md text-slate-400 hover:text-slate-50 hover:bg-slate-800 border border-slate-800 hover:border-slate-700 transition-colors"
          title="Nova Conexão Remota [ + ]"
        >
          <Plus className="w-4 h-4" />
        </button>
      </div>

      {/* Indicador de Status Global do Signaling Server */}
      <div className="flex items-center space-x-2 pl-3 text-xs">
        {signalingConnected ? (
          <div className="flex items-center space-x-1.5 text-emerald-400">
            <Wifi className="w-3.5 h-3.5" />
            <span className="hidden sm:inline font-medium">Pronto</span>
          </div>
        ) : (
          <div className="flex items-center space-x-1.5 text-amber-400">
            <WifiOff className="w-3.5 h-3.5" />
            <span className="hidden sm:inline font-medium">Conectando...</span>
          </div>
        )}
      </div>
    </header>
  );
};
