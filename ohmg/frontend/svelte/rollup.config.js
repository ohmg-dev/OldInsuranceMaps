import svelte from 'rollup-plugin-svelte';
import commonjs from '@rollup/plugin-commonjs';
import resolve from '@rollup/plugin-node-resolve';
import terser from '@rollup/plugin-terser';
import livereload from 'rollup-plugin-livereload';
import css from 'rollup-plugin-css-only';

const production = !process.env.ROLLUP_WATCH;

function serve() {
  let server;

  function toExit() {
    if (server) server.kill(0);
  }

  return {
    writeBundle() {
      if (server) return;
      server = require('child_process').spawn('npm', ['run', 'start', '--', '--dev'], {
        stdio: ['ignore', 'inherit', 'inherit'],
        shell: true,
      });

      process.on('SIGTERM', toExit);
      process.on('exit', toExit);
    },
  };
}

function componentExportDetails(componentName) {
  return {
    input: `./src/bundles/${componentName.toLowerCase()}.js`,
    output: {
      sourcemap: true,
      format: 'iife',
      name: `${componentName.toLowerCase()}`,
      file: `public/build/${componentName}.js`,
      inlineDynamicImports: true,
    },
    plugins: [
      svelte({
        compilerOptions: {
          // enable run-time checks when not in production
          dev: !production,
        },
      }),
      // we'll extract any component CSS out into
      // a separate file - better for performance
      css({ output: `${componentName}.css` }),

      // If you have external dependencies installed from
      // npm, you'll most likely need these plugins. In
      // some cases you'll need additional configuration -
      // consult the documentation for details:
      // https://github.com/rollup/plugins/tree/master/packages/commonjs
      resolve({
        browser: true,
        dedupe: ['svelte'],
        exportConditions: ['svelte'],
      }),
      commonjs(),

      // In dev mode, call `npm run start` once
      // the bundle has been generated
      !production && serve(),

      // Watch the `public` directory and refresh the
      // browser on changes when not in production
      !production && livereload('public'),

      // If we're building for production (npm run build
      // instead of npm run dev), minify
      production && terser(),
    ],
    watch: {
      clearScreen: false,
    },
    onwarn: function (warning, superOnWarn) {
      /*
       * skip certain warnings
       * https://github.com/openlayers/openlayers/issues/10245
       */
      if (warning.code === 'THIS_IS_UNDEFINED') {
        return;
      }
      superOnWarn(warning);
    },
  };
}

export default (cliArgs) => {
  // Add exportable to this array. These must match a lowercase file in ./src/bundles
  // e.g. ./src/bundles/main.js
  let exportable = [];

  if (cliArgs.configComponent) {
    // Only build one component if it has been specified in the configComponent arg
    exportable.push(componentExportDetails(cliArgs.configComponent));
  } else {
    // Otherwise build all components
    [
      'Index', // this forces prettier to multiline array
      'Georeference',
      'Resource',
      'Split',
      'Viewer',
      'Map',
      'SessionList',
    ].forEach((d) => exportable.push(componentExportDetails(d)));
  }

  return exportable;
};
