<script>
  import TitleBar from '@components/layout/TitleBar.svelte';
  import Georeferencer from '@components/interfaces/Georeferencer.svelte';

  export let CONTEXT;
  export let REGION;
  export let VOLUME;
  export let ANNOSET_MAIN;
  export let ANNOSET_KEYMAP;

  const iconLinks = [
    {
      visible: true,
      enabled: true,
      iconClass: 'document',
      alt: 'Go to document: ' + REGION.title,
      url: REGION.urls.resource,
    },
    {
      visible: true,
      enabled: REGION.layer ? true : false,
      iconClass: 'layer',
      alt: REGION.layer ? 'Go to layer: ' + REGION.layer.title : 'Layer not yet made',
      url: REGION.layer ? REGION.layer.urls.resource : '',
    },
    {
      visible: true,
      enabled: true,
      iconClass: 'volume',
      alt: 'Go to volume: ' + VOLUME.title,
      url: VOLUME.urls.summary,
    }
  ]

</script>

<TitleBar TITLE={REGION.title} ICON_LINKS={iconLinks}/>
<Georeferencer {CONTEXT} {REGION} {VOLUME} {ANNOSET_MAIN} {ANNOSET_KEYMAP} />
