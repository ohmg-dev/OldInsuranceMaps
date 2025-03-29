<script>
    import '../css/shared.css'
    import Browse from './overviews/Browse.svelte'
    import Home from './overviews/Home.svelte'
    import Place from './overviews/Place.svelte'
    import Profile from './overviews/Profile.svelte'
    import Participants from './lists/Participants.svelte'
    import SessionList from './lists/SessionList.svelte'

    import MarkdownPage from './common/MarkdownPage.svelte';

    export let PAGE_NAME = '';
    export let PARAMS = {};
    export let CONTEXT = {};

</script>

{#if PAGE_NAME == 'home'}
<Home 
    {CONTEXT}
    NEWSLETTER_SLUG={PARAMS.NEWSLETTER_SLUG}
    USER_SUBSCRIBED={PARAMS.USER_SUBSCRIBED}
    PLACES_CT={PARAMS.PLACES_CT}
    MAP_CT={PARAMS.MAP_CT}
    FEATURED_MAPS={PARAMS.FEATURED_MAPS}
    MAP_FILTER_LIST={PARAMS.MAP_FILTER_LIST}
 />
{:else if PAGE_NAME == 'profile'}
<Profile
    {CONTEXT}
    PROFILE_USER={PARAMS.PROFILE_USER}
    MAP_FILTER_LIST={PARAMS.MAP_FILTER_LIST} />
{:else if PAGE_NAME == 'activity'}
<SessionList
    {CONTEXT}
    mapFilterItems={PARAMS.MAP_FILTER_LIST}
    userFilterItems={PARAMS.USER_FILTER_LIST}
    limit=25 showThumbs={true}/>
{:else if PAGE_NAME == 'profiles'}
<Participants
    {CONTEXT} />
{:else if PAGE_NAME == 'place'}
<Place
    {CONTEXT}
    PLACE={PARAMS.PLACE} />
{:else if PAGE_NAME == 'browse'}
<Browse 
    {CONTEXT}
    PLACES_CT={PARAMS.PLACES_CT}
    MAP_CT={PARAMS.MAP_CT} />
{:else if PAGE_NAME == 'markdown-page'}
<MarkdownPage 
    HEADER={PARAMS.HEADER}
    source={PARAMS.source}
    isHtml={PARAMS.isHtml}/>
{/if}
