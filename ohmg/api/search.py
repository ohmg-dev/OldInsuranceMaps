from django.contrib.postgres.search import SearchQuery, SearchVector
from django.db.models.query import QuerySet


def search_fuzzy_first_word(search_param: str, search_field: str, queryset: QuerySet):
    """if there is only one word in the query, then automatically treat
    it as ending in a wilcard.

    If two words or more, use websearch."""
    vector = SearchVector(*search_field)
    words = search_param.split(" ")
    if len(words) == 1:
        search_param += ":*"
        query = SearchQuery(search_param, search_type="raw")
    else:
        query = SearchQuery(search_param, search_type="websearch")

    return queryset.annotate(search=vector).filter(search=query)


def search_word_contains(search_param: str, search_field: str, queryset: QuerySet):
    """apply a basic, case-insensitive search for string within string."""

    filter_statement = {f"{search_field}__icontains": search_param}

    return queryset.filter(**filter_statement)
