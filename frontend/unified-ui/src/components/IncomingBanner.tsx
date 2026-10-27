import React from "react";
import { AlertTriangle, Power } from "lucide-react";

interface IncomingBannerProps {
  clientIp: string;
  onDisconnect: () => void;
}

export const IncomingBanner: React.FC<IncomingBannerProps> = ({
  clientIp,
  onDisconnect,
}) => {
  return (
    <div className="h-10 bg-red-950/90 border-b border-red-800/80 px-4 flex items-center justify-between text-red-200 select-none animate-in fade-in duration-200">
      <div className="flex items-center space-x-2 text-xs font-semibold">
        <span className="w-2.5 h-2.5 rounded-full bg-red-500 animate-ping" />
        <AlertTriangle className="w-4 h-4 text-red-400" />
        <span>
          Acesso remoto em andamento neste computador por{" "}
          <strong className="text-white font-mono-tabular">[{clientIp}]</strong>
        </span>
        <span className="hidden md:inline text-red-300 font-normal">
          (Kill Switch físico: <kbd className="bg-red-900/80 px-1.5 py-0.5 rounded text-[11px] font-mono text-red-100">Ctrl+Alt+Shift+Q</kbd>)
        </span>
      </div>

      <button
        onClick={onDisconnect}
        className="flex items-center space-x-1.5 bg-red-600 hover:bg-red-500 active:bg-red-700 text-white text-xs font-semibold px-3 py-1 rounded-md shadow transition-colors cursor-pointer"
        title="Encerrar conexão remota recebida imediatamente"
      >
        <Power className="w-3.5 h-3.5" />
        <span>Desconectar</span>
      </button>
    </div>
  );
};
