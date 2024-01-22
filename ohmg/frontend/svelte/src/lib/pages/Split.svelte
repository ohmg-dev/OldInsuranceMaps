<script>
  import TitleBar from '@components/layout/TitleBar.svelte';
  import Splitter from '@components/interfaces/Splitter.svelte';

  export let USER;
  export let SESSION_LENGTH;
  export let DOCUMENT;
  export let CSRFTOKEN;
  export let VOLUME;

  const iconLinks = [
    {
      visible: true,
      enabled: true,
      iconClass: 'document',
      alt: 'Go to document: ' + DOCUMENT.title,
      url: DOCUMENT.urls.resource,
    },
    {
      visible: true,
      enabled: false,
      iconClass: 'layer',
      alt: '',
      url: '',
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

<TitleBar TITLE={DOCUMENT.title} SIDE_LINKS={[]} ICON_LINKS={iconLinks}/>
<Splitter USER={USER}
  SESSION_LENGTH={SESSION_LENGTH}
  DOCUMENT={DOCUMENT}
  CSRFTOKEN={CSRFTOKEN}
  VOLUME={VOLUME}
  />
