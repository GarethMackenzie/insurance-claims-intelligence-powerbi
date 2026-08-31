let
    Source = Csv.Document(File.Contents(pProjectRoot & "\data\raw\claims_raw.csv"), [Delimiter=",", Encoding=65001, QuoteStyle=QuoteStyle.Csv]),
    PromotedHeaders = Table.PromoteHeaders(Source, [PromoteAllScalars=true]),
    NormalizedText = Table.TransformColumns(PromotedHeaders, {
        {"Region", fnNormalizeText, type nullable text},
        {"Channel", fnNormalizeText, type nullable text},
        {"Claim_Type", fnNormalizeText, type nullable text},
        {"Claim_Status", fnNormalizeText, type nullable text}
    }),
    DuplicateCounts = Table.Group(NormalizedText, {"Claim_ID"}, {{"Row_Count", each Table.RowCount(_), Int64.Type}}),
    WithDuplicateFlag = Table.NestedJoin(NormalizedText, {"Claim_ID"}, DuplicateCounts, {"Claim_ID"}, "Audit", JoinKind.LeftOuter),
    ExpandedAudit = Table.ExpandTableColumn(WithDuplicateFlag, "Audit", {"Row_Count"}, {"Duplicate_Row_Count"})
in
    ExpandedAudit
