from django.urls import reverse
from django.views import View
from django.shortcuts import render

class HomePage(View):

    def get(self, request):

        newsletter_slug = None
        user_subscribed = None
        # if settings.ENABLE_NEWSLETTER:
        #     newsletter = None
        #     if Newsletter.objects.all().exists():
        #         newsletter = Newsletter.objects.all()[0]
        #         newsletter_slug = newsletter.slug
        #     if newsletter is not None and request.user.is_authenticated:
        #         user_subscription = Subscription.objects.filter(newsletter=newsletter, user=request.user)
        #         if user_subscription.exists() and user_subscription[0].subscribed is True:
        #             user_subscribed = True
        # user_email = ""
        # if request.user.is_authenticated and request.user.email is not None:
        #     user_email = request.user.email

        # viewer_showcase = None
        # if settings.VIEWER_SHOWCASE_SLUG:
        #     try:
        #         p = Place.objects.get(slug=settings.VIEWER_SHOWCASE_SLUG)
        #         viewer_showcase = {
        #             'name': p.name,
        #             'url': reverse('viewer', args=(settings.VIEWER_SHOWCASE_SLUG,))
        #         }
        #     except Place.DoesNotExist:
        #         pass

        context_dict = {
            "search_params": {
                # "CITY_QUERY_URL": reverse('lc_api'),
                # 'USER_TYPE': get_user_type(request.user),
                # 'CITY_LIST': city_list,
            },
            "svelte_params": {
                # "PLACES_GEOJSON": Volume().get_map_geojson(),
                # "IS_MOBILE": mobile(request),
                # "CSRFTOKEN": csrf.get_token(request),
                # "NEWSLETTER_SLUG": newsletter_slug,
                # "USER_SUBSCRIBED": user_subscribed,
                # "USER_EMAIL": user_email,
                # "VIEWER_SHOWCASE": viewer_showcase,
            },
        }

        return render(
            request,
            "index.html",
            context=context_dict
        )