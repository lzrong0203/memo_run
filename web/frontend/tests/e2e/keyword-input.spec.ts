import { test, expect } from '@playwright/test'

test.describe('Keyword Input', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/')
    // Wait for the form to be fully rendered
    await expect(page.locator('#keywords')).toBeVisible()
  })

  test('keyword input field is present and focusable', async ({ page }) => {
    const input = page.locator('#keywords')
    await expect(input).toBeVisible()
    await expect(input).toBeEnabled()
    await expect(input).toHaveAttribute(
      'placeholder',
      'e.g. AI, blockchain, startup',
    )

    await input.focus()
    await expect(input).toBeFocused()
  })

  test('can type keywords into the input field', async ({ page }) => {
    const input = page.locator('#keywords')

    await input.fill('AI, blockchain, startup')
    await expect(input).toHaveValue('AI, blockchain, startup')
  })

  test('start button is disabled when input is empty', async ({ page }) => {
    const input = page.locator('#keywords')
    const startButton = page.locator('button', { hasText: 'Start Monitor' })

    // Initially empty -- button should be disabled
    await expect(input).toHaveValue('')
    await expect(startButton).toBeDisabled()
  })

  test('start button is enabled when input has text', async ({ page }) => {
    const input = page.locator('#keywords')
    const startButton = page.locator('button', { hasText: 'Start Monitor' })

    await input.fill('AI')
    await expect(startButton).toBeEnabled()
  })

  test('start button becomes disabled after clearing input', async ({ page }) => {
    const input = page.locator('#keywords')
    const startButton = page.locator('button', { hasText: 'Start Monitor' })

    // Type something first
    await input.fill('AI')
    await expect(startButton).toBeEnabled()

    // Clear the input
    await input.clear()
    await expect(startButton).toBeDisabled()
  })

  test('start button is disabled for whitespace-only input', async ({ page }) => {
    const input = page.locator('#keywords')
    const startButton = page.locator('button', { hasText: 'Start Monitor' })

    await input.fill('   ')
    await expect(startButton).toBeDisabled()
  })

  test('input has correct label', async ({ page }) => {
    const label = page.locator('label[for="keywords"]')
    await expect(label).toBeVisible()
    await expect(label).toHaveText('Keywords')
  })

  test('description text is visible', async ({ page }) => {
    const description = page.getByText(
      'Enter keywords separated by commas to monitor Threads posts.',
    )
    await expect(description).toBeVisible()
  })

  test('clicking start with keywords triggers API call', async ({ page }) => {
    const input = page.locator('#keywords')
    const startButton = page.locator('button', { hasText: 'Start Monitor' })

    // Intercept the API call (it will fail since backend is not running, but we can verify it was attempted)
    const apiPromise = page.waitForRequest(
      (request) =>
        request.url().includes('/api/monitor/start') &&
        request.method() === 'POST',
    )

    await input.fill('AI, blockchain')
    await startButton.click()

    // Verify the API was called with correct payload
    const request = await apiPromise
    const postData = request.postDataJSON()
    expect(postData).toEqual({ keywords: ['AI', 'blockchain'] })
  })

  test('after failed start, error state appears and reset button is visible', async ({
    page,
  }) => {
    const input = page.locator('#keywords')
    const startButton = page.locator('button', { hasText: 'Start Monitor' })

    await input.fill('test-keyword')
    await startButton.click()

    // Since backend is not running, the API call will fail
    // The error state should appear eventually
    const resetButton = page.locator('button', { hasText: 'Reset' })
    await expect(resetButton).toBeVisible({ timeout: 10000 })

    // There should be some error indication
    // The status is no longer 'idle', so the progress panel should be visible
    const progressSection = page.locator('h3', { hasText: 'Progress' })
    await expect(progressSection).toBeVisible()
  })

  test('reset button clears the progress state', async ({ page }) => {
    const input = page.locator('#keywords')
    const startButton = page.locator('button', { hasText: 'Start Monitor' })

    await input.fill('test-keyword')
    await startButton.click()

    // Wait for error/reset state
    const resetButton = page.locator('button', { hasText: 'Reset' })
    await expect(resetButton).toBeVisible({ timeout: 10000 })

    // Click reset
    await resetButton.click()

    // Progress panel should disappear
    await expect(resetButton).not.toBeVisible()
    const progressSection = page.locator('h3', { hasText: 'Progress' })
    await expect(progressSection).not.toBeVisible()

    // Start button should be visible again and input should still have the value
    await expect(
      page.locator('button', { hasText: 'Start Monitor' }),
    ).toBeVisible()
  })

  test('pressing Enter triggers start when input is filled', async ({
    page,
  }) => {
    const input = page.locator('#keywords')

    // Intercept the API call
    const apiPromise = page.waitForRequest(
      (request) =>
        request.url().includes('/api/monitor/start') &&
        request.method() === 'POST',
    )

    await input.fill('startup')
    await input.press('Enter')

    const request = await apiPromise
    const postData = request.postDataJSON()
    expect(postData).toEqual({ keywords: ['startup'] })
  })
})
