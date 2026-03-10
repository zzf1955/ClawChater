import { render, screen } from "@testing-library/react";
import App from "./App";

describe("App smoke", () => {
  it("renders core entry points", () => {
    render(<App />);

    expect(screen.getByRole("heading", { name: "Recall" })).toBeInTheDocument();
    expect(screen.getByText("Screenshot timeline")).toBeInTheDocument();
    expect(screen.getByText("Settings panel")).toBeInTheDocument();
    expect(screen.getByText("Summary explorer")).toBeInTheDocument();
  });
});
