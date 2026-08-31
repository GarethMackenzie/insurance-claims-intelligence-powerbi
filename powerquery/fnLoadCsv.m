// Reusable governed CSV loader used by model partitions.
(relativePath as text, tableType as type) as table =>
let
    FullPath = pProjectRoot & "\" & relativePath,
    Source = Csv.Document(File.Contents(FullPath), [Delimiter=",", Encoding=65001, QuoteStyle=QuoteStyle.Csv]),
    PromotedHeaders = Table.PromoteHeaders(Source, [PromoteAllScalars=true]),
    TypeRecord = Type.RecordFields(Type.TableRow(tableType)),
    Transformations = List.Transform(Record.FieldNames(TypeRecord), (columnName) => {columnName, Record.Field(TypeRecord, columnName)[Type]}),
    Typed = Table.TransformColumnTypes(PromotedHeaders, Transformations)
in
    Typed
