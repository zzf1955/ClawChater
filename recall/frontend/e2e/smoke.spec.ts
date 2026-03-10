import { expect, test } from "@playwright/test";

test("home page smoke", async ({ page }) => {
  await page.goto("/");

  await expect(page.getByRole("heading", { name: "Recall" })).toBeVisible();
  await expect(page.getByText("Screenshot timeline")).toBeVisible();
  await expect(page.getByText("Settings panel")).toBeVisible();
  await expect(page.getByText("Summary explorer")).toBeVisible();
});
