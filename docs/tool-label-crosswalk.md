# Four-Tool Vulnerability Label Crosswalk

Every native label from Dedaub, Mythril, Slither and Wake mapped onto one shared
canonical class, so findings can be compared apple-to-apple. Catalogs captured 2026-07-14
(Dedaub `common.vulnerability_metadata`=80 types, Mythril 0.24.8=16 SWC, Slither 0.11.4=99, Wake 4.22.1).

## Cross-matchable — Dedaub + ≥1 open-source tool

| Canonical class | Plain meaning | Dedaub | Mythril (SWC) | Slither | Wake |
|---|---|---|---|---|---|
| **reentrancy** | State/external-call reentered before state is settled. | Reentrancy<br>Inconsistent Reentrancy guards | SWC-107 ExternalCalls<br>SWC-107 StateChangeAfterCall | reentrancy-eth<br>reentrancy-no-eth<br>reentrancy-benign<br>reentrancy-events<br>reentrancy-unlimited-gas | reentrancy |
| **accessible_selfdestruct** | SELFDESTRUCT reachable / target overwritable by an untrusted caller. | Accessible selfdestruct<br>Tainted selfdestruct<br>FUZZED: Selfdestruct | SWC-106 AccidentallyKillable | suicidal | unprotected-selfdestruct |
| **tainted_delegatecall** | DELEGATECALL target controllable by an untrusted caller (incl. in loops). | Tainted delegatecall<br>Call and Delegate Together<br>Looped delegateCall and msg.value | SWC-112 ArbitraryDelegateCall | controlled-delegatecall<br>delegatecall-loop | unsafe-delegatecall |
| **arbitrary_storage_write** | SSTORE to an attacker-controlled storage slot. | SSTORE to tainted address<br>SSTORE inconsistent with others | SWC-124 ArbitraryStorage | controlled-array-length | — |
| **unchecked_low_level_call** | Return status/value of an external or token call is not checked. | Unchecked Low-Level Call<br>ERC20 call demands high-level return value | SWC-104 UncheckedRetval | unchecked-lowlevel<br>unchecked-send<br>unchecked-transfer<br>unused-return | unchecked-return-value<br>unsafe-erc20-call |
| **arbitrary_send** | Unauthorized movement of value/tokens: unprotected fund transfer, approve/transferFrom proxy, or a fund-moving DeFi op reachable by anyone. | Swap publicly reachable<br>Swap reachable, contract has funds<br>Sensitive call can be reached by anyone<br>Unrestricted transfer proxy<br>Unrestricted transferFrom Proxy<br>Unrestricted approve proxy<br>Tainted money-sensitive var in external call<br>Rare tainted money-sensitive var in external call<br>Call to Tainted Function<br>FUZZED: Arbitrary Call<br>FUZZED: Fund Loss<br>Suspicious money transfer operation<br>Suspicious money burn operation<br>Transfer of entire balance | SWC-105 EtherThief | arbitrary-send-eth<br>arbitrary-send-erc20<br>arbitrary-send-erc20-permit | — |
| **access_control** | A sensitive guard/owner variable is overwritable, or a privileged action lacks an effective caller check. | Tainted Ownership Guard<br>Guard can be overwritten<br>Suspicious SSTORE guard<br>Sensitive callback does not check sender<br>Suspicious conditions on msg.sender<br>Suspicious conditions on msg.sender1<br>Suspicious conditions on msg.sender2<br>Suspicious conditions on msg.sender3<br>tainted owner variable | — | protected-vars<br>unprotected-upgrade<br>events-access<br>missing-zero-check<br>incorrect-modifier | — |
| **arithmetic** | Integer overflow/underflow or unchecked arithmetic error. | Arithmetic error | SWC-101 IntegerArithmetics | divide-before-multiply<br>incorrect-exp<br>tautology<br>incorrect-shift | — |
| **bad_randomness** | Predictable environment value (randomness, block.timestamp) an attacker can influence. | Bad Randomness | SWC-116/120 PredictableVariables | weak-prng<br>gelato-unprotected-randomness<br>timestamp | — |
| **tx_origin_auth** | Authorization relies on tx.origin. | Relying on msg.sender == tx.origin | SWC-115 TxOrigin | tx-origin | tx-origin |
| **dos_gas** | Denial of service: unbounded iteration, griefing, or a call that can wedge the transaction. | DoS: Unbounded Iteration<br>DoS (Unbounded Iteration)<br>DoS: Wallet Griefing<br>DoS: Call can cause failure<br>DoS: Suspicious revert inside loop<br>Inconsistent array iteration | SWC-113 MultipleSends | calls-loop<br>costly-loop<br>msg-value-loop<br>return-bomb | — |
| **signature_malleability** | ECDSA signature malleability / signature used as a map key. | ECDSA signature malleability | — | domain-separator-collision | — |
| **uninitialized_proxy** | Initializer/guard can be (re)set by anyone; uninitialized state. | Initialization guard checked but not set | — | uninitialized-state<br>uninitialized-storage<br>uninitialized-local | missing-return |
| **oracle_manipulation** | Price/oracle read is manipulable or unchecked for staleness. | Uniswap price manipulation potential<br>Uniswap tainted token<br>Chainlink data feed may provide stale answers<br>Manipulable Tellor answer<br>Stale value in storage | — | chainlink-feed-registry<br>chronicle-unchecked-price<br>pyth-unchecked-confidence<br>pyth-unchecked-publishtime<br>pyth-deprecated-functions | chainlink-deprecated-function |
| **front_running** | Transaction-order / slippage dependence exploitable by front-running. | Swap call with 0 minAmountOut<br>Vault vulnerable to front-running when (near) empty | SWC-114 TransactionOrderDependence | — | — |
| **assertion_failure** | A reachable assert / invariant violation. | Reachable assert<br>Inconsistent assertions | SWC-110 Exceptions<br>SWC-110 UserAssertions<br>SWC-123 RequirementsViolation | assert-state-change | — |
| **dead_code** | Dead/no-op code, unused declarations, or mis-declared mutability. | Immutable storage location declared mutable<br>No-op storage load<br>No-op internal function call<br>No-op external function call<br>Unused public function argument<br>Storage leak due to undeleted mapping | — | dead-code<br>unused-state<br>immutable-states<br>constable-states<br>write-after-write<br>redundant-statements | unused-function<br>unused-import<br>unused-event<br>unused-error<br>unused-modifier<br>unused-contract |

## Dedaub-only — no open-source corroborator (need Dedaub's own reachability/fuzzer)

| Canonical class | Plain meaning | Dedaub | Mythril (SWC) | Slither | Wake |
|---|---|---|---|---|---|
| **signature_replay** | Signed payload omits chainId/nonce -> cross-chain or replay risk. | ECDSA without chainid<br>Permit omits sensitive variable<br>Inconsistent ECDSA signing | — | — | — |
| **flashloan** | Flash-loan callback does not authenticate the initiator. | FlashLoan unchecked callback<br>FUZZED: Imbalanced Uniswap Pair | — | — | — |
| **decimal_scaling** | Inconsistent decimal/scaling handling or unsafe monetary rounding. | Suspicious decimal arithmetic<br>Suspicious token decimal arithmetic<br>Suspicious lack of token decimal arithmetic<br>Inconsistent absolute scaling<br>Inconsistent relative scaling<br>Inconsistent complex relative scaling<br>Tokens may have inconsistent decimals<br>Rounding up of monetary amount<br>Rounding down of monetary amount | — | — | — |
| **merkle_leaf_confusion** | Internal Merkle node usable as a leaf (2nd-preimage). | Merkle node can be used as leaf | — | — | — |
| **twin_calls** | Repeated external calls to an untrusted contract can return inconsistent results across the same transaction. | Twin calls<br>this.call() | — | — | — |
| **logic_error** | Dedaub-specific semantic/logic smell not covered by a shared class. | Undisclosed Vulnerability<br>Classifier: Suspicious contract<br>SCREAM does not have a permit function | — | — | — |

## Open-source-only — no Dedaub label

| Canonical class | Plain meaning | Dedaub | Mythril (SWC) | Slither | Wake |
|---|---|---|---|---|---|
| **unexpected_ether** | Contract balance assumptions broken by forced/locked ether. | — | SWC-132 UnexpectedEther | locked-ether<br>incorrect-equality | balance-relied-on<br>msg-value-nonpayable-function |
| **arbitrary_jump** | Caller can redirect execution to arbitrary bytecode. | — | SWC-127 ArbitraryJump | — | — |
| **compiler_bug** | Version-specific solc miscompilation. | — | — | storage-array<br>array-by-reference<br>abiencoderv2-array<br>encode-packed-collision | calldata-tuple-reencoding-head-overflow-bug<br>empty-byte-array-copy-bug |
| **shadowing_integrity** | Name/scope integrity: shadowed or reused identifiers, RTLO override, wrong-signature ABI encoding, malformed interfaces. | — | — | shadowing-state<br>shadowing-abstract<br>shadowing-builtin<br>shadowing-local<br>name-reused<br>multiple-constructors<br>public-mappings-nested<br>uninitialized-fptr-cst<br>rtlo<br>incorrect-return<br>return-leave<br>variable-scope<br>void-cst<br>erc20-interface<br>erc721-interface<br>incorrect-using-for<br>tautological-compare<br>missing-inheritance<br>unimplemented-functions | abi-encode-with-signature<br>incorrect-interface<br>complex-struct-getter<br>axelar-proxy-contract-id<br>invalid-memory-safe-assembly |
| **code_quality** | Style, hygiene, gas, and low-signal informational checks. Not a vulnerability class; never a Dedaub false-positive source. | — | — | assembly<br>boolean-cst<br>boolean-equal<br>cyclomatic-complexity<br>deprecated-standards<br>erc20-indexed<br>external-function<br>function-init-state<br>low-level-calls<br>naming-convention<br>pragma<br>solc-version<br>unindexed-event-address<br>var-read-using-this<br>cache-array-length<br>constant-function-asm<br>constant-function-state<br>events-maths<br>optimism-deprecation<br>too-many-digits<br>mapping-deletion<br>incorrect-unary<br>enum-conversion<br>out-of-order-retryable<br>reused-constructor | call-options-not-called<br>struct-mapping-deletion<br>array-delete-nullification |
