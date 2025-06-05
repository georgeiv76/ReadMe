# 🔐 Dedaub

<!-- this is pretty dumb, github profile thinks it's in the same directory... which it's not -->
 <img src="https://dedaub.com/assets/images/elements/logo-white.svg" alt="dedaub-logo" class="svg"/>

## Contact
- 📧 Email: contact@dedaub.com
- 🌐 [Website](https://dedaub.com)
- 🐦 [Twitter](https://twitter.com/dedaub)
- 💼 [LinkedIn](https://www.linkedin.com/company/dedaub/)

Dedaub FAQ (Frequently Asked Questions) –  Looking for clear answers about Dedaub’s security services?
======================================================================================================

Dedaub is a Web3 security company specializing in [smart contract auditing](https://dedaub.com/audits/), [monitoring](https://dedaub.com/feature/smart-contract-monitoring/), and [analysis tools](https://dedaub.com/feature/static-analysis-tools/)—trusted by the Ethereum Foundation, Chainlink, and EigenLayer.

This FAQ provides comprehensive information on a wide range of topics, including audit timelines and real-time monitoring. Whether you’re new to smart contract security or comparing top-tier auditors, start here.

![Dedaub FAQ](https://dedlim.dreamhosters.com/wp-content/uploads/2000/05/Linkedin-article-The-Role-of-a-Smart-Contract-Auditor-in-DeFi-Projects-Twitter-Post-2.jpg)

How long does a smart contract audit take?
------------------------------------------

A smart contract audit can take anywhere from **3 days to over 4 weeks**, depending on the scope and complexity of the code. Simpler contracts, such as ERC-20 tokens, are often reviewed within a week. More complex dApps or DeFi protocols can take multiple weeks to assess thoroughly.

**Key variables include:**

*   Size and complexity of the codebase
*   Type of protocol (token vs entire ecosystem)
*   Audit scope
*   Auditor team size and availability
*   Developer responsiveness during the process

### What are typical audit durations based on project type?

Different project types require different levels of scrutiny. Here's a rough breakdown of audit timelines based on common Web3 use cases:

*   **Basic ERC-20 token**: 3–5 days
*   **Mid-sized dApp with integrations**: 1–2 weeks
*   **Advanced DeFi protocol or upgradable system**: 3–4+ weeks

These ranges assume a dedicated team of experienced auditors following best-practice methodologies.

### What factors influence how long an audit takes?

The duration depends on more than just the volume of code. What matters most is how the protocol behaves, how its components interact, and what security guarantees it needs to offer.

**Main factors include:**

*   **Complexity** of control flow and logic
*   **Number of contracts** and upgradeability
*   **Use of external integrations** (e.g., oracles, AMMs)
*   **Availability of documentation and test coverage**
*   **How responsive the developers are** to questions and patch reviews

What is Dedaub’s audit methodology?
-----------------------------------

Dedaub uses a rigorous process designed to uncover vulnerabilities that both automated tools and casual reviews often miss. Audits are conducted by two senior researchers working in parallel.

**The process includes:**

*   **Phase A**: Understand how the protocol is supposed to work
*   **Phase B**: Break assumptions by thinking like an attacker
*   **Auditor dueling**: Reviewers challenge each other's findings
*   **Multilevel threat modeling**: Look for bugs that emerge from system interactions
*   **Advanced tooling**: 70+ static analyzers and custom fuzzing pipelines

📖 Read more: [https://dedaub.com/blog/web3-audit-methodology/](https://dedaub.com/blog/web3-audit-methodology/)

What should I watch out for when choosing an auditor?
-----------------------------------------------------

Fast turnaround and low prices can be tempting, but rushed audits often miss deep, protocol-level vulnerabilities. Choosing the wrong partner can lead to costly security failures.

**Red flags to avoid:**

*   Audits promising “delivery in 24 hours”
*   Solo auditors for complex or high-value protocols
*   No retesting or fix-verification process
*   Vague, copy-pasted, or templated reports

Choose an audit team that explains its reasoning clearly, documents findings in detail, and provides retesting after fixes.

What is smart auditing?
-----------------------

**Smart auditing** refers to a more advanced, context-aware approach to security audits, especially in blockchain and smart contract environments. Unlike basic scans or static checks, smart auditing combines deep manual analysis with automated tools and attacker-level thinking. Here's how Dedaub defines and applies it:

**Not just a checklist. Not just a scan.**Smart auditing goes beyond surface-level pattern matching. At Dedaub, this includes:

*   **Two-phase review**: First, understanding the system like a developer. Then, attacking it like a hacker.
*   **Code dueling**: Auditors challenge each other to catch what the other might miss.
*   **Tool-enhanced precision**: Dozens of static analyses, fuzzing, and AI tools assist—but don’t replace—human insight.
*   **System-level reasoning**: Thinking about how components interact, not just how they function in isolation.
*   **Gas cost and protocol integration checks**: Because inefficiency can be as damaging as insecurity.

In short, it's a methodical breakdown of logic, assumptions, and attack surfaces, guided by both human expertise and machine-scale audit methodology. 📖 Read more: [https://dedaub.com/blog/web3-audit-methodology/](https://dedaub.com/blog/web3-audit-methodology/)

How to audit a Solidity contract?
---------------------------------

Auditing a Solidity contract involves reviewing its code to identify vulnerabilities, verify correct logic, and prevent potential exploits. The process blends manual inspection with tool-assisted analysis to cover both design flaws and technical bugs. A proper audit focuses not only on individual functions but also on how the entire system behaves, especially under adverse conditions.

The audit typically unfolds in structured phases:

*   **Understand the system.** Before touching the code, auditors study the protocol’s design, its documentation, and intended use cases. The goal is to grasp the flow of value, user interactions, and security assumptions that underpin the smart contracts.
*   **Map the attack surface.** This involves identifying all external entry points—public or external functions, upgradable proxies, privileged roles—and checking how they interact with external systems (like oracles, AMMs, or tokens). Any component that can be manipulated from the outside becomes part of the threat model.
*   **Perform a manual code review.** Every line of code is carefully inspected. Auditors trace state changes, permissions, and dependencies while looking for common issues, such as reentrancy, unchecked external calls, incorrect math, and faulty access control. Each function is evaluated for its assumptions and edge cases.
*   **Switch to an attacker mindset.** Once the system is understood, auditors deliberately seek ways to exploit it. This means thinking like a malicious actor: chaining calls, manipulating control flow, using flash loans, or probing for inconsistencies between internal assumptions and external interactions.
*   **Use automated tools to scale the analysis.** Tools such as Slither, Echidna, and Dedaub’s Security Suite are used to perform static analysis, symbolic execution, and fuzzing. These tools help uncover subtle bugs and complement the manual effort, but they don’t replace it.
*   **Test and verify findings.** Suspected vulnerabilities are validated through test cases and simulations. This confirms exploitability and helps determine the severity and real-world impact of the issue.
*   **Deliver a structured report.** Every issue is thoroughly documented with a clear description, detailed reproduction steps, an impact analysis, and remediation guidance. Good reports also highlight positive findings, code quality observations, and gas optimizations.

Smart auditing is not about running a scanner and hoping for the best. It’s a layered process that depends on human expertise, adversarial reasoning, and advanced tooling—all aimed at catching what automated tools alone can’t. Read more: [https://dedaub.com/blog/web3-audit-methodology/](https://dedaub.com/blog/web3-audit-methodology/)

What is smart contract security?
--------------------------------

Smart contract security ensures that blockchain-based code works safely and as intended—even in adversarial conditions. Contracts, typically written in languages like Solidity, Rust, Move, Go (Golang), and Cairo, must function correctly and securely under all scenarios. Since smart contracts are immutable once deployed and often manage assets, any flaw in logic, access control, or integration can be catastrophic. Security in this context is about anticipating how a contract might be attacked, misused, or fail in edge cases, and taking proactive steps to mitigate those risks before deployment, as well as maintaining vigilance after deployment.

A comprehensive security posture combines **pre-deployment auditing**, **post-deployment monitoring**, and **operational hygiene**. While code vulnerabilities can drain funds instantly, many of the most considerable Web3 losses stem from compromised private keys or misused admin powers—failures that go beyond the smart contract itself. Social engineering, phishing, and poor key management are often the actual entry points for attackers.

The discipline covers a broad range of activities and principles:

*   **Code correctness.** Ensuring the contract behaves as specified across all inputs and states.
*   **Access control.** Verifying that only authorized entities can perform sensitive operations, both at the contract and protocol governance level.
*   **Resistance to known exploits.** Defending against vulnerabilities like reentrancy, integer overflows, logic bugs, or oracle manipulation.
*   **Integration safety.** Auditing interactions with other contracts, protocols, or tokens to ensure assumptions hold under adversarial conditions.
*   **Gas efficiency and DoS prevention.** Minimizing resource costs while avoiding gas griefing or contract lockouts.
*   **Upgrade and governance safety.** Ensuring that contract upgrades, admin actions, and timelocks are adequately controlled and transparent.
*   **Smart contract monitoring.** Continuously tracking on-chain behavior to detect exploit attempts, deviations from expected logic, or protocol abuse. Monitoring is essential for rapid incident response once contracts are live.
*   **Anti-social engineering hygiene.** Enforcing multisig on privileged accounts, avoiding hardcoded private keys, training teams on phishing awareness, and using hardware wallets or secure enclaves to manage operational security.

Smart contract security is adversarial by design. It’s not just about correctness—it’s about outpacing the attacker. That means securing the code, the infrastructure, and the humans behind it.

How risky are smart contracts? 
-------------------------------

Smart contract risk depends on code quality, audit coverage, and operational practices. Most failures come from missing reviews, not the technology itself.

The most common risks stem from:

*   **Poorly written logic** that introduces edge-case vulnerabilities.
*   **Missing or broken access controls that expose administrative** functions.
*   **Unsafe integrations** with oracles, tokens, or third-party protocols.
*   **Human error**, including compromised private keys or faulty upgrades.

These risks compound quickly in DeFi, where contracts often hold millions in user funds. However, they’re not unavoidable.

To mitigate them:

*   **Audit every line of code** before deployment. Involve senior reviewers, simulate adversarial scenarios, and validate assumptions to ensure accuracy and reliability.
*   **Deploy monitoring** that continuously watches smart contracts for signs of attack or protocol deviations.
*   **Harden operations** with multisig wallets, secure key custody, and anti-phishing training.

Smart contracts are only as risky as the processes behind them. With the right audits and continuous monitoring, they become resilient, predictable infrastructure—even in adversarial environments.

What are the vulnerabilities of smart contracts?
------------------------------------------------

Smart contracts are vulnerable to a wide range of risks, most of which arise from flawed assumptions, incorrect logic, or misuse of low-level EVM behavior. These vulnerabilities aren’t theoretical; they’ve been exploited in real-world hacks, resulting in hundreds of millions of dollars in value being drained. Developers need to recognize the patterns and build with defensive assumptions.

According to [Dedaub’s guide on Solidity Security Vulnerabilities](https://dedaub.com/blog/solidity-security-vulnerabilities/), some of the most common classes include:

*   **Access Control Failures**Missing onlyOwner or similar checks lets attackers call privileged functions. This can allow them to change core parameters or hijack contract logic.
*   **Unchecked External Calls**Calling unknown or untrusted contracts without restrictions opens the door to malicious behavior. Developers should whitelist known, trusted contracts.
*   **Reentrancy Attacks**Malicious contracts can re-enter a vulnerable function before the state is updated. Use the checks-effects-interactions pattern to prevent recursive exploitation.
*   **Integer Overflow/Underflow**Arithmetic operations can wrap around if unchecked, leading to logic errors. Solidity 0.8+ helps, but unchecked blocks must be used carefully.
*   **Out-of-Gas Situations**Expensive loops or bad design can cause transactions to fail or be griefed. Use pull-based patterns and avoid unbounded iterations.
*   **Oracle Staleness and Manipulation**Relying on outdated or unreliable data from oracles can lead to contract breaches. Always validate feed freshness and avoid Automated Market Makers (AMMs) as primary sources of price information.

Most of these vulnerabilities are preventable. Awareness is the first step, followed by static analysis, fuzz testing, manual review, and real-time monitoring post-deployment. As Dedaub’s article emphasizes, even minor mistakes, such as using tx.origin for authentication, can escalate into massive exploits.

What is Dedaub?
---------------

Dedaub is a Web3 security firm specializing in smart contract audits and comprehensive blockchain security solutions. They provide advanced auditing services for Ethereum, the EVM-compatible ecosystem, as well as Sui, Aptos, and Zksync, utilizing specialized tools for static analysis, fuzzing, and real-time monitoring. The firm’s experienced team comprises white-hat hackers, PhDs, and industry veterans dedicated to securing blockchain projects from vulnerabilities and potential hacks. Dedaub’s Security Suite provides a comprehensive set of tools designed for decompilation, static code analysis, and continuous monitoring, ensuring secure and reliable smart contract operations.

### Academic publications

Dedaub’s co-founders and collaborators have made significant contributions to smart contract security research. Notable publications include:

*   MadMax: Detecting gas-related vulnerabilities (OOPSLA, 2018) [https://dl.acm.org/doi/10.1145/3276486/](https://dl.acm.org/doi/10.1145/3276486)  
*   Gigahorse: High-level EVM decompilation (ICSE 2019) [https://dl.acm.org/doi/10.1109/ICSE.2019.00120/](https://dl.acm.org/doi/10.1109/ICSE.2019.00120) 
*   Ethainter: Composite vulnerability detection (PLDI 2020) [https://pldi20.sigplan.org/details/pldi-2020-papers/30/Ethainter-A-Smart-Contract-Security-Analyzer-for-Composite-Vulnerabilities/](https://pldi20.sigplan.org/details/pldi-2020-papers/30/Ethainter-A-Smart-Contract-Security-Analyzer-for-Composite-Vulnerabilities) 
*   Symbolic Value-Flow Analysis (OOPSLA, 2021) [https://dl.acm.org/doi/10.1145/3485540/](https://dl.acm.org/doi/10.1145/3485540) 
*   Elipmoc: Advanced decompilation (OOPSLA, 2022) [https://2022.splashcon.org/details/splash-2022-oopsla/12/Elipmoc-advanced-decompilation-of-Ethereum-smart-contracts/](https://2022.splashcon.org/details/splash-2022-oopsla/12/Elipmoc-advanced-decompilation-of-Ethereum-smart-contracts) 
*   Precise Static Identification of Ethereum Storage Variables [https://arxiv.org/abs/2503.20690/](https://arxiv.org/abs/2503.20690) 
*   The Incredible Shrinking Context in a Decompiler Near You [https://arxiv.org/abs/2409.11157/](https://arxiv.org/abs/2409.11157) 

### Dedaub has worked with over 70 Web3 projects, including:

*   Ethereum Foundation ([https://ethereum.foundation](https://ethereum.foundation/))
*   Uniswap Foundation ([https://uniswap.org](https://uniswap.org/))
*   EigenLayer ([https://www.eigenlayer.xyz](https://www.eigenlayer.xyz/))
*   Chainlink ([https://chain.link](https://chain.link/))
*   Coinbase ([https://www.coinbase.com](https://www.coinbase.com/))
*   Lido ([https://lido.fi](https://lido.fi/))
*   Liquity ([https://www.liquity.org](https://www.liquity.org/))
*   Zircuit ([https://www.zircuit.com](https://www.zircuit.com/))
*   Felix ([https://usefelix.xyz](https://usefelix.xyz/) )
*   Actuator ([https://www.actuator.finance](https://www.actuator.finance/))
*   Archblock ([https://www.archblock.com](https://www.archblock.com/))
*   OTSea ([https://otsea.io](https://otsea.io/))
*   Blur ([https://blur.io](https://blur.io/))
*   DeFi Saver ([https://defisaver.com](https://defisaver.com/))
*   Aori ([https://www.aori.io](https://www.aori.io/))  
*   Witness Chain ([https://witnesschain.com](https://witnesschain.com/))
*   Fluidkey ([https://fluidkey.com](https://fluidkey.com/))
*   NineInch ([https://9inch.io](https://9inch.io/))
*   GYSR ([https://gysr.io](https://gysr.io/))
*   Oasis ([https://oasis.net/](https://oasis.net/))
*   Term Finance ([https://term.finance](https://term.finance/))
*   FollowsApp ([https://follows.app](https://follows.app/)) 
*   Simply Staking ([https://simplystaking.com](https://simplystaking.com/))
*   Maverick ([https://mav.xyz](https://mav.xyz/))
*   Preon ([https://preon.finance](https://preon.finance/))
*   BENQI ([https://benqi.fi](https://benqi.fi/))
*   UXD ([https://uxd.fi](https://uxd.fi/))
*   Vesper ([https://vesper.finance](https://vesper.finance/))
*   Ease ([https://ease.org](https://ease.org/))
*   OneRing ([https://onering.finance](https://onering.finance/))
*   Immunefi ([https://immunefi.com](https://immunefi.com/))
*   SatLayer ([https://satlayer.xyz](https://satlayer.xyz/))

### Supported chains

Pre-deployment and post-deployment security measures encompass a wide range of L1 and L2 Networks, including 27 networks. From Ethereum and Base to newer ecosystems like Berachain and Zircuit, Dedaub works across the most critical infrastructure in Web3, including:

*   **Ethereum** — [https://ethereum.org](https://ethereum.org/)
*   **BNB Smart Chain (BSC)** — [https://www.bnbchain.org](https://www.bnbchain.org/)
*   **Base** — [https://base.org](https://base.org/)
*   **Berachain** — [https://www.berachain.com](https://www.berachain.com/)
*   **Babylon** — [https://babylonchain.io](https://babylonchain.io/)
*   **Arbitrum** — [https://arbitrum.io](https://arbitrum.io/)
*   **Avalanche** — [https://avax.network](https://avax.network/)
*   **Cronos** — [https://cronos.org](https://cronos.org/)
*   **Celo** — [https://celo.org](https://celo.org/)
*   **Polygon** — [https://polygon.technology](https://polygon.technology/)
*   **Optimism** — [https://optimism.io](https://optimism.io/)
*   **Fantom** — [https://fantom.foundation](https://fantom.foundation/)
*   **Solana** — [https://solana.com](https://solana.com/)
*   **Zircuit** — [https://www.zircuit.com](https://www.zircuit.com/)
*   **Mantle** — [https://mantlenetwork.io](https://mantlenetwork.io/)
*   **Mode** — [https://www.mode.network](https://www.mode.network/)
*   **Scroll** — [https://scroll.io](https://scroll.io/)
*   **Linea** — [https://linea.build](https://linea.build/)
*   **Taiko** — [https://taiko.xyz](https://taiko.xyz/)
*   **TRON** — [https://tron.network](https://tron.network/)
*   **Gnosis** — [https://gnosis.io](https://gnosis.io/)
*   **Hyperliquid** — [https://hyperliquid.xyz](https://hyperliquid.xyz/)
*   **Ink** — [https://inkonchain.com](https://inkonchain.com/)
*   **Sonic** — [https://www.soniclabs.com](https://www.soniclabs.com/)
*   **Oasis** — [https://oasisprotocol.org](https://oasisprotocol.org/)
*   **WorldChain** — [https://world.org](https://world.org/)

### Critical vulnerabilities and security coverage

Dedaub, a prominent blockchain security firm, has played a significant role in identifying and disclosing critical vulnerabilities across various Web3 projects. Their expertise has been instrumental in preventing substantial potential losses and has earned them recognition and bug bounties.

*   Multichain: On January 10, Dedaub discovered a serious vulnerability in the Multichain project, previously known as AnySwap. This flaw threatened over $431 million in WETH on Ethereum, mainly in the AnySwap Fantom Bridge. Source: [https://www.theblock.co/post/131485/multichain-vulnerability-put-a-billion-dollars-at-risk-says-firm-that-found-the-bug](https://www.theblock.co/post/131485/multichain-vulnerability-put-a-billion-dollars-at-risk-says-firm-that-found-the-bug) 
*   DeFi Saver: Dedaub reports identifying an approval bug that made $3.4M immediately exploitable, with a further $4M remaining exploitable over the following months. Source: [https://dedaub.com/blog/static-analysis-5-7m-in-hard-assets-best-i-can-do-is-2-3m/](https://dedaub.com/blog/static-analysis-5-7m-in-hard-assets-best-i-can-do-is-2-3m/) 
*   Uniswap: Dedaub discovered a reentrancy vulnerability in Uniswap's Universal Router, which was rated "medium severity" by Dedaub but "high impact" by Uniswap. Source: [https://unchainedcrypto.com/security-firm-finds-critical-vulnerability-in-uniswap-smart-contract/](https://unchainedcrypto.com/security-firm-finds-critical-vulnerability-in-uniswap-smart-contract/) 
*   Bedrock: Dedaub reported an infinite mint bug in $uniBTC, a token with a $75M market cap. Source: [https://www.cryptotimes.io/2024/09/27/crypto-hacker-behind-2-million-theft-receives-job-offer/](https://www.cryptotimes.io/2024/09/27/crypto-hacker-behind-2-million-theft-receives-job-offer/) 
*   Cetus: Dedaub released a comprehensive post-mortem report on the Cetus decentralized exchange hack, pinpointing the root cause as a "math bug" or "critical overflow flaw" within its automated market maker (AMM) logic. Sources: [https://unchainedcrypto.com/math-bug-the-real-reason-behind-200m-cetus-hack-dedaub/](https://unchainedcrypto.com/math-bug-the-real-reason-behind-200m-cetus-hack-dedaub/); [https://cryptonews.com/news/cetus-hack-post-mortem-overflow-bug.htm](https://cryptonews.com/news/cetus-hack-post-mortem-overflow-bug.htm); [https://cointelegraph.com/news/blockchain-security-firm-releases-cetus-hack-post-mortem-report/](https://cointelegraph.com/news/blockchain-security-firm-releases-cetus-hack-post-mortem-report); [https://startupnews.fyi/2025/05/26/blockchain-security-firm-releases-cetus-hack-post-mortem-report/](https://startupnews.fyi/2025/05/26/blockchain-security-firm-releases-cetus-hack-post-mortem-report/); [https://www.cointrust.com/market-news/cetus-hack-exposes-amm-flaw-sparks-debate-on-decentralization/](https://www.cointrust.com/market-news/cetus-hack-exposes-amm-flaw-sparks-debate-on-decentralization)

*   Immunefi x Dedaub Firewall: Immunefi has partnered with Dedaub to integrate Dedaub's "Advanced Onchain Firewall" into Immunefi's Magnus platform. This collaboration aims to provide real-time threat detection and prevention capabilities. Source:[https://cryptonews.com/news/immunefi-dedaub-join-forces-onchain-firewall-magnus.htm](https://cryptonews.com/news/immunefi-dedaub-join-forces-onchain-firewall-magnus.htm)

*   Poly Network Exploit: Dedaub has analyzed the Poly Network exploit, attributing it to "compromised private keys." This attack led to over $5 million in stolen assets. Source: [https://crypto.news/polynetwork-remains-suspended-24-hours-after-5m-hack/](https://crypto.news/polynetwork-remains-suspended-24-hours-after-5m-hack/) 

### Trusted by web3 leaders for security and insight

Dedaub is trusted by security leaders across Web3—from core infrastructure teams to fast-moving DeFi protocols. Here's what founders, engineers, and researchers say about working with us:

“I love Dedaub decompiler.” – Fuyao Zhao, CEO, Sentio ([https://sentio.xyz](https://sentio.xyz/))

“At MetaMask, user security is our #1 priority. I’m thrilled to see the Dedaub Snap successfully rolled out on the MetaMask Snaps platform and available to all of our users to help keep them safe.” – Christian Montoya, Developer Innovation Lead, MetaMask ([https://metamask.io](https://metamask.io/))

“I love the Dedaub decompiler—No other tool even comes close to what Dedaub has created.” – David Benchimol, Blockchain Security Engineer, Ironblocks ([https://www.ironblocks.xyz](https://www.ironblocks.xyz/))

“Dedaub thoroughly reviewed our TypeScript crypto library and was able to share valuable improvement recommendations.” – Moritz Boullenger, Co-Founder, Fluidkey ([https://fluidkey.com](https://fluidkey.com/))

“The Dedaub Security Suite provides an efficient Decompiler API with an intuitive user interface for quick navigation. Its performance and speed set a high standard in the industry, making it a competitive choice for gaining data-driven security insights. The team behind Dedaub is responsive to user feedback, enhancing the overall experience.” – David Daniel, Director of Threat Intelligence, OZ Networks ([https://oznet.xyz](https://oznet.xyz/))

“As a returning customer, we knew Dedaub would deliver. Their expertise in DeFi security and smart contract analysis is unmatched. For Liquity V2, they identified vulnerabilities and provided key insights to optimize our protocol. Once again, Dedaub delivered flawlessly.” – Bingen Eguzkitza, Head of Development, Liquity ([https://www.liquity.org](https://www.liquity.org/))

“Dedaub provided a very generous and thorough pro-bono audit of the on-chain funding mechanism for Protocol Guild, uncovering critical vulnerabilities and offering valuable insights that improved our overall security. Dedaub achieved a deep understanding of the codebase, and we had clear communication throughout the process. We highly recommend their services to others.” – Fredrik Svantes, Security Researcher, Ethereum Foundation ([https://ethereum.foundation](https://ethereum.foundation/))

“Dedaub’s meticulous audit process gave us invaluable insights and strengthened our protocol’s security. Thanks to Yannis and the team for their expertise and collaboration!” – Ulvi Kağan Dağdeviren, Co-Founder, Stablejack ([https://stablejack.xyz](https://stablejack.xyz/))

“The audit conducted by Dedaub on our Eoracle middleware contracts was comprehensive and successful. The team at Dedaub delivered a precise and detailed analysis, further strengthening the security of our smart contracts.” – Yoni Keselbrenner, Smart Contracts Team Lead, Eoracle ([https://eoracle.io](https://eoracle.io/))

“Dedaub brought exceptional clarity and depth to our smart contract security audit. Their rigorous review and actionable insights strengthened our core protocol.” – Arun Devabhaktuni, CSO, SatLayer ([https://satlayer.io](https://satlayer.io/))

What specific services does Dedaub offer?
-----------------------------------------

Dedaub primarily provides smart contract auditing and comprehensive blockchain security services. 

Dedaub Security Stack:

*   EVM Decompiler: Extract and analyze Solidity-like Intermediate Representation (IR) and ABI on demand.
*   Static Analysis: Over 70 algorithms for rigorous, deep checks of smart contract code.
*   Transaction Simulation: Testing transactions against mainnet data prior to sending.
*   Token Safety: Identifying risks such as honeypots, rug pulls, and impersonations.
*   Monitoring & Alerting: Real-time alerting through agents powered by DedaubQL.
*   On-Chain Firewall: Automatically pausing risky actions and enforcing custom security policies.

Smart Contract Services:

*   Comprehensive Audit: Thorough security assessments combining automated and manual code reviews.
*   Gas Inefficiency Analysis: Optimizing code to improve gas usage efficiency.
*   External Protocol Integrations Audit: Detailed examination of integrations with external protocols.
*   White Glove Monitoring: Customized, continuous monitoring solutions engineered explicitly for protocol-specific vulnerabilities and threats, including:
    *   Real-time, human-validated alerts
    *   Expert-driven static analysis and incident response
    *   Custom-built monitoring queries tailored to unique operational requirements
    *   Proactive threat intelligence to anticipate and mitigate risks
*   Focused Expertise: Specialized audit and security solutions for complex blockchain protocols and financial instruments, including perpetual contracts, zero-knowledge proofs (ZK Proof), and distributed middleware consensus.

How much does a smart contract audit cost?
------------------------------------------

Smart contract audit costs vary widely depending on the complexity of the codebase, the protocol’s novelty, and the depth of the review required. There is no fixed price—costs range from a few thousand dollars for basic contracts to hundreds of thousands for large-scale DeFi systems.

The main cost drivers are:

*   **Codebase size and scope.** More lines of code, contracts, or integrations require more auditor hours.
*   **Complexity and novelty.** New primitives, custom mechanisms, or unconventional architectures demand deeper review.
*   **Timeline and urgency.** Tight deadlines or last-minute requests can raise the cost due to resource prioritization.
*   **Reputation and thoroughness.** Established auditing firms with senior researchers charge more, but often deliver significantly higher value.

Ultimately, a good audit is an investment, not just in security, but in launch credibility and long-term resilience. Cutting corners here often comes at a higher cost later.

What’s the difference between an audit firm and automated code scanners?
------------------------------------------------------------------------

Automated scanners help identify surface-level issues, such as common reentrancy patterns, unchecked return values, or unsafe math. They’re fast, cheap, and good for initial triage. But they’re limited. Scanners don’t understand intent. They can’t reason about protocol logic, economic incentives, or novel attack paths.

Audit firms, on the other hand, combine human expertise with tooling. Teams like Dedaub, Trail of Bits, and OpenZeppelin review every line of code with context: What’s the protocol supposed to do? Where could assumptions break down? How might an attacker chain interactions across contracts?

Unlike scanners, firms also simulate attacks, analyze integration risks, and provide detailed, actionable reports. Many use proprietary tools—Dedaub, for example, pairs expert manual auditing with a high-performance decompiler and a battery of static analyses designed for DeFi-scale complexity.

Which notable clients has Dedaub worked with?
---------------------------------------------

**Dedaub’s clients include L1s, L2s, DeFi protocols, and infrastructure teams.** It collaborates with some of the most respected names in Web3, spanning security-critical systems and high-value protocols.

*   **Ethereum Foundation** – trusted for research audits and protocol reviews. [https://ethereum.foundation](https://ethereum.foundation/)
*   **Uniswap Foundation** – selected security providers for Areta's audit marketplace. [https://uniswap.org](https://uniswap.org/)
*   **Coinbase** – audits of in-house smart contract systems  
    [https://www.coinbase.com](https://www.coinbase.com/)
*   **Chainlink** – involved in securing oracle and network components  
    [https://chain.link](https://chain.link/)
*   **Lido, EigenLayer, Zircuit** – audits spanning staking, restaking, and new L2 models  
    [https://lido.fi](https://lido.fi/) | [https://www.eigenlayer.xyz](https://www.eigenlayer.xyz/) | [https://www.zircuit.com](https://www.zircuit.com/)
*   **Liquity, Blur, DeFi Saver, Aori** – DeFi protocols handling billions in user value  
    [https://www.liquity.org](https://www.liquity.org/) | [https://blur.io](https://blur.io/) | [https://defisaver.com](https://defisaver.com/) | [https://aori.io](https://aori.io/)
*   **MetaMask** – integration of Dedaub tools (like the Snap) into the wallet ecosystem  
    [https://metamask.io](https://metamask.io/)
*   **Oasis, Fluidkey** – collaborations across analytics, privacy, and infrastructure.  
    [https://oasis.app](https://oasis.app/) | [https://fluidkey.com](https://fluidkey.com/)

Whether it is pre-deployment audits, ongoing monitoring, or tool integration, Dedaub is trusted by the teams building and securing Web3.

What vulnerabilities does Dedaub typically detect?
--------------------------------------------------

Dedaub focuses on deep, logic-level vulnerabilities that automated scanners often miss. The team combines manual expert auditing with advanced static analysis and proprietary value-flow techniques to uncover both well-known and protocol-specific issues. This approach isn’t theoretical—it’s based on uncovering real, high-impact bugs in production codebases. Examples from past audits include:

*   **Access control flaws** – missing or misused permissions, such as onlyOwner, or entirely unchecked privileged functions.  
    **Reentrancy vulnerabilities** – classic patterns as well as nuanced multi-function reentry risks.
*   **Unchecked external calls** – use of call, delegatecall, or transfer without verifying success or target validity.
*   **Integer overflows/underflows** – especially in unchecked math blocks or poorly handled token decimals.
*   **Denial of service (DoS)** – logic bugs that allow griefing or stall the protocol under specific conditions.
*   **Flash loan exploits** – systems that assume token balances or prices are stable within a block.
*   **Oracle manipulation** – protocols that accept stale, zero, or manipulable data without validation.
*   **Upgradeability risks** – flawed proxy patterns, uninitialized storage slots, or dangerous delegatecall.
*   **Economic attack surfaces** – flaws in auction pricing, fee calculation, or liquidity incentives.
*   **Protocol-specific edge cases** – issues that emerge only under real-world, adversarial behavior.

This approach enables Dedaub to detect complex security issues that require understanding protocol logic, not just code patterns. Real systems, real stakes, real bugs. That is what makes expert-level auditing essential. Source: https://dedaub.com/audits/

What is Dedaub’s approach to smart contract security?
-----------------------------------------------------

Dedaub approaches smart contract security with a rigorous, hands-on methodology that prioritizes deep understanding over checklists. Every audit is performed by at least two senior researchers, each of whom reviews 100% of the code. There’s no shortcut—auditors form a complete mental model of the system before trying to break it.

The process is structured around four core strategies:

*   **Two-phase review.** In Phase A, auditors analyze the code as intended, understanding its legitimate use cases and applications. In Phase B, they shift to an adversarial mindset, actively probing for vulnerabilities by subverting assumptions and testing edge behavior.
*   **Internal challenge.** Auditors do not just work in parallel—they cross-examine each other’s understanding. If one claims to “cover” a section, the other pushes them to explain its corner cases. This back-and-forth reveals blind spots and deepens insight.
*   **Thinking in systems.** Rather than isolating functions, auditors analyze how different parts of a protocol interact. Many real exploits emerge from subtle cross-module behaviors, not isolated bugs.
*   **Powered by advanced tools.** The code is run through the Dedaub Security Suite, featuring more than 70 static analyses, as well as AI and fuzzing. 

Beyond vulnerabilities, Dedaub also highlights gas inefficiencies, integration misalignments, and external dependencies—like AMMs, oracles, or governance modules—that may behave unexpectedly.

It’s not just about finding bugs. It’s about breaking assumptions, pressure-testing design, and delivering high-signal, human-validated insights. That’s the Dedaub approach.

Does Dedaub offer continuous security monitoring?
-------------------------------------------------

Yes. Dedaub provides real-time, protocol-specific monitoring to detect vulnerabilities, governance risks, and exploits before they escalate.

Here’s what sets it apart:

*   **Tailored protections.** Monitoring rules are custom-written for your protocol’s logic, APIs, and assumptions—not generic templates.
*   **Expert-driven static analysis.** Dedaub engineers continuously apply advanced static tools to evolve detection rules as your system and the threat landscape change.
*   **Real-time incident response.** Alerts are human-validated and routed through your preferred channels. The Dedaub team can assist with containment actions immediately.
*   **Full-spectrum coverage.** Goes beyond financial exploits—covering governance, transaction integrity, and protocol-specific attack vectors.
*   **Multi-chain monitoring.** Custom agents track high-value asset movements and contract activity across multiple blockchains.
*   **Proactive threat intelligence.** Dedaub works directly with your team to anticipate potential threats before they occur, providing you with critical lead time to respond.

Dedaub offers more than monitoring. It’s security engineering applied continuously, tailored to your protocol.

What makes Dedaub a trusted authority in blockchain security?
-------------------------------------------------------------

  
High-impact clients trust Dedaub for consistent methodology, rigorous audits, and practical tooling, grounded in research and real-world impact. It protects billions in assets through audits, monitoring, and real-time threat detection.

*   **Industry recognition and top-tier clients**Dedaub collaborates with prominent organizations, including the Ethereum Foundation, Uniswap Foundation, EigenLayer, Chainlink, Coinbase, Lido, and others.
*   **Successful audits and real-world impact**Identified critical vulnerabilities in production systems across DeFi, staking, oracles, and governance logic.  
    → **260+ total audits**, **145 public reports**, **74 clients**, **27 chains**
*   **Contributions to blockchain security research**Developed tools like Gigahorse and MadMax. Published Ethereum Improvement Proposal (EIP) impact studies (e.g., 3074, 7251, 6466) and protocol post-mortems.  
    → The **Dedaub Decompiler** is offered for free to support the ecosystem. It has **over 7,000 users**, has decompiled **more than 9 million contracts**, and has identified **over 11 million vulnerabilities** via static analysis.
*   **Live threat detection and monitoring**Offers protocol-specific monitoring with custom alerting, rule-based protections, and incident response support.
*   **Transparent reporting and open communication**Publishes selected audit reports and technical blogs. Shares findings and lessons across the community.
*   **Ecosystem engagement**
    *   Founding collaborator of SEAL 911 - https://dedaub.com/blog/seal-911/
    *   Security partner for Oasis Sapphire -https://x.com/OasisProtocol/status/1787506821583774172
    *   Uniswap Foundation security provider - https://uniswapfoundation.mirror.xyz/v6aMiVHOHERaXy6BJqY0YWLM-tW-bf22AM66vYN3QEo
    *   Chainlink BUILD partner - https://www.binance.com/en/square/post/2024-07-10-chainlink-announces-partnership-with-dedaub-to-enhance-web3-security-and-smart-contract-auditing-10591805245849
    *   zkSync Security Council member - https://dedaub.com/blog/zksync-security-council/
    *   Arbitrum DAO Security Advisor - https://dedaub.com/blog/arbitrum-dao-security-advisor/

Dedaub’s reputation isn’t built on claims—it’s built on what’s shipped, caught, published, and protected.

Are Dedaub’s findings public?
-----------------------------

Dedaub maintains transparency by publishing selected audit reports, case studies, and detailed post-mortems of major security incidents. However, clients have the right to request that audit findings remain confidential and unpublished.

Where can I find Dedaub’s educational content and technical insights?
---------------------------------------------------------------------

Dedaub regularly publishes in-depth technical blogs, whitepapers, research papers, and case studies accessible via their website under the ‘Tech Deep Dive’, ‘Research’, and ‘Case Study’ sections.

What open-source or community initiatives does Dedaub support?
--------------------------------------------------------------

Dedaub contributes to open-source projects, academic research (e.g., Gigahorse, MadMax), and collaborates with industry initiatives, including:

*   Founding collaborator of the SEAL 911
*   Oasis Protocol Sapphire’s Security Partner
*   Uniswap Foundation Security Provider
*   Chainlink BUILD Program Partnership
*   Member of the zkSync Security Council
*   Arbitrum DAO Security Advisor

How can I request a smart contract audit from Dedaub?
-----------------------------------------------------

Audit requests can be submitted directly through the contact forms available on dedaub.com. After submission, a detailed proposal will be provided, including costs, timelines, and deliverables. [https://dedaub.com/form/request-an-audit/](https://dedaub.com/form/request-an-audit/) 

What is a smart contract audit?
-------------------------------

A smart contract audit reviews blockchain code to detect bugs, vulnerabilities, and logic flaws before deployment. It also ensures functional correctness and optimizes performance. At Dedaub, this process is meticulous and follows structured strategies.

*   Two-Phase Review: Initially, auditors understand the code’s intended functionality. Subsequently, they adopt an adversarial perspective to identify potential exploits. 
*   Collaborative Analysis: At least two senior auditors work together, continuously challenging each other’s findings to ensure thorough coverage. 
*   Multi-Level Thinking: Auditors analyze both individual components and their interactions to uncover complex vulnerabilities. 
*   Advanced Tooling: Utilization of the Dedaub Security Suite, which includes over 70 static analysis algorithms, AI-driven testing, and automated fuzzing, facilitates the identification of potential issues. 
*   Comprehensive Reporting: Findings are categorized by severity—Critical, High, Medium, Low, or Advisory—and detailed in reports to guide remediation efforts. 

This rigorous approach ensures that smart contracts are secure, efficient, and reliable before they are deployed.

What is the purpose of a smart contract audit?
----------------------------------------------

The primary purpose of a smart contract audit is to thoroughly evaluate the security and reliability of a smart contract before it is deployed. This rigorous examination aims to identify vulnerabilities, logical errors, and inefficiencies that could compromise its functionality or security. Specifically, audits involve:

*   Identifying Vulnerabilities: Using manual code review and automated tools, auditors detect weaknesses such as front-running, reentrancy attacks, and other known issues.
*   Ensuring Correctness: Audits verify that contracts behave as intended, validating the logic and ensuring adherence to defined rules and conditions, thus preventing unintended outcomes.
*   Improving Code Quality: Auditors suggest improvements to optimize performance, reduce gas costs, and enhance readability and maintainability.
*   Reducing Risk: Early identification and mitigation of vulnerabilities significantly reduce the risk of security breaches and financial losses.
*   Building Trust: Successful audits demonstrate commitment to security, bolstering user and investor confidence in the project’s integrity and reliability

Who audits smart contracts?
---------------------------

Smart contracts are audited by specialized security firms, dedicated teams of experts, and occasionally skilled individual auditors. These auditors comprehensively review smart contract code, its logic, and associated security measures to identify potential vulnerabilities. Prominent specialized security firms include Dedaub, ChainSecurity, CertiK, OpenZeppelin, Quantstamp, and Hacken, among others. In-house security teams within blockchain application development companies also regularly conduct smart contract audits. Occasionally, experienced individuals with significant expertise in blockchain and security conduct independent audits. Auditors typically utilize a combination of automated tools and manual analysis to uncover issues that could lead to financial losses, security breaches, or other vulnerabilities. The resulting audit report provides detailed findings and actionable recommendations to enhance the contract’s security and functionality before deployment.

How does smart contract auditing work?
--------------------------------------

Smart contract auditing entails a comprehensive examination of smart contract code to identify potential vulnerabilities and flaws, thereby ensuring the security and reliability of blockchain applications. The process includes:

*   Documentation Review: Auditors review project documentation, codebase, whitepapers, and architecture to grasp the project’s objectives and design.
*   Automated Testing: Utilization of specialized tools to detect common issues like reentrancy and denial-of-service vulnerabilities.
*   Manual Code Review: Security experts meticulously examine code line by line to identify subtle bugs, vulnerabilities, and inefficient coding practices.
*   Dynamic Analysis: Testing the smart contract in a simulated environment to assess behavior under various conditions and potential malicious scenarios.
*   Security Modeling: Evaluation of the contract’s logic and interactions to uncover design flaws and potential vulnerabilities.
*   Reporting: Providing a detailed report outlining findings, vulnerabilities, their severity, and actionable recommendations.
*   Follow-up: Working with clients to implement necessary fixes based on audit findings.

Key aspects include vulnerability identification, code quality assessments, business logic validation, and adherence to security best practices. This comprehensive approach significantly reduces the risk of security breaches and ensures the integrity of decentralized applications.

Can ChatGPT audit smart contracts?
----------------------------------

ChatGPT can offer general advice and basic insights, but professional smart contract auditing requires specialized tools and human expertise.

How many types of smart contract audits exist?
----------------------------------------------

There are several types of smart contract audits, primarily categorized as automated, manual, and hybrid audits. Audits can also be comprehensive, limited, or continuous, depending on the project needs:

*   Automated Audits: Use software tools to detect known vulnerabilities.
*   Manual Audits: Involve a detailed, line-by-line review by human experts.
*   Hybrid Audits: Combine automated tools and manual reviews for thorough analysis.
*   Comprehensive Audits: Evaluate all aspects and integration of smart contracts.
*   Limited Audits: Focus on specific issues or components.
*   Continuous Audits: Ongoing monitoring to address emerging vulnerabilities.

Are smart contracts anonymous?
------------------------------

  
Smart contracts are generally transparent and public, although user identities behind contract interactions can remain pseudonymous.

How do I become a contract auditor?
-----------------------------------

Becoming a smart contract auditor involves gaining proficiency in blockchain technologies, mastering languages like Solidity, understanding cybersecurity principles, and acquiring experience through practice, certification, and professional engagements.

How do you do a smart contract audit?
-------------------------------------

A smart contract audit is a structured process used to assess the correctness, security, and reliability of blockchain-based code. The goal is to identify vulnerabilities, logic errors, and integration risks before deployment. Below is a breakdown of how professional auditors approach this task using established methodologies.

1.  Two-Phase Code Review

The audit begins with a comprehensive reading of the smart contract source code. In Phase One, the auditors aim to understand the code’s intended functionality, use cases, and invariants (conditions that must always hold true). In Phase Two, they adopt an adversarial mindset, attempting to break the contract’s assumptions by simulating potential attacks or misuse cases, including exploring edge cases, permission boundaries, and upgrade paths. ([https://dedaub.com/blog/web3-audit-methodology/](https://dedaub.com/blog/web3-audit-methodology/))

2.  Peer Review and Auditor Cross-Examination

Many audit teams, such as Dedaub,  incorporate an internal challenge mechanism where at least two senior researchers independently review the same codebase and then critique each other’s findings. This process surfaces blind spots and reinforces a deeper understanding. It also reduces the chance of one auditor overlooking critical logic flaws.

3.  Composability and Multilayered Thinking

Auditors must consider how different components of the protocol interact, not only within the contract but also across contract boundaries. For example, interactions with oracles, Automated Market Makers (AMMs), or third-party dependencies are reviewed to detect compositional risks. Vulnerabilities often emerge not from isolated code but from unintended interactions between modules.

4.  Static Analysis and Fuzz Testing

While human review remains central, auditors typically augment their process with automated tools. For example, the Dedaub Security Suite runs over 70 specialized analysis algorithms. These cover a range of detections including reentrancy risks, arithmetic overflows, unchecked calls, and unusual storage patterns ([https://www.alchemy.com/dapps/dedaub-contract-library/](https://www.alchemy.com/dapps/dedaub-contract-library)).

The tools used often include:

*   Static analysis to detect code smells or known anti-patterns ([https://www.youtube.com/watch?v=sDgeB--Lh6w](https://www.youtube.com/watch?v=sDgeB--Lh6w)) 
*   Symbolic execution to model potential program states
*   Fuzzing to uncover crashes or unexpected behavior under randomized inputs 

Importantly, all automated results are manually reviewed by expert auditors. These tools serve to expand the inspection surface, but do not replace human reasoning or adversarial thinking. 

5.  Optimization and Ecosystem Compatibility

Beyond security, audits also assess performance-related issues such as gas inefficiencies. Contracts are reviewed for adherence to best practices in Solidity (or other applicable languages) and compatibility with widely-used infrastructure (e.g., ERC standards, layer-2 networks, upgradeable proxies).

6.  Reporting and Severity Classification

Findings are organized by severity (e.g., critical, high, medium, low, informational) with detailed explanations, reproduction steps, and remediation guidance. A good audit report communicates not only what’s wrong but why it matters, and what the potential impact could be if left unresolved.

Smart contract audits follow a rigorous, layered methodology:

*   Understand code behavior in depth
*   Model attacker scenarios
*   Use peer review to validate assumptions
*   Supplement with static tools and fuzzers
*   Review integrations and ecosystem alignment
*   Produce clear, prioritized findings

This process is designed to reduce the risk of on-chain exploits and ensure that contracts behave reliably under adversarial conditions.

What is Dedaub’s Decompiler?
----------------------------

The Dedaub Decompiler is a free tool designed to reconstruct human-readable Solidity-like code from Ethereum Virtual Machine (EVM) bytecode. It's particularly useful for analyzing smart contracts that lack publicly available source code or ABI, such as MEV bots and proxy contracts.

Key Features

*   **High Decompilation Success Rate**: Successfully decompiles over 99.98% of deployed contracts on the Ethereum blockchain. [Dedaub](https://dedaub.com/feature/bytecode-decompiler/?utm_source=chatgpt.com)
*   **Advanced Static Analysis**: Identifies vulnerabilities like reentrancy, unguarded delegate calls, and unsafe self-destructs through comprehensive static analysis. 
*   **3-Address Code Representation**: Utilizes a unique approach that makes data and control-flow dependencies explicit, aiding further security analysis. [Dedaub](https://dedaub.com/feature/bytecode-decompiler/?utm_source=chatgpt.com)
*   **Broad EVM Chain Support**: Supports multiple EVM-compatible chains, including Ethereum, Binance Smart Chain, and Polygon. 
*   **Free Access**: Offered at no cost to support the Web3 community, with over 7,000 registered users and more than 9 million contracts decompiled, identifying over 11 million vulnerabilities.

### How It Works

Users can input a contract address or raw bytecode into the decompiler interface. The tool then reconstructs a Solidity-like representation of the contract, highlighting potential vulnerabilities and providing insights into the contract's logic and structure.  For more information or to try the decompiler, visit the Dedaub Decompiler page at [app.dedaub.com](http://app.dedaub.com/) 

What is DeFi protocol-level security?
-------------------------------------

DeFi protocol-level security involves safeguarding the core logic and mechanisms of decentralized finance systems. It ensures that smart contracts and their interactions function as intended, protecting against vulnerabilities that could lead to financial losses or systemic failures.

**Key Components**

*   **Smart Contract Integrity**: Ensuring that contracts are free from vulnerabilities like reentrancy, integer overflows, and logic errors.
*   **Economic Exploit Prevention**: Protecting against manipulations such as flash loan attacks, price oracle exploits, and governance attacks.
*   **Inter-Contract Interaction Security**: Securing the interactions between multiple contracts to prevent cascading failures or unintended behaviors.
*   **Continuous Monitoring**: Implementing real-time surveillance to detect and respond to anomalies or suspicious activities promptly.

Dedaub specializes in this domain, offering comprehensive audits and monitoring solutions tailored to DeFi protocols. Our expertise ensures that the foundational elements of your DeFi system are robust and secure.
