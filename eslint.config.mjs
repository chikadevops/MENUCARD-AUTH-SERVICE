import globals from "globals";
import pluginJs from "@eslint/js";

/** @type {import('eslint').Linter.Config[]} */
export default [
  // Ignores configuration
  {
    ignores: [
      "**/node_modules/**",
      "**/dist/**",
      "**/coverage/**",
      "**/*.test.js",
      "**/*.spec.js",
      "**/tests/**",
      "**/__tests__/**"
    ]
  },

  // Main configuration for all JS files
  {
    files: ["**/*.{js,mjs,cjs}"],
    languageOptions: {
      ecmaVersion: 2021,
      sourceType: "module",
      globals: {
        ...globals.node,
        process: "readonly"
      }
    },
    rules: {
      "no-unused-vars": "warn"
    }
  },

  // CommonJS specific configuration
  {
    files: ["**/*.js"],
    languageOptions: {
      sourceType: "commonjs"
    }
  },

  pluginJs.configs.recommended
];