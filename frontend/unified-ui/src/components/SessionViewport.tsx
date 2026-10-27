import React, { useRef, useEffect } from "react";
import { KeyRound, Eye, MousePointer, Power, Maximize, AlertCircle } from "lucide-react";
import type { RemoteSession } from "../types/protocol";
import { getNormalizedVideoCoords } from "../utils/coordinates";

interface SessionViewportProps {
  session: RemoteSession;
  stream: MediaStream | null;
  onSendPointerMove: (x: number, y: number) => void;
  onSendMouseButton: (b: 0 | 1 | 2, d: 0 | 1, x: number, y: number) => void;
  onSendMouseWheel: (dx: number, dy: number) => void;
  onSendKeyboard: (code: string, d: 0 | 1) => void;
  onToggleMode: () => void;
  onOpenUnattendedSetupModal: () => void;
  onDisconnect: () => void;
}

export const SessionViewport: React.FC<SessionViewportProps> = ({
  session,
  stream,
  onSendPointerMove,
  onSendMouseButton,
  onSendMouseWheel,
  onSendKeyboard,
  onToggleMode,
  onOpenUnattendedSetupModal,
  onDisconnect,
}) => {
  const videoRef = useRef<HTMLVideoElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);
  const lastMoveTs = useRef(0);

  // Vincula o MediaStream WebRTC ao elemento <video>
  useEffect(() => {
    if (videoRef.current && stream) {
      videoRef.current.srcObject = stream;
    }
  }, [stream]);

  // Captura de Teclado quando o viewport está focado
  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (session.mode === "view") return;
    e.preventDefault();
    onSendKeyboard(e.code, 1);
  };

  const handleKeyUp = (e: React.KeyboardEvent) => {
    if (session.mode === "view") return;
    e.preventDefault();
    onSendKeyboard(e.code, 0);
  };

  // Captura de Mouse com normalização e throttling de 60 Hz (16 ms)
  const handleMouseMove = (e: React.MouseEvent) => {
    if (session.mode === "view" || !videoRef.current) return;
    const now = performance.now();
    if (now - lastMoveTs.current < 16) return;
    lastMoveTs.current = now;

    const coords = getNormalizedVideoCoords(
      e.clientX,
      e.clientY,
      videoRef.current,
      session.remoteWidth || 1920,
      session.remoteHeight || 1080
    );

    if (coords) {
      onSendPointerMove(coords.x, coords.y);
    }
  };

  const handleMouseDown = (e: React.MouseEvent) => {
    if (session.mode === "view" || !videoRef.current) return;
    e.preventDefault();

    const coords = getNormalizedVideoCoords(
      e.clientX,
      e.clientY,
      videoRef.current,
      session.remoteWidth || 1920,
      session.remoteHeight || 1080
    );

    if (coords) {
      const btnMap: Record<number, 0 | 1 | 2> = { 0: 0, 1: 1, 2: 2 };
      const btn = btnMap[e.button] ?? 0;
      onSendMouseButton(btn, 1, coords.x, coords.y);
    }
  };

  const handleMouseUp = (e: React.MouseEvent) => {
    if (session.mode === "view" || !videoRef.current) return;
    e.preventDefault();

    const coords = getNormalizedVideoCoords(
      e.clientX,
      e.clientY,
      videoRef.current,
      session.remoteWidth || 1920,
      session.remoteHeight || 1080
    );

    if (coords) {
      const btnMap: Record<number, 0 | 1 | 2> = { 0: 0, 1: 1, 2: 2 };
      const btn = btnMap[e.button] ?? 0;
      onSendMouseButton(btn, 0, coords.x, coords.y);
    }
  };

  const handleWheel = (e: React.WheelEvent) => {
    if (session.mode === "view") return;
    e.preventDefault();
    const dy = e.deltaY < 0 ? 120 : -120;
    onSendMouseWheel(0, dy);
  };

  const handleToggleFullscreen = () => {
    if (!document.fullscreenElement) {
      containerRef.current?.requestFullscreen();
    } else {
      document.exitFullscreen();
    }
  };

  return (
    <div
      ref={containerRef}
      tabIndex={0}
      onKeyDown={handleKeyDown}
      onKeyUp={handleKeyUp}
      className="relative flex-1 bg-black overflow-hidden flex flex-col items-center justify-center outline-none select-none cursor-default"
    >
      {/* HUD Compacto Superior */}
      <div className="absolute top-3 z-30 flex items-center space-x-2 bg-slate-900/90 backdrop-blur border border-slate-700/80 px-3.5 py-1.5 rounded-full shadow-2xl text-xs text-slate-200">
        <div className="flex items-center space-x-2 pr-2 border-r border-slate-700">
          <span className="w-2 h-2 rounded-full bg-emerald-400" />
          <span className="font-mono-tabular font-semibold tracking-wide">
            {session.hostId}
          </span>
          <span className="text-[11px] text-slate-400 font-mono-tabular">
            • {session.rttMs} ms
          </span>
        </div>

        {/* Botão de Provisionamento Remoto de Senha Fixa (RF-H08 / RF-C04) */}
        <button
          onClick={onOpenUnattendedSetupModal}
          className="flex items-center space-x-1 px-2.5 py-1 rounded-full bg-slate-800 hover:bg-slate-700 border border-slate-600 text-indigo-300 font-medium transition-colors cursor-pointer"
          title="Criar Senha Fixa permanente neste host (exige aprovação física no computador parceiro)"
        >
          <KeyRound className="w-3.5 h-3.5 text-indigo-400" />
          <span className="text-[11px]">Criar Senha Fixa</span>
        </button>

        {/* Alternância Controle / Apenas Visualização */}
        <button
          onClick={onToggleMode}
          className={`flex items-center space-x-1 px-2.5 py-1 rounded-full text-[11px] font-medium transition-colors cursor-pointer ${
            session.mode === "control"
              ? "bg-indigo-600/30 text-indigo-300 border border-indigo-500/50"
              : "bg-amber-600/30 text-amber-300 border border-amber-500/50"
          }`}
          title="Alternar entre modo Controle Total e Apenas Visualização"
        >
          {session.mode === "control" ? (
            <>
              <MousePointer className="w-3.5 h-3.5" />
              <span>Controle</span>
            </>
          ) : (
            <>
              <Eye className="w-3.5 h-3.5" />
              <span>Visualização</span>
            </>
          )}
        </button>

        {/* Tela Cheia */}
        <button
          onClick={handleToggleFullscreen}
          className="p-1 rounded-full hover:bg-slate-800 text-slate-400 hover:text-slate-100 transition-colors cursor-pointer"
          title="Alternar Tela Cheia"
        >
          <Maximize className="w-3.5 h-3.5" />
        </button>

        {/* Botão Sair */}
        <button
          onClick={onDisconnect}
          className="flex items-center space-x-1 px-2.5 py-1 rounded-full bg-red-600/80 hover:bg-red-500 text-white font-semibold text-[11px] transition-colors cursor-pointer"
          title="Encerrar Sessão Remota"
        >
          <Power className="w-3.5 h-3.5" />
          <span>Sair</span>
        </button>
      </div>

      {/* Exibição de Status de Conexão ou Erro */}
      {session.status !== "connected" && (
        <div className="absolute inset-0 z-20 flex flex-col items-center justify-center bg-slate-950/90 text-center px-4">
          <div className="w-10 h-10 border-4 border-indigo-500 border-t-transparent rounded-full animate-spin mb-4" />
          <h3 className="text-sm font-semibold text-slate-100">
            {session.status === "connecting" && "Conectando ao Signaling Server..."}
            {session.status === "authenticating" && "Validando credencial no Host parceiro..."}
            {session.status === "error" && (
              <span className="text-red-400 flex items-center justify-center space-x-1.5">
                <AlertCircle className="w-4 h-4" />
                <span>{session.errorMessage || "Falha na conexão"}</span>
              </span>
            )}
          </h3>
          <p className="text-xs text-slate-400 mt-1 font-mono-tabular">ID: {session.hostId}</p>
        </div>
      )}

      {/* Elemento <video> com captura de mouse */}
      <video
        ref={videoRef}
        autoPlay
        playsInline
        muted
        onMouseMove={handleMouseMove}
        onMouseDown={handleMouseDown}
        onMouseUp={handleMouseUp}
        onWheel={handleWheel}
        onContextMenu={(e) => e.preventDefault()}
        className="w-full h-full object-contain cursor-crosshair pointer-events-auto"
      />
    </div>
  );
};
