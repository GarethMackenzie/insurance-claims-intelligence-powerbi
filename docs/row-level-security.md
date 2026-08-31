# Row-level security

Two conceptual roles are defined in `roles.tmdl`:

- **Executive** has read access to the full model.
- **Regional Manager** is restricted to a demonstration set of Gauteng, Western Cape and KwaZulu-Natal.

No real users, email addresses or identity provider values are included. In production, replace the static filter with a governed user-to-region bridge and `USERPRINCIPALNAME()`, validate effective identity in the service, and test export, Analyze in Excel, drill-through and subscription behaviour.

The example demonstrates model security structure only. It must not be treated as a deployed access-control design.
