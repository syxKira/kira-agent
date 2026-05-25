import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it } from "vitest";

import { App } from "./App";

describe("App", () => {
  it("renders the welcome screen without backend events and enters the workbench", async () => {
    render(<App />);

    expect(screen.getByRole("heading", { name: "Kira Agent" })).toBeTruthy();
    expect(screen.getByRole("article", { name: "Kira agent" })).toBeTruthy();
    expect(screen.getAllByText("一个专业的数据agent助手").length).toBeGreaterThan(0);
    expect(screen.getByRole("button", { name: "立刻开始" })).toBeTruthy();
    expect(screen.queryByText("FastAPI local")).toBeNull();
    expect(screen.queryByText("Read-only context")).toBeNull();
    expect(screen.queryByText("Auto or fixture")).toBeNull();
    expect(screen.queryByText("Local Web Agent")).toBeNull();
    const shell = document.querySelector(".welcome-shell") as HTMLElement;
    const panel = document.querySelector(".welcome-panel") as HTMLElement;
    expect(shell.className).toContain("welcome-shell");
    expect(panel.className).toContain("welcome-panel");
    await userEvent.click(screen.getByRole("button", { name: "立刻开始" }));

    expect(screen.getByLabelText("Prompt")).toBeTruthy();
    expect(screen.getByText("Ask Kira to work with the local project.")).toBeTruthy();
  });
});
