import { afterEach, describe, expect, it, vi } from "vitest";
import { ApiError, createApiClient } from "./client";

describe("API client", () => {
  afterEach(() => vi.restoreAllMocks());

  it("adds the Cognito bearer token and returns envelope data", async () => {
    const fetchMock = vi.spyOn(globalThis, "fetch").mockResolvedValue(
      new Response(JSON.stringify({ data: [{ expense_id: "expense-1" }] }), {
        status: 200,
        headers: { "Content-Type": "application/json" },
      }),
    );
    const request = createApiClient(async () => "jwt-token");

    const data = await request<{ expense_id: string }[]>("/expenses");

    expect(data).toEqual([{ expense_id: "expense-1" }]);
    const headers = fetchMock.mock.calls[0][1]?.headers as Headers;
    expect(headers.get("Authorization")).toBe("Bearer jwt-token");
  });

  it("turns backend error envelopes into ApiError", async () => {
    vi.spyOn(globalThis, "fetch").mockResolvedValue(
      new Response(
        JSON.stringify({ error: { code: "BAD_REQUEST", message: "Invalid date" } }),
        { status: 400, headers: { "Content-Type": "application/json" } },
      ),
    );
    const request = createApiClient(async () => "jwt-token");

    await expect(request("/expenses")).rejects.toEqual(
      expect.objectContaining<ApiError>({
        name: "ApiError",
        message: "Invalid date",
        status: 400,
        code: "BAD_REQUEST",
      }),
    );
  });
});
