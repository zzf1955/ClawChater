import { expect, test } from "@playwright/test";

test("query screenshots then preview image", async ({ page }) => {
  await page.route("**/api/screenshots?**", async (route) => {
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify([
        {
          id: 1,
          captured_at: "2026-03-10T08:00:00Z",
          file_path: "screenshots/2026-03-10/08/1.jpg",
          ocr_text: "draft notes",
          ocr_status: "done",
          window_title: "Terminal",
          process_name: "iTerm2",
        },
      ]),
    });
  });

  await page.route("**/api/screenshots/1", async (route) => {
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({
        id: 1,
        captured_at: "2026-03-10T08:00:00Z",
        file_path: "screenshots/2026-03-10/08/1.jpg",
        ocr_text: "draft notes",
        ocr_status: "done",
        window_title: "Terminal",
        process_name: "iTerm2",
      }),
    });
  });

  await page.route("**/api/screenshots/1/image", async (route) => {
    await route.fulfill({
      status: 200,
      contentType: "image/gif",
      body: Buffer.from("R0lGODlhAQABAIAAAAAAAP///ywAAAAAAQABAAACAUwAOw==", "base64"),
    });
  });

  await page.goto("/");
  await expect(page.getByRole("heading", { name: "截图列表" })).toBeVisible();
  await page.getByRole("button", { name: "查看详情" }).click();
  await expect(page.getByTestId("screenshot-detail")).toBeVisible();
  await expect(page.getByAltText("Screenshot preview")).toBeVisible();
});
