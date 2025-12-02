from typing import List, Optional

from ninja import (
    Field,
    FilterSchema,
)


class FilterSessionSchema(FilterSchema):
    username: Optional[str] = Field(q="user__username")
    map: Optional[List[str]] = Field(q=["map_id__in"])
    document: Optional[List[int]] = Field(
        q=["doc2_id__in", "reg2__document_id__in", "lyr2__region__document_id__in"]
    )
    region: Optional[List[int]] = Field(q=["reg2_id__in", "lyr2__region_id__in"])
    layer: Optional[List[int]] = Field(q=["lyr2_id__in"])
    type: Optional[str]


class FilterDocumentSchema(FilterSchema):
    map: str = Field(q="map_id")
    prepared: Optional[bool] = Field(q="prepared")


class FilterAllDocumentsSchema(FilterSchema):
    prepared: Optional[bool] = Field(q="prepared")


class FilterRegionSchema(FilterSchema):
    map: Optional[str] = Field(q="document__map_id")
    document: Optional[str] = Field(q="document_id")
    prepared: Optional[bool] = Field(q="prepared")
