<script>
    import Modal from "@components/base/Modal.svelte";

    export let id;

    let modalContent = `## Activity by sessions

When users complete a step in the georeferencing process, it is stored as a session, either a **Prep** (preparation) session or **Georef** (georeferencing) session. (For now, MultiMask trimming is not stored in sessions.)

This panel allows you to view all sessions that have been performed on _OldInsuranceMaps.net_ since the project began in early 2022. There are a few filtering methods you can use. Note that this session list appears in different contexts across the platform, and some filter methods are hidden in certain contexts.

- **Map** - All sessions across all resources within a specific map.
- **Type** - Only show Prep or Georef sessions (by default all are shown)
- **Date range** - spe

If you are looking for a list of the most recently added items (volumes), go to the [items page](/search#items)</a> and sort the table by **Load date**.

*More sophisticated filter and sort capabilities for this list are in the works. This data is also accessible via the [beta API](/api/beta/docs). Please [get in touch](/contact) if you would like a key for the API.*`
</script>

<Modal id={id} mdContent={modalContent} />
