import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import App from "./App";

function jsonResponse(payload: unknown, status = 200): Response {
  return new Response(JSON.stringify(payload), {
    status,
    headers: {
      "Content-Type": "application/json",
    },
  });
}

describe("App", () => {
  beforeEach(() => {
    window.history.pushState({}, "", "/screenshots");
  });

  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it("submits screenshot filters", async () => {
    const fetchMock = vi.fn(async () => jsonResponse([]));
    vi.stubGlobal("fetch", fetchMock);

    render(<App />);
    await waitFor(() => expect(fetchMock).toHaveBeenCalledTimes(1));

    const limitInput = screen.getByLabelText("条数");
    fireEvent.change(limitInput, { target: { value: "20" } });
    await userEvent.click(screen.getByRole("button", { name: "查询截图" }));

    await waitFor(() => expect(fetchMock).toHaveBeenCalledTimes(2));
    const queryUrl = fetchMock.mock.calls[1][0]?.toString() ?? "";
    expect(queryUrl).toContain("/api/screenshots?");
    expect(queryUrl).toContain("limit=20");
  });

  it("submits updated config values", async () => {
    const fetchMock = vi.fn(async (input: RequestInfo | URL, init?: RequestInit) => {
      const url = input.toString();
      if (url.includes("/api/config") && init?.method === "POST") {
        return jsonResponse({ OCR_BATCH_SIZE: "12" });
      }
      if (url.includes("/api/config")) {
        return jsonResponse({ OCR_BATCH_SIZE: "10" });
      }
      if (url.includes("/api/screenshots")) {
        return jsonResponse([]);
      }
      return jsonResponse([]);
    });
    vi.stubGlobal("fetch", fetchMock);

    render(<App />);
    await userEvent.click(screen.getByRole("link", { name: "配置编辑" }));
    const input = await screen.findByDisplayValue("10");
    await userEvent.clear(input);
    await userEvent.type(input, "12");
    await userEvent.click(screen.getByRole("button", { name: "保存配置" }));

    await screen.findByText("配置已更新");
    const postCall = fetchMock.mock.calls.find((call) => call[1]?.method === "POST");
    expect(postCall).toBeTruthy();
    expect(postCall?.[1]?.body).toContain("12");
  });

  it("shows error message when screenshot query fails", async () => {
    const fetchMock = vi.fn(async () => jsonResponse({ detail: "invalid range" }, 422));
    vi.stubGlobal("fetch", fetchMock);

    render(<App />);

    await screen.findByText("invalid range");
  });
});
