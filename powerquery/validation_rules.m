let
    Source = stg_ClaimsRaw,
    WithAmountRule = Table.AddColumn(Source, "Amount_Rule", each if [Claim_Amount] = null or Number.From([Claim_Amount]) <= 0 then "FAIL" else "PASS", type text),
    WithDateRule = Table.AddColumn(WithAmountRule, "Date_Rule", each if Date.From([Report_Date]) < Date.From([Loss_Date]) then "FAIL" else "PASS", type text),
    WithCategoryRule = Table.AddColumn(WithDateRule, "Region_Rule", each if List.Contains({"Gauteng","Western Cape","KwaZulu-Natal","Eastern Cape","Free State","Limpopo","Mpumalanga","North West","Northern Cape"}, [Region]) then "PASS" else "FAIL", type text),
    WithOutcome = Table.AddColumn(WithCategoryRule, "Validation_Outcome", each if List.Contains({[Amount_Rule], [Date_Rule], [Region_Rule]}, "FAIL") then "QUARANTINE" else "ACCEPT", type text)
in
    WithOutcome
