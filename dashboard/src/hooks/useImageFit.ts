import { useState, useEffect, useCallback, type RefObject } from 'react';

interface ImageFit {
  offsetX: number;
  offsetY: number;
  width: number;
  height: number;
}

/**
 * Berechnet die tatsaechliche Bildflaeche eines object-contain <img>
 * innerhalb seines Containers (beruecksichtigt Letterboxing/Pillarboxing).
 */
export function useImageFit(
  containerRef: RefObject<HTMLDivElement | null>,
  imgRef: RefObject<HTMLImageElement | null>,
): ImageFit {
  const [fit, setFit] = useState<ImageFit>({ offsetX: 0, offsetY: 0, width: 0, height: 0 });

  const recalc = useCallback(() => {
    const container = containerRef.current;
    const img = imgRef.current;
    if (!container || !img || !img.naturalWidth || !img.naturalHeight) {
      return;
    }
    const cw = container.clientWidth;
    const ch = container.clientHeight;
    const nw = img.naturalWidth;
    const nh = img.naturalHeight;

    const scale = Math.min(cw / nw, ch / nh);
    const w = nw * scale;
    const h = nh * scale;
    const ox = (cw - w) / 2;
    const oy = (ch - h) / 2;

    setFit((prev) => {
      if (prev.offsetX === ox && prev.offsetY === oy && prev.width === w && prev.height === h) {
        return prev;
      }
      return { offsetX: ox, offsetY: oy, width: w, height: h };
    });
  }, [containerRef, imgRef]);

  useEffect(() => {
    const container = containerRef.current;
    if (!container) return;

    const ro = new ResizeObserver(recalc);
    ro.observe(container);
    recalc();

    return () => ro.disconnect();
  }, [containerRef, recalc]);

  return fit;
}
