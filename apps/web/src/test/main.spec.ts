import { beforeEach, describe, expect, it, vi } from "vitest";

const TOP_NAV_HEIGHT = 64;

const { appMountMock, appUseMock, createAppMock } = vi.hoisted(() => {
  const appUseMock = vi.fn();
  const appMountMock = vi.fn();
  const createAppMock = vi.fn(() => ({
    use: appUseMock,
    mount: appMountMock
  }));

  return {
    appMountMock,
    appUseMock,
    createAppMock
  };
});

vi.mock("vue", async () => {
  const actual = await vi.importActual<typeof import("vue")>("vue");

  return {
    ...actual,
    createApp: createAppMock
  };
});

describe("main bootstrap", () => {
  beforeEach(() => {
    appMountMock.mockClear();
    appUseMock.mockClear();
    createAppMock.mockClear();
    vi.resetModules();
  });

  it("configures Element Plus messages below the top navigation", async () => {
    await import("@/main");

    const elementPlusCall = appUseMock.mock.calls.find(
      ([, options]) => typeof options === "object" && options !== null && "locale" in options
    );

    expect(elementPlusCall).toBeDefined();
    expect(elementPlusCall?.[1]).toMatchObject({
      message: {
        offset: expect.any(Number)
      }
    });

    const options = elementPlusCall?.[1] as {
      message: {
        offset: number;
      };
    };

    expect(options.message.offset).toBeGreaterThan(TOP_NAV_HEIGHT);
    expect(appMountMock).toHaveBeenCalledWith("#app");
  });
});
