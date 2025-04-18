module.exports = {
  testEnvironment: 'node',
  coverageReporters: ['lcov', 'text', 'text-summary', 'html'],
  coverageThreshold: {
    global: {
      branches: 95,
      functions: 95,
      lines: 95,
      statements: 95,
    },
  },
};
