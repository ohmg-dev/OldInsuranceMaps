from django import forms


class DynamicForm(forms.Form):
    def __init__(self, form_config: dict, *args, **kwargs):
        super().__init__(*args, **kwargs)

        FIELD_MAPPING = {
            "char": forms.CharField,
            "integer": forms.IntegerField,
            "email": forms.EmailField,
            "boolean": forms.BooleanField,
            "choice": forms.ChoiceField,
        }

        for field_data in form_config["fields"]:
            field_name = field_data.get("name")
            field_type = field_data.get("type", "char")

            field_kwargs = {
                "label": field_data.get("label", field_name.replace("_", " ").title()),
                "required": field_data.get("required", True),
                "initial": field_data.get("initial", None),
                "widget": forms.TextInput(attrs={"class": "input"}),
            }

            # Handle unique requirements for specific field types
            if field_type == "choice":
                field_kwargs["choices"] = field_data.get("choices", [])

            # Instantiate and attach the field dynamically
            field_class = FIELD_MAPPING.get(field_type, forms.CharField)
            self.fields[field_name] = field_class(**field_kwargs)
