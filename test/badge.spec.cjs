const {test, expect} = require('@playwright/test');
const {run} = require('ormas_acceptance');

test('badge shows the unread count', async ({page}) => {
  const r = await run(['node', 'src/badge.cjs', '3']);
  expect(r.returncode).toBe(0);
  await page.setContent('<main>' + r.output + '</main>');
  await expect(page.locator('.badge')).toHaveText('3 new');
});
test('badge is absent at zero', async ({page}) => {
  const r = await run(['node', 'src/badge.cjs', '0']);
  expect(r.returncode).toBe(0);
  await page.setContent('<main>' + r.output + '</main>');
  await expect(page.locator('.badge')).toHaveCount(0);
});
