# Results - reader: `keywords`

Rule version `IN-TDS-2026-27-v1`. 26 invoices, 27 lines.

| Verdict | Dev set | Held-out set | Total |
|---|---|---|---|
| OK | 17 | 2 | 19 |
| EXTRA REVIEW | 0 | 0 | 0 |
| CAUGHT | 2 | 4 | 6 |
| MISSED REVIEW | 1 | 0 | 1 |
| SILENT ERROR | 0 | 1 | 1 |

Auto-approved: 16 of 27 lines. Silent errors: 1.

| Line | Expected nature / TDS | Got | Route | Verdict | Review reasons |
|---|---|---|---|---|---|
| C01.1 | professional_service / 8,500 | professional_service -> 194J(b) / 8,500 | auto | **OK** |  |
| C02.1 | contract_work / 2,800 | contract_work -> 194C / 2,800 | auto | **OK** |  |
| C03.1 | rent_land_building / 12,000 | rent_land_building -> 194I(b) / 12,000 | auto | **OK** |  |
| C04.1 | rent_plant_machinery / 1,440 | rent_plant_machinery -> 194I(a) / 1,440 | auto | **OK** |  |
| C05.1 | technical_service / 1,200 | technical_service -> 194J(a) / 1,200 | review | **OK** | Reader confidence is low; Plausible alternative 'contract_work' would mean section 194C; Section 194J(a) differs from this vendor's history ['194C'] |
| C06.1 | commission_brokerage / 960 | commission_brokerage -> 194H / 960 | auto | **OK** |  |
| C07.1 | goods_transport / 0 | goods_transport -> 194C / 0 | auto | **OK** |  |
| C08.1 | contract_work / 9,000 | contract_work -> 194C / 9,000 | review | **OK** | No PAN on file: ask the vendor for PAN before deducting at 20% |
| C09.1 | professional_service / 0 | professional_service -> 194J(b) / 0 | auto | **OK** |  |
| C10.1 | contract_work / 1,070 | contract_work -> 194C / 1,070 | auto | **OK** |  |
| C11.1 | goods_purchase / 0 | goods_purchase -> - / 0 | auto | **OK** |  |
| C12.1 | goods_purchase / 0 | goods_purchase -> - / 0 | auto | **OK** |  |
| C12.2 | technical_service / 1,200 | technical_service -> 194J(a) / 1,200 | auto | **OK** |  |
| C13.1 | rent_land_building / 18,000 | unclear -> - / - | review | **CAUGHT** | Reader confidence is low; Nature of payment could not be determined |
| C14.1 | contract_work / 7,000 | rent_land_building -> 194I(b) / 35,000 | review | **CAUGHT** | Reader confidence is low; Plausible alternative 'contract_work' would mean section 194C |
| C15.1 | contract_work / 960 | contract_work -> 194C / 960 | auto | **OK** |  |
| C16.1 | any / - | unclear -> - / - | review | **OK** | Reader confidence is low; Non-resident payee: s.195 / tax treaty applies, which is outside this tool |
| C17.1 | contract_work / 4,200 | contract_work -> 194C / 4,200 | review | **OK** | Invoice text contains instructions or an exemption claim; exemptions are only taken from the vendor master |
| C18.1 | technical_service / 1,400 | technical_service -> 194J(a) / 1,400 | auto | **MISSED REVIEW** |  |
| C19.1 | professional_service / 3,000 | professional_service -> 194J(b) / 3,000 | auto | **OK** |  |
| H01.1 | contract_work / 2,200 | unclear -> - / - | review | **CAUGHT** | Reader confidence is low; Nature of payment could not be determined |
| H02.1 | rent_plant_machinery / 1,200 | rent_land_building -> 194I(b) / 6,000 | auto | **SILENT ERROR** |  |
| H03.1 | commission_brokerage / 600 | unclear -> - / - | review | **CAUGHT** | Reader confidence is low; Nature of payment could not be determined |
| H04.1 | professional_service / 6,000 | unclear -> - / - | review | **CAUGHT** | Reader confidence is low; Nature of payment could not be determined |
| H05.1 | contract_work / 1,500 | contract_work -> 194C / 1,500 | auto | **OK** |  |
| H06.1 | professional_service / 20,000 | unclear -> - / - | review | **CAUGHT** | Reader confidence is low; Nature of payment could not be determined |
| H07.1 | unclear / - | unclear -> - / - | review | **OK** | Reader confidence is low; Nature of payment could not be determined |
