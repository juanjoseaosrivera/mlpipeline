import { defineConfig } from 'vitest/config';

export default defineConfig({
  test: {
    coverage: {
      provider: 'v8',
      reporter: ['text', 'json-summary', 'lcov'],
      reportsDirectory: 'coverage',
      thresholds: {
        lines: 80,
        functions: 80,
        branches: 80,
        statements: 80,
      },
      exclude: [
        'node_modules/**',
        '.angular/**',
        'dist/**',
        'coverage/**',
        '**/*.spec.ts',
        '**/*.d.ts',
        'src/main.ts',
        'src/environments/**',
        'vitest.config.ts',
      ],
    },
  },
});
