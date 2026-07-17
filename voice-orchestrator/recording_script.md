# Recording Script

Read these aloud to build your voice dataset. Each numbered line ≈ one clip
(5–15 s). Stay in the section's style. Total ≈ 30 min / ~4,300 words.

Tip: `record.py` shows you one line at a time and saves each take into the
right folder with the transcript filled in automatically.

---

## Section A — NEUTRAL (calm narration)  ·  target ~18 min

Phonetically balanced sentences (broad sound coverage) + flowing prose.

1. The early morning sun cast long shadows across the quiet valley floor.
2. She sells sea shells by the shore, and the shore is never truly silent.
3. Six zebras jogged quietly, vexing the sleepy, dozing watchman nearby.
4. A gentle breeze carried the scent of rain over the wheat fields.
5. Numbers like three, thirteen, and thirty are often confused when spoken.
6. The judge weighed the evidence carefully before reaching her verdict.
7. Bright blue balloons floated above the crowded market square.
8. Please pour the water into the tall glass without spilling a single drop.
9. Thick fog rolled in from the harbor as the last ferry departed.
10. The old wooden bridge creaked under the weight of the loaded cart.
11. Every author eventually learns that clarity beats cleverness.
12. The lecture covered history, geography, and a little bit of chemistry.
13. He whispered the answer so softly that only the front row could hear.
14. Autumn leaves drifted down, red and gold, onto the damp cobblestones.
15. A good explanation removes confusion instead of adding to it.
16. The train arrived precisely on time, which surprised absolutely everyone.
17. Cool rivers wind through warm meadows on their way to the wide sea.
18. Reading aloud reveals the rhythm that silent reading tends to hide.
19. The museum's newest exhibit opens to the public early next spring.
20. Careful measurement is the difference between a bridge and a collapse.
21. Most people underestimate how much tone changes the meaning of a word.
22. The recipe calls for flour, sugar, two eggs, and a pinch of patience.
23. Distant thunder rumbled while the children counted the seconds between.
24. A single well-placed pause can carry more weight than a loud voice.
25. The librarian catalogued each volume with quiet, unhurried precision.
26. Snow settled on the rooftops, softening every hard edge of the town.
27. Good narration sounds like a person thinking, not a machine reciting.
28. The path forked twice before finally reaching the lighthouse cliff.
29. Warm light spilled from the kitchen window onto the frosted garden.
30. When in doubt, read the sentence the way you would say it to a friend.

## Section B — EMPHATIC (engaged, persuasive)  ·  target ~8 min

Push energy onto the **bold** words. This is your "headline" voice.

31. This is the single **most important** thing you will read all week.
32. Stop. **Think** about what that number actually means for your users.
33. It's not slightly better — it is **dramatically, measurably** better.
34. Here's the part nobody tells you, and it **changes everything**.
35. We didn't just fix the bug. We **eliminated the entire class** of bugs.
36. Never — and I mean **never** — ship that to production untested.
37. The results were not good. They were **extraordinary**.
38. Pay attention, because **this** is where most people get it wrong.
39. That's not a feature. That is a **fundamental** shift in how it works.
40. You have one chance to make this right, so **make it count**.
41. The difference between safe and exploited is **one missing check**.
42. This matters. It matters **more** than almost anything else on the list.
43. Read that again, slowly, because it is **genuinely** that significant.
44. We proved it. We tested it. And it **works**, every single time.
45. If you remember **one** thing from this article, remember **this**.

## Section C — CONVERSATIONAL (questions, rising, lighter)  ·  target ~4 min

Natural questions and asides. Let the pitch rise on the questions.

46. So, what actually happens when the oracle returns a stale price?
47. Ever wonder why some audits catch this and others just don't?
48. Right? It seems obvious once someone finally points it out.
49. Now, you might be thinking — isn't that a bit paranoid?
50. But here's a question worth sitting with: who verifies the verifier?
51. Interesting, isn't it, how the simplest bugs cause the biggest losses?
52. Okay, so where do we go from here? Let's walk through it together.
53. Have you ever shipped code you were absolutely sure was correct?
54. And what if — just for a moment — we assumed the attacker is patient?
55. Makes you think, doesn't it, about everything we take for granted?

## Section D — DOMAIN VOCABULARY (your work words)  ·  target ~3 min

Read in your **neutral** style. Ensures your real vocabulary is captured.

56. Dedaub audits smart contracts, monitors protocols, and builds analysis tools.
57. Reentrancy, integer overflow, and access-control flaws remain the classics.
58. The oracle was manipulated through a flash-loan-funded price swing.
59. We reviewed the ERC-20 token, the AMM, and the upgradeable proxy pattern.
60. Chainlink, EigenLayer, and the Ethereum Foundation trust rigorous review.
61. A liquidity pool, a lending market, and a bridge each fail differently.
62. Static analysis catches what casual review and even fuzzing often miss.
63. Governance, delegatecall, and storage collisions deserve real scrutiny.
64. The exploit chained an approval, a callback, and an unchecked transfer.
65. Real-time monitoring flags anomalies the moment a transaction lands.

---

**Done?** You should have ~65 clips across `neutral/`, `emphatic/`,
`conversational/` and a `transcript.csv`. Run
`python orchestrator.py ingest` to validate, then
`python orchestrator.py build` to create your voice profile.
