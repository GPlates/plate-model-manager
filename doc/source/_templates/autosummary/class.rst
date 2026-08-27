{{ objname | escape | underline }}

.. currentmodule:: {{ module }}

.. autoclass:: {{ objname }}
   :members:
   :show-inheritance:
   :inherited-members:
   :special-members: __init__
   :exclude-members: models, model, rasters

{% block methods %}
{% if methods %}
{{ _('Methods') }}
{{ '-' * _('Methods')|length }}

.. autosummary::
   :nosignatures:
{% for item in methods %}
   ~{{ name }}.{{ item }}
{%- endfor %}
{% endif %}
{% endblock %}

{% block attributes %}
{% if attributes %}
{{ _('Attributes') }}
{{ '-' * _('Attributes')|length }}

.. autosummary::
{% for item in attributes %}
   ~{{ name }}.{{ item }}
{%- endfor %}
{% endif %}
{% endblock %}