<script>
  import '../../../../static/css/fancy-icons.css';

  export let icon;
  export let size = 'lg';
  export let link = '';
</script>

<i
  class="fancy fancy-{size} i-{icon} {link == 'enabled' ? ' link-enabled' : ''}{link == 'disabled'
    ? ' link-disabled'
    : ''}"
></i>
