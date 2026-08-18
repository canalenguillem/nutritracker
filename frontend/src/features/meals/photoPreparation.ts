const MAX_EDGE_PIXELS = 1600;
const JPEG_QUALITY = 0.85;

/**
 * Shrink a photograph before sending it.
 *
 * A phone camera writes several megabytes, enough to be refused by the upload
 * limit and slow over mobile data, while the printed label stays perfectly
 * legible at this size.
 */
export const preparePhoto = async (file: File): Promise<File> => {
  if (typeof createImageBitmap !== "function") {
    return file;
  }

  try {
    // Honour the orientation the camera recorded, or a portrait shot arrives sideways.
    const bitmap = await createImageBitmap(file, { imageOrientation: "from-image" });
    const longestEdge = Math.max(bitmap.width, bitmap.height);
    const scale = longestEdge > MAX_EDGE_PIXELS ? MAX_EDGE_PIXELS / longestEdge : 1;
    const width = Math.round(bitmap.width * scale);
    const height = Math.round(bitmap.height * scale);

    const canvas = document.createElement("canvas");
    canvas.width = width;
    canvas.height = height;
    const context = canvas.getContext("2d");
    if (!context) {
      bitmap.close();
      return file;
    }

    context.drawImage(bitmap, 0, 0, width, height);
    bitmap.close();

    const blob = await new Promise<Blob | null>((resolve) => {
      canvas.toBlob(resolve, "image/jpeg", JPEG_QUALITY);
    });

    if (!blob || blob.size >= file.size) {
      return file;
    }

    return new File([blob], "etiqueta.jpg", { type: "image/jpeg" });
  } catch {
    // A format the browser cannot decode still goes up as it came.
    return file;
  }
};

export const formatFileSize = (bytes: number): string => {
  const megabytes = bytes / (1024 * 1024);
  if (megabytes >= 1) {
    return `${new Intl.NumberFormat("es-ES", { maximumFractionDigits: 1 }).format(megabytes)} MB`;
  }
  return `${Math.round(bytes / 1024)} kB`;
};
