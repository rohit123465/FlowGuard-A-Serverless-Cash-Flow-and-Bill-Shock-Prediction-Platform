export async function isWebP(file: File): Promise<boolean> {
  const buffer = await new Promise<ArrayBuffer>((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = () => resolve(reader.result as ArrayBuffer);
    reader.onerror = () => reject(new Error("The receipt file could not be read."));
    reader.readAsArrayBuffer(file.slice(0, 12));
  });
  const bytes = new Uint8Array(buffer);
  const text = String.fromCharCode(...bytes);
  return text.startsWith("RIFF") && text.slice(8, 12) === "WEBP";
}

export async function prepareReceiptFile(file: File): Promise<File> {
  if (!(await isWebP(file))) return file;

  const bitmap = await createImageBitmap(file);
  try {
    const canvas = document.createElement("canvas");
    canvas.width = bitmap.width;
    canvas.height = bitmap.height;
    const context = canvas.getContext("2d");
    if (!context) throw new Error("This browser could not convert the receipt image.");
    context.drawImage(bitmap, 0, 0);
    const blob = await new Promise<Blob>((resolve, reject) => {
      canvas.toBlob(
        (result) => result ? resolve(result) : reject(new Error("This browser could not convert the receipt image.")),
        "image/png",
      );
    });
    const baseName = file.name.replace(/\.[^.]+$/, "") || "receipt";
    return new File([blob], `${baseName}.png`, { type: "image/png", lastModified: file.lastModified });
  } finally {
    bitmap.close();
  }
}
