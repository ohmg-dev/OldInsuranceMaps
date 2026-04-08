# Contributing documentation

This documentation is built with [Zensical](https://zensical.org), and is very easy to work with locally. Once changes have been made to the source Markdown files and merged into the main branch, the published docs site at https://docs.oldinsurancemaps.net will be automatically rebuilt.

## Local install

1. Install [`uv`](https://docs.astral.sh/uv/getting-started/installation/) if you don't already have it.
2. Fork the [main repo on GitHub](https://github.com/ohmg-dev/OldInsuranceMaps), and then clone your fork of it:

    ```
    git clone https://github.com/<your gh username>/OldInsuranceMaps
    ```

3. Enter the repo directory and install `zensical`:

    ```
    cd OldInsuranceMaps
    uv venv
    uv pip install zensical
    ```

    If you are also creating a full installation of entire application, you can instead use this command to install the docs dependencies in addition to all others:

    ```
    uv sync --extra docs
    ```

4. Run the zensical server

    ```
    uv run zensical serve
    ```

You can now view the docs in a browser at `http://localhost:8000`.

## Editing content

All documention is written in Markdown (.md) files inside of the `/docs` directory. CSS modifications are in `docs/stylesheets/extra.css`.