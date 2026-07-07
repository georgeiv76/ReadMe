# Raw Legal Sources — Manifest

> **Note on provenance:** This session's sandboxed network policy blocks direct downloads
> from government websites (govinfo.gov, congress.gov, eur-lex.europa.eu all return
> 403 at the egress proxy). The verbatim statutory texts therefore could not be
> committed to this repository. This manifest gives the canonical identifiers and
> official download links so the full texts can be pulled with one command from any
> unrestricted machine. The accompanying digest files (`genius-act-digest.md`,
> `mica-digest.md`) reconstruct the structure and operative provisions of each law,
> cross-checked against official summaries and accredited legal commentary via web search.

---

## 1. GENIUS Act (United States)

| Field | Value |
|---|---|
| Full name | Guiding and Establishing National Innovation for U.S. Stablecoins Act of 2025 |
| Bill | S. 1582, 119th Congress |
| Public Law | Pub. L. 119-27 |
| Signed | July 18, 2025 |
| Senate passage | June 17, 2025 (68-30) |
| House passage | July 17, 2025 (308-122) |

**Official full-text sources:**

- Public Law PDF (govinfo): https://www.congress.gov/119/plaws/publ27/PLAW-119publ27.pdf
- Public Law HTML (govinfo): https://www.govinfo.gov/content/pkg/PLAW-119publ27/html/PLAW-119publ27.htm
- Bill text (Congress.gov): https://www.congress.gov/bill/119th-congress/senate-bill/1582/text
- Compiled statute (govinfo COMPS): https://www.govinfo.gov/content/pkg/COMPS-18221/pdf/COMPS-18221.pdf

**Download command:**

```bash
curl -L -o genius-act-plaw-119-27.pdf \
  "https://www.congress.gov/119/plaws/publ27/PLAW-119publ27.pdf"
```

**Key implementation documents:**

- Treasury ANPRM, "GENIUS Act Implementation," 90 FR (Sept 19, 2025):
  https://www.federalregister.gov/documents/2025/09/19/2025-18226/genius-act-implementation
- Federal banking agencies / Treasury proposed rules (Dec 2025):
  https://www.govinfo.gov/content/pkg/FR-2025-12-19/pdf/2025-23510.pdf

---

## 2. MiCA — Markets in Crypto-Assets Regulation (European Union)

| Field | Value |
|---|---|
| Full name | Regulation (EU) 2023/1114 of the European Parliament and of the Council of 31 May 2023 on markets in crypto-assets |
| CELEX | 32023R1114 |
| Official Journal | OJ L 150, 9.6.2023, p. 40-205 |
| Entered into force | June 29, 2023 |
| Stablecoin titles (III & IV) apply from | June 30, 2024 |
| Remaining titles apply from | December 30, 2024 |

**Official full-text sources:**

- EUR-Lex HTML (EN): https://eur-lex.europa.eu/legal-content/EN/TXT/HTML/?uri=CELEX:32023R1114
- EUR-Lex PDF (EN): https://eur-lex.europa.eu/legal-content/EN/TXT/PDF/?uri=CELEX:32023R1114
- EUR-Lex landing page (all languages): https://eur-lex.europa.eu/eli/reg/2023/1114/oj

**Download command:**

```bash
curl -L -o mica-regulation-eu-2023-1114.pdf \
  "https://eur-lex.europa.eu/legal-content/EN/TXT/PDF/?uri=CELEX:32023R1114"
```

**Key implementation documents:**

- EBA Guidelines & RTS on ARTs/EMTs hub: https://www.eba.europa.eu/regulation-and-policy/markets-crypto-assets-mica
- ESMA MiCA hub: https://www.esma.europa.eu/esmas-activities/digital-finance-and-innovation/markets-crypto-assets-regulation-mica
- ECB Opinion on the digital euro & stablecoin commentary: https://www.ecb.europa.eu
