let
    Source = fnLoadCsv("data\clean\FactClaims.csv", type table [
        Claim_ID=text, Policy_ID=text, Loss_Date=date, Report_Date=date,
        Claim_Amount=Currency.Type, Paid_Amount=Currency.Type,
        Reserve_Amount=Currency.Type, Total_Incurred=Currency.Type
    ]),
    PositiveAmounts = Table.SelectRows(Source, each [Claim_Amount] > 0 and [Total_Incurred] >= 0),
    ValidDateOrder = Table.SelectRows(PositiveAmounts, each [Report_Date] >= [Loss_Date]),
    UniqueClaims = Table.Distinct(ValidDateOrder, {"Claim_ID"}),
    WithReportingDelay = Table.AddColumn(UniqueClaims, "Reporting_Delay_Check", each Duration.Days([Report_Date] - [Loss_Date]), Int64.Type)
in
    WithReportingDelay
