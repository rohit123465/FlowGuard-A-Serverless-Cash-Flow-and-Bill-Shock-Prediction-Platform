import { describe, expect, it } from "vitest";
import { isWebP } from "./receiptFiles";

describe("receipt file detection", () => {
  it("detects WebP content even when the filename says PNG", async () => {
    const file = new File([new TextEncoder().encode("RIFF1234WEBPVP8 ")], "receipt.png", { type: "image/png" });
    await expect(isWebP(file)).resolves.toBe(true);
  });

  it("does not classify a genuine PNG header as WebP", async () => {
    const file = new File([new Uint8Array([0x89, 0x50, 0x4e, 0x47, 0x0d, 0x0a, 0x1a, 0x0a])], "receipt.png", { type: "image/png" });
    await expect(isWebP(file)).resolves.toBe(false);
  });
});
