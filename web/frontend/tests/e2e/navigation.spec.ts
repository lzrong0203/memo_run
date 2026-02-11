import { test, expect } from '@playwright/test'

test.describe('Navigation', () => {
  test('app loads with correct title', async ({ page }) => {
    await page.goto('/')
    await expect(page).toHaveTitle('Threads Monitor Dashboard')
  })

  test('navbar shows brand and nav links', async ({ page }) => {
    await page.goto('/')

    // Brand link
    const brand = page.locator('nav a', { hasText: 'Threads Monitor' })
    await expect(brand).toBeVisible()
    await expect(brand).toHaveAttribute('href', '/')

    // Navigation links
    const monitorLink = page.locator('nav a', { hasText: /^Monitor$/ })
    const historyLink = page.locator('nav a', { hasText: 'History' })
    await expect(monitorLink).toBeVisible()
    await expect(historyLink).toBeVisible()
  })

  test('home page renders the keyword input form', async ({ page }) => {
    await page.goto('/')

    // The "Start Monitoring" heading should be visible
    await expect(page.locator('h2', { hasText: 'Start Monitoring' })).toBeVisible()

    // The keyword input should be present
    await expect(page.locator('#keywords')).toBeVisible()

    // The start button should be present
    await expect(page.locator('button', { hasText: 'Start Monitor' })).toBeVisible()
  })

  test('clicking History link navigates to /history', async ({ page }) => {
    await page.goto('/')

    const historyLink = page.locator('nav a', { hasText: 'History' })
    await historyLink.click()

    await expect(page).toHaveURL(/\/history/)

    // The History page heading should appear
    // It will either show "Run History" or a loading/error state
    // (since the backend is not running, we may see the error or the heading briefly)
    const heading = page.locator('h2', { hasText: 'Run History' })
    const errorSection = page.locator('h3', { hasText: 'Error' })
    const loadingText = page.getByText('Loading history...')

    // At least one of these should be visible - the page rendered
    await expect(heading.or(errorSection).or(loadingText)).toBeVisible()
  })

  test('clicking Monitor link navigates back to /', async ({ page }) => {
    await page.goto('/history')

    const monitorLink = page.locator('nav a', { hasText: /^Monitor$/ })
    await monitorLink.click()

    await expect(page).toHaveURL(/^\/$|localhost:\d+\/$/)

    await expect(page.locator('h2', { hasText: 'Start Monitoring' })).toBeVisible()
  })

  test('clicking brand logo navigates to home', async ({ page }) => {
    await page.goto('/history')

    const brand = page.locator('nav a', { hasText: 'Threads Monitor' })
    await brand.click()

    await expect(page).toHaveURL(/^\/$|localhost:\d+\/$/)
    await expect(page.locator('h2', { hasText: 'Start Monitoring' })).toBeVisible()
  })

  test('active nav link has distinct styling', async ({ page }) => {
    await page.goto('/')

    // The "Monitor" link should have active styling (bg-gray-900)
    const monitorLink = page.locator('nav a', { hasText: /^Monitor$/ })
    await expect(monitorLink).toHaveClass(/bg-gray-900/)

    // The "History" link should NOT have active styling
    const historyLink = page.locator('nav a', { hasText: 'History' })
    await expect(historyLink).not.toHaveClass(/bg-gray-900/)
  })

  test('navigating to /history updates active link styling', async ({ page }) => {
    await page.goto('/history')

    // History should be active
    const historyLink = page.locator('nav a', { hasText: 'History' })
    await expect(historyLink).toHaveClass(/bg-gray-900/)

    // Monitor should not be active
    const monitorLink = page.locator('nav a', { hasText: /^Monitor$/ })
    await expect(monitorLink).not.toHaveClass(/bg-gray-900/)
  })

  test('unknown route still renders the app shell', async ({ page }) => {
    await page.goto('/some-nonexistent-page')

    // The navbar should still render
    await expect(page.locator('nav a', { hasText: 'Threads Monitor' })).toBeVisible()

    // Neither Monitor nor History should be marked active
    const monitorLink = page.locator('nav a', { hasText: /^Monitor$/ })
    const historyLink = page.locator('nav a', { hasText: 'History' })
    await expect(monitorLink).not.toHaveClass(/bg-gray-900/)
    await expect(historyLink).not.toHaveClass(/bg-gray-900/)
  })
})
