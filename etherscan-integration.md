# Etherscan Integration — Dedaub tok{in} Token Safety API

## Etherscan API Standards (Requirements)

1. Must be HTTP-GET API (POST can be supported later)
2. Only one endpoint per card
3. If API Key is required:
   - a. Include in request headers (e.g. `x-api-key`, `authorization`)
      - b. Include as query string param (e.g. `apikey=[ApiKeyHere]`)
      4. `[address]` parameter is required (route-parameter or query-string)
         - chainId / chainName required if supporting multichain
         5. API response must be:
            - a. JSON format
               - b. Include status properties **only if all requests return 200-OK** (e.g. `success: true`, `status: "ok"`)
                  - c. Ready to use — no custom logic required
                       - If message only: return full message or provide template `"text ${X}, ${Y}"`
                            - If bullet points: template message required
                                 - If images: return CDN image links

                                 ---

                                 ## tok{in} API — Compliance Summary

                                 | # | Requirement | Status | Notes |
                                 |---|---|---|---|
                                 | 1 | HTTP-GET | ✅ | GET only |
                                 | 2 | Single endpoint per card | ✅ | One endpoint |
                                 | 3a | API key in request header | ✅ | `X-API-Key: YOUR-API-KEY` |
                                 | 3b | API key as query string param | ⚠️ | Not yet supported — needs to be added |
                                 | 4 | `[address]` as route parameter | ✅ | `{token_address}` route param |
                                 | 4a | chainName for multichain | ✅ | `{chain}` route param |
                                 | 5a | JSON response | ✅ | Returns JSON |
                                 | 5b | Status properties | ✅ | Returns 200 (success) / 422 (error) — no body status field needed |
                                 | 5c | Ready to use | ✅ | Fields returned directly — template defined below |

                                 ---

                                 ## Endpoint

                                 ```
                                 GET https://tokin-api.dedaub.com/token/{chain}/{token_address}
                                 ```

                                 **Supported chains:** `ethereum`, `binance`, `arbitrum`, `base`, `avalanche`

                                 **Authentication:**
                                 ```
                                 Header: X-API-Key: YOUR-API-KEY
                                 Query param (to be added): ?apikey=YOUR-API-KEY
                                 ```

                                 **Example request:**
                                 ```
                                 GET https://tokin-api.dedaub.com/token/ethereum/0x2328434559f7dec44373822cf68052de0d671b7f
                                 X-API-Key: YOUR-API-KEY
                                 ```

                                 ---

                                 ## Proposed Card Display

                                 ### Key Flags (shown only when `true`)
                                 | Field | Description |
                                 |---|---|
                                 | `cannot_buy` | Token cannot be bought |
                                 | `timebomb` | Functionality enabled only after a specific timestamp |
                                 | `mint_or_burn_function` | Public function that changes total supply |
                                 | `has_blacklist_or_whitelist` | Addresses can be restricted from trading |

                                 ### Tax & Liquidity Summary
                                 | Field | Source | Notes |
                                 |---|---|---|
                                 | `buy_tax` | `dex[].buy_tax` | From most liquid pool |
                                 | `sell_tax` | `dex[].sell_tax` | From most liquid pool |
                                 | `pool_count` | `dex.length` | Pre-computed by API — **edit required** |
                                 | `total_liquidity` | sum of `dex[].liquidity` | Pre-computed by API — **edit required** |
                                 | `avg_buy_tax` | avg of `dex[].buy_tax` | Pre-computed by API — **edit required** |
                                 | `avg_sell_tax` | avg of `dex[].sell_tax` | Pre-computed by API — **edit required** |

                                 ### Proposed Message Template
                                 ```
                                 Risks: ${cannot_buy_flag} ${timebomb_flag} ${mint_burn_flag} ${blacklist_flag}
                                 Pools: ${dex_summary.pool_count} | Total Liquidity: $${dex_summary.total_liquidity}
                                 Avg. Buy Tax: ${dex_summary.avg_buy_tax}% | Avg. Sell Tax: ${dex_summary.avg_sell_tax}%
                                 ```

                                 ---

                                 ## Required API Edits

                                 | # | Edit | Priority |
                                 |---|---|---|
                                 | 1 | Add API key support as query string param: `?apikey=xxx` | High |
                                 | 2 | Add `dex_summary` object to response with pre-computed: `pool_count`, `total_liquidity`, `avg_buy_tax`, `avg_sell_tax` | High |

                                 ### Proposed `dex_summary` addition to API response
                                 ```json
                                 "dex_summary": {
                                   "pool_count": 1,
                                     "total_liquidity": 59292.71,
                                       "avg_buy_tax": 1.0,
                                         "avg_sell_tax": 1.0
                                         }
                                         ```

                                         ---

                                         ## Swagger UI
                                         Full API documentation and testing available at: https://tokin-api.dedaub.com

                                         ---

                                         *Last updated: April 2026*
