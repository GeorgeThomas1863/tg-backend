import { describe, test, expect, vi, beforeEach } from "vitest";
import { renderHook, waitFor, act } from "@testing-library/react";
import { useVideos } from "./useVideos";
import { fetchVideos } from "../api/client";

vi.mock("../api/client", () => ({
  fetchVideos: vi.fn(),
}));

function buildHttpError(status) {
  const error = new Error(`HTTP ${status}`);
  error.status = status;
  return error;
}

beforeEach(() => {
  fetchVideos.mockReset();
});

describe("useVideos", () => {
  test("sets videos and loading=false on successful fetch", async () => {
    const videos = [{ id: 1 }, { id: 2 }];
    fetchVideos.mockResolvedValue(videos);

    const { result } = renderHook(() => useVideos());

    expect(result.current.loading).toBe(true);
    await waitFor(() => expect(result.current.loading).toBe(false));
    expect(result.current.videos).toEqual(videos);
    expect(result.current.error).toBeNull();
    expect(result.current.unauthorized).toBe(false);
  });

  test("sets unauthorized=true and NOT a generic error when fetch rejects with .status 401", async () => {
    fetchVideos.mockRejectedValue(buildHttpError(401));

    const { result } = renderHook(() => useVideos());

    await waitFor(() => expect(result.current.loading).toBe(false));
    expect(result.current.unauthorized).toBe(true);
    expect(result.current.error).toBeNull();
  });

  test("sets error message and unauthorized stays false on a non-401 failure", async () => {
    fetchVideos.mockRejectedValue(buildHttpError(500));

    const { result } = renderHook(() => useVideos());

    await waitFor(() => expect(result.current.loading).toBe(false));
    expect(result.current.error).toBe("HTTP 500");
    expect(result.current.unauthorized).toBe(false);
  });

  test("refetch() triggers a new fetch and recovers after a prior error", async () => {
    const videos = [{ id: 3 }];
    fetchVideos.mockRejectedValueOnce(buildHttpError(500)).mockResolvedValueOnce(videos);

    const { result } = renderHook(() => useVideos());
    await waitFor(() => expect(result.current.error).toBe("HTTP 500"));

    act(() => result.current.refetch());

    await waitFor(() => expect(result.current.loading).toBe(false));
    expect(fetchVideos).toHaveBeenCalledTimes(2);
    expect(result.current.videos).toEqual(videos);
    expect(result.current.error).toBeNull();
    expect(result.current.unauthorized).toBe(false);
  });
});
