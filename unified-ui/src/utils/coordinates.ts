/**
 * Normaliza as coordenadas de clique/mouse para [0.0000 .. 1.0000]
 * baseado na proporção útil da imagem de vídeo (object-fit: contain),
 * retornando null se o ponteiro estiver em barras pretas (letterbox/pillarbox).
 */
export function getNormalizedVideoCoords(
  clientX: number,
  clientY: number,
  videoElement: HTMLVideoElement,
  remoteWidth: number,
  remoteHeight: number
): { x: number; y: number } | null {
  const rect = videoElement.getBoundingClientRect();
  const elemW = rect.width;
  const elemH = rect.height;

  if (elemW <= 0 || elemH <= 0 || remoteWidth <= 0 || remoteHeight <= 0) {
    return null;
  }

  const scale = Math.min(elemW / remoteWidth, elemH / remoteHeight);
  const activeW = remoteWidth * scale;
  const activeH = remoteHeight * scale;

  const offsetX = (elemW - activeW) / 2;
  const offsetY = (elemH - activeH) / 2;

  const relX = clientX - rect.left;
  const relY = clientY - rect.top;

  // Verifica se está dentro da área útil do vídeo
  if (
    relX < offsetX ||
    relX > offsetX + activeW ||
    relY < offsetY ||
    relY > offsetY + activeH
  ) {
    return null; // Clique na barra preta (letterbox / pillarbox)
  }

  const normX = Math.max(0, Math.min(1, (relX - offsetX) / activeW));
  const normY = Math.max(0, Math.min(1, (relY - offsetY) / activeH));

  return {
    x: Number(normX.toFixed(4)),
    y: Number(normY.toFixed(4)),
  };
}
