// Null-safe text normalization helper for controlled categories.
(value as nullable any) as nullable text =>
let
    AsText = if value = null then null else Text.From(value),
    Trimmed = if AsText = null then null else Text.Trim(AsText),
    Cleaned = if Trimmed = "" then null else Text.Clean(Trimmed)
in
    Cleaned
