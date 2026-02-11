import { test, expect } from '@playwright/test'

test.describe('History Page', () => {
  test('navigating to /history renders the page', async ({ page }) => {
    await page.goto('/history')

    // The page should show loading state first, then either content or error
    // (backend is not running so we expect an error eventually)
    const heading = page.locator('h2', { hasText: 'Run History' })
    const errorSection = page.locator('h3', { hasText: 'Error' })
    const loadingText = page.getByText('Loading history...')

    // First check: one of these should appear
    await expect(heading.or(errorSection).or(loadingText)).toBeVisible({
      timeout: 10000,
    })
  })

  test('shows loading state initially', async ({ page }) => {
    // Intercept the API call and delay it so we can observe loading
    await page.route('**/api/history*', async (route) => {
      // Hold the request for 2 seconds to observe loading state
      await new Promise((resolve) => setTimeout(resolve, 2000))
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ runs: [], total: 0, page: 1, limit: 20 }),
      })
    })

    await page.goto('/history')

    // Loading state should appear
    await expect(page.getByText('Loading history...')).toBeVisible()
  })

  test('shows empty state when no runs exist', async ({ page }) => {
    // Mock the API to return empty results
    await page.route('**/api/history*', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ runs: [], total: 0, page: 1, limit: 20 }),
      })
    })

    await page.goto('/history')

    // Wait for the empty state message
    const emptyMessage = page.getByText('No runs yet.')
    await expect(emptyMessage).toBeVisible()

    // The "home page" link should be present in the empty state
    const homeLink = page.locator('a', { hasText: 'home page' })
    await expect(homeLink).toBeVisible()
    await expect(homeLink).toHaveAttribute('href', '/')
  })

  test('empty state link navigates to home', async ({ page }) => {
    await page.route('**/api/history*', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ runs: [], total: 0, page: 1, limit: 20 }),
      })
    })

    await page.goto('/history')
    await expect(page.getByText('No runs yet.')).toBeVisible()

    // Click the home link
    await page.locator('a', { hasText: 'home page' }).click()
    await expect(page).toHaveURL(/^\/$|localhost:\d+\/$/)
    await expect(page.locator('h2', { hasText: 'Start Monitoring' })).toBeVisible()
  })

  test('shows error state when API fails', async ({ page }) => {
    // Mock the API to return an error
    await page.route('**/api/history*', async (route) => {
      await route.fulfill({
        status: 500,
        contentType: 'application/json',
        body: JSON.stringify({ detail: 'Internal server error' }),
      })
    })

    await page.goto('/history')

    // Error section should appear
    const errorHeading = page.locator('h3', { hasText: 'Error' })
    await expect(errorHeading).toBeVisible({ timeout: 10000 })
  })

  test('displays runs in a table when data exists', async ({ page }) => {
    const mockRuns = [
      {
        id: '550e8400-e29b-41d4-a716-446655440001',
        status: 'completed',
        keywords: ['AI', 'blockchain'],
        created_at: '2026-02-10T12:00:00Z',
        completed_at: '2026-02-10T12:05:00Z',
        stats: { valid_count: 15 },
      },
      {
        id: '550e8400-e29b-41d4-a716-446655440002',
        status: 'failed',
        keywords: ['startup', 'tech', 'innovation', 'web3'],
        created_at: '2026-02-10T11:00:00Z',
        completed_at: null,
        stats: null,
      },
    ]

    await page.route('**/api/history*', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          runs: mockRuns,
          total: 2,
          page: 1,
          limit: 20,
        }),
      })
    })

    await page.goto('/history')

    // Page heading
    await expect(page.locator('h2', { hasText: 'Run History' })).toBeVisible()

    // Table headers
    await expect(page.locator('th', { hasText: 'Run ID' })).toBeVisible()
    await expect(page.locator('th', { hasText: 'Status' })).toBeVisible()
    await expect(page.locator('th', { hasText: 'Keywords' })).toBeVisible()
    await expect(page.locator('th', { hasText: 'Posts' })).toBeVisible()
    await expect(page.locator('th', { hasText: 'Created' })).toBeVisible()

    // Table rows
    const rows = page.locator('tbody tr')
    await expect(rows).toHaveCount(2)

    // First row: completed run
    const firstRow = rows.nth(0)
    await expect(firstRow.locator('a')).toContainText('550e8400')
    await expect(firstRow).toContainText('completed')
    await expect(firstRow).toContainText('AI')
    await expect(firstRow).toContainText('blockchain')
    await expect(firstRow).toContainText('15')

    // Second row: failed run, truncated keywords (>3)
    const secondRow = rows.nth(1)
    await expect(secondRow).toContainText('failed')
    await expect(secondRow).toContainText('startup')
    await expect(secondRow).toContainText('+1') // 4 keywords, showing 3 + "+1"
    await expect(secondRow).toContainText('-') // null stats
  })

  test('run ID links to the correct run detail page', async ({ page }) => {
    const runId = '550e8400-e29b-41d4-a716-446655440001'
    await page.route('**/api/history*', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          runs: [
            {
              id: runId,
              status: 'completed',
              keywords: ['AI'],
              created_at: '2026-02-10T12:00:00Z',
              completed_at: '2026-02-10T12:05:00Z',
              stats: { valid_count: 5 },
            },
          ],
          total: 1,
          page: 1,
          limit: 20,
        }),
      })
    })

    await page.goto('/history')
    await expect(page.locator('tbody tr')).toHaveCount(1)

    // The run ID link should point to the correct run detail page
    const runLink = page.locator('tbody tr a').first()
    await expect(runLink).toHaveAttribute('href', `/run/${runId}`)
  })

  test('pagination controls appear when there are multiple pages', async ({
    page,
  }) => {
    const mockRuns = Array.from({ length: 20 }, (_, i) => ({
      id: `550e8400-e29b-41d4-a716-4466554400${String(i).padStart(2, '0')}`,
      status: 'completed',
      keywords: [`keyword-${i}`],
      created_at: `2026-02-10T${String(i).padStart(2, '0')}:00:00Z`,
      completed_at: `2026-02-10T${String(i).padStart(2, '0')}:05:00Z`,
      stats: { valid_count: i + 1 },
    }))

    await page.route('**/api/history*', async (route) => {
      const url = new URL(route.request().url())
      const requestPage = parseInt(url.searchParams.get('page') ?? '1')

      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          runs: requestPage === 1 ? mockRuns : mockRuns.slice(0, 5),
          total: 45, // More than one page worth
          page: requestPage,
          limit: 20,
        }),
      })
    })

    await page.goto('/history')

    // Wait for data to load
    await expect(page.locator('tbody tr').first()).toBeVisible()

    // Pagination info
    await expect(page.getByText('Page 1 of 3')).toBeVisible()
    await expect(page.getByText('45 total runs')).toBeVisible()

    // Previous should be disabled on first page
    const prevButton = page.locator('button', { hasText: 'Previous' })
    const nextButton = page.locator('button', { hasText: 'Next' })
    await expect(prevButton).toBeDisabled()
    await expect(nextButton).toBeEnabled()
  })

  test('clicking Next loads the next page', async ({ page }) => {
    let requestedPage = 0

    await page.route('**/api/history*', async (route) => {
      const url = new URL(route.request().url())
      requestedPage = parseInt(url.searchParams.get('page') ?? '1')

      const mockRuns = Array.from({ length: 5 }, (_, i) => ({
        id: `550e8400-e29b-41d4-a716-44665544${String(requestedPage).padStart(2, '0')}${String(i).padStart(2, '0')}`,
        status: 'completed',
        keywords: [`page${requestedPage}-kw${i}`],
        created_at: '2026-02-10T12:00:00Z',
        completed_at: '2026-02-10T12:05:00Z',
        stats: { valid_count: requestedPage * 10 + i },
      }))

      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          runs: mockRuns,
          total: 45,
          page: requestedPage,
          limit: 20,
        }),
      })
    })

    await page.goto('/history')
    await expect(page.locator('tbody tr').first()).toBeVisible()
    await expect(page.getByText('Page 1 of 3')).toBeVisible()

    // Click Next
    await page.locator('button', { hasText: 'Next' }).click()

    // Wait for page 2
    await expect(page.getByText('Page 2 of 3')).toBeVisible()

    // Previous should now be enabled
    await expect(page.locator('button', { hasText: 'Previous' })).toBeEnabled()
  })

  test('no pagination controls when only one page', async ({ page }) => {
    await page.route('**/api/history*', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          runs: [
            {
              id: '550e8400-e29b-41d4-a716-446655440001',
              status: 'completed',
              keywords: ['AI'],
              created_at: '2026-02-10T12:00:00Z',
              completed_at: '2026-02-10T12:05:00Z',
              stats: { valid_count: 5 },
            },
          ],
          total: 1,
          page: 1,
          limit: 20,
        }),
      })
    })

    await page.goto('/history')
    await expect(page.locator('tbody tr')).toHaveCount(1)

    // Pagination buttons should not be visible
    await expect(
      page.locator('button', { hasText: 'Previous' }),
    ).not.toBeVisible()
    await expect(page.locator('button', { hasText: 'Next' })).not.toBeVisible()
  })

  test('status badges have correct styling', async ({ page }) => {
    await page.route('**/api/history*', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          runs: [
            {
              id: '550e8400-e29b-41d4-a716-446655440001',
              status: 'completed',
              keywords: ['AI'],
              created_at: '2026-02-10T12:00:00Z',
              completed_at: '2026-02-10T12:05:00Z',
              stats: { valid_count: 5 },
            },
            {
              id: '550e8400-e29b-41d4-a716-446655440002',
              status: 'failed',
              keywords: ['test'],
              created_at: '2026-02-10T11:00:00Z',
              completed_at: null,
              stats: null,
            },
            {
              id: '550e8400-e29b-41d4-a716-446655440003',
              status: 'running',
              keywords: ['web3'],
              created_at: '2026-02-10T10:00:00Z',
              completed_at: null,
              stats: null,
            },
          ],
          total: 3,
          page: 1,
          limit: 20,
        }),
      })
    })

    await page.goto('/history')
    await expect(page.locator('tbody tr')).toHaveCount(3)

    // Completed badge should have green styling
    const completedBadge = page.locator('span', { hasText: 'completed' })
    await expect(completedBadge).toHaveClass(/bg-green-100/)
    await expect(completedBadge).toHaveClass(/text-green-800/)

    // Failed badge should have red styling
    const failedBadge = page.locator('span', { hasText: 'failed' })
    await expect(failedBadge).toHaveClass(/bg-red-100/)
    await expect(failedBadge).toHaveClass(/text-red-800/)

    // Running badge should have blue styling
    const runningBadge = page.locator('span', { hasText: 'running' })
    await expect(runningBadge).toHaveClass(/bg-blue-100/)
    await expect(runningBadge).toHaveClass(/text-blue-800/)
  })
})
