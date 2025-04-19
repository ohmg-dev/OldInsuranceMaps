module.exports = {
    extends: [
        'plugin:svelte/recommended',
        'prettier',
    ],
    parser: '@babel/eslint-parser',
    parserOptions: {
        requireConfigFile: false,
        ecmaVersion: 8
    },
    // Add an `overrides` section to add a parser configuration for svelte.
    overrides: [
        {
            files: ['*.svelte'],
            parser: 'svelte-eslint-parser'
        }
    ]
};