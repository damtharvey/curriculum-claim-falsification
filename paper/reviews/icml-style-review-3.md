# ICML-Style Review 3

## 1. Summary

This paper introduces a programmatic, one-sided test for the construct validity of mathematics assessment items. The authors argue that if a program lacking a standard-tagged operation (e.g., "solve an equation") or lacking access to given quantities can still correctly answer a multiple-choice item at a rate better than chance, then the item does not strictly require that operation or information to pass. Using a census of 2,405 public-release items (New York Regents, EQAO, TIMSS, STAAR, etc.), the authors score three pre-registered families of programs: item-writing rules, test-taking strategies (like arithmetic closure), and partial-input language models (which see the question type and options but have all given numbers/quantities masked). The main finding is that two language model families (Qwen2.5 and Phi-4) can recover New York Regents Algebra I and II keys from masked stems at rates significantly above chance and modal-letter frequency. A lower-central rule (picking the second-smallest numeric option) cleared chance on Geometry and EQAO Grade 6 items, though not after family-wise error correction. An arithmetic closure strategy on STAAR Grade 5 showed an initial positive result but failed a pre-registered replication. Ultimately, the authors demonstrate that for a subset of Algebra I/II items, passing does not require the given quantities.

## 2. Claims and Evidence

The central claim—that a subset of Algebra I and II items can be passed without access to the given quantities—is rigorously supported by the masked-stem language model experiments. The authors implement strict controls: comparing results on the PDF text layer against a vision-language transcription from the page image (the "repaired" layer), employing a second independent transcription, running an option-numeral isomorph control to rule out simple memorization of specific numbers, and tracking contamination via unmasked token log-probabilities.

However, the connection between "solving without given quantities" and "not requiring the tagged operation" is more problematic. As the authors note, two item-level language-model coders disagree significantly with the publisher's tags regarding whether an item strictly requires execution on the given quantities. The authors correctly narrow their claim to "passing does not require the given quantities." While this is true, the paper conflates information masking with operation restriction. If a model recognizes the form of the options (e.g., recognizing that roots match factors, as in the Section 4.3 example) to bypass the need for givens, it is exploiting structural cues. This is a known phenomenon in NLP dataset evaluation (e.g., NLI or QA artifact exploitation, as seen in Gururangan et al. 2018 or Poliak et al. 2018), but mapping this directly to a failure of mathematics construct validity is a strong claim that relies heavily on what we define as the "tagged operation" (which the coders showed is ambiguous). 

Furthermore, the negative results (e.g., TIMSS items not yielding a witness) are properly contextualized as power-limited non-refutations rather than certifications of validity. The authors are commendably disciplined in their statistical reporting, employing strict Holm corrections and openly reporting replication failures (STAAR Grade 5 closure). 

## 3. Relation to Prior Work

The paper properly situates itself at the intersection of psychometrics (construct validity, cognitive diagnosis) and NLP (shortcut learning, choices-only baselines). It cites foundational psychometric work (Kane, Messick, Haladyna) and key NLP artifact papers. 

However, there are notable omissions in the recent literature surrounding LLM evaluation and assessment generation that weaken the contextualization:
- The paper treats LLM performance on masked stems as a proxy for item structural flaws, but does not deeply engage with recent 2024-2026 work on how LLMs exhibit surface-pattern reliance and behavioral memorization on benchmarks (e.g., *Are Large Language Models Truly Smarter Than Humans? Benchmark Contamination, Surface-Pattern Reliance, and Behavioral Memorization Across Six Frontier Models*, 2026). While the authors include an isomorph control, the literature suggests LLMs can memorize abstract structural patterns of highly mirrored exams (like NY Regents).
- Recent work evaluating the construct validity of AI-generated Q-matrices and items (e.g., *Advancing Item Writing Methods with Large Language Models and Subject Matter Experts*, 2026; *Frontiers | AI-assisted MCQ creation increases item-writing flaws through automation bias*, 2026) demonstrates that LLMs are highly sensitive to—and often replicate—the exact lexical/structural cueing biases (like longest option correct, or stem-option overlap) that this paper tests for. The fact that an LLM can exploit these cues is deeply connected to how they are trained on such flawed texts.
- Work on *JudgmentBench* (2026) and related studies show LLM scorers converge on construct-irrelevant surface cues. The authors use LLMs as item-level coders (GLM 5.2 and Kimi K3) to judge whether items require execution, finding they disagree with publisher tags. The literature suggests these models may just be latching onto surface terminology in the items rather than performing deep cognitive diagnosis, which limits the reliability of the item-level coding step.

## 4. Strengths

**S1. Methodological Rigor and Discipline.** The pre-registration of rules, strict Holm correction within families, and the requirement that a program beat the 95th percentile of random programs are excellent practices. The willingness to report the failure of the STAAR Grade 5 replication adds significant credibility to the findings.
**S2. Layered Measurement Architecture.** Recognizing that the PDF text layer is dirty (e.g., missing operators) and implementing a dual-transcription vision-language repair layer is a highly robust methodological choice that prevents artifacts of OCR/PDF parsing from driving the results.
**S3. Innovative Conceptual Framing.** Formalizing construct validity threats as executable "witness" programs (and clearly distinguishing this from claims about human student behavior) is a mathematically elegant way to operationalize an often-fuzzy psychometric concept.

## 5. Weaknesses

**W1. (Critical) Ambiguity in "Tagged Operation" vs. "Information Masking."** The core finding relies on masking given quantities (e.g., replacing numbers with [N]). If a model answers correctly, the authors claim this refutes the necessity of the "tagged operation." However, as shown in the example in Section 4.3 (zeros of a polynomial), the tag may ask to "understand the relationship," which the model *does* do by recognizing the structural relationship between $n$ placeholders and $n$ factors. Masking numbers tests information sufficiency, but does not strictly prove the operation itself wasn't performed abstractly. 
**W2. (Major) Memorization and Structural Contamination.** While the option-numeral isomorph control successfully shows the models aren't just memorizing specific numbers, recent literature (e.g., the 2026 "Truly Smarter Than Humans?" contamination audit) shows LLMs exhibit distributed memorization signatures and high sensitivity to indirect surface wording. New York Regents exams are heavily mirrored online. The models might have memorized the abstract *templates* of these specific exams, making them uniquely capable of filling in the blanks on this dataset in a way they couldn't on secure items.
**W3. (Moderate) Reliability of LLM Item Coders.** The paper uses GLM 5.2 and Kimi K3 to code item demand (execution vs. recognition), finding they disagree with the publisher. Given recent findings that LLMs struggle with nuanced Q-matrix generation and cognitive diagnostic tagging (e.g., *The Use of AI Tools to Develop and Validate Q-Matrices*, 2026), the discrepancy might reflect model failure rather than publisher error. 

## 6. Questions for Authors

**Q1.** In Section 4.3, you note that the model recognizes the $n$ placeholders correspond to $n$ factors, matching the "understand the relationship" tag. Doesn't this imply the model *is* performing the tagged cognitive operation (understanding the relationship), just on abstract symbols rather than concrete numbers? If so, does the masked-stem test actually falsify the tag?
**Q2.** For the LLM item coders (GLM 5.2, Kimi K3), did you evaluate their zero-shot coding accuracy against a gold-standard human expert baseline on a subset of items, or only against the publisher tags?
**Q3.** Given that NY Regents exams are extensively distributed online (often in template forms by test-prep sites), could the masked-stem success be a result of the models having memorized the structural templates of these specific exams, rather than exploiting general item-writing flaws?

## 7. Minor Issues / Typos

- The description of the Holm correction families in Section 2.2 is slightly repetitive across paragraphs and could be consolidated for readability.
- It would be helpful to explicitly define "format chance" with an equation early in Section 2.2 rather than inline later.

## 8. Overall Recommendation

**Overall: 3 (Weak Accept)**

This paper presents a highly rigorous, methodologically disciplined approach to operationalizing construct validity through programmatic witnesses. The use of a dual-transcription repair layer and pre-registered replication tests sets a high standard for empirical rigor. However, the conceptual leap from "an LLM can guess the answer without the numbers" to "the item fails its tagged construct claim" is problematic, particularly given how LLMs process abstract templates and the ambiguity of what operations like "understand relationships" actually require. Furthermore, the paper misses some highly relevant 2026 context on LLM benchmark contamination and automated Q-matrix generation. It is a very strong borderline paper: addressing the conceptual gap between information masking and operation execution in the rebuttal would likely push it to a clear accept.

## 9. Confidence Score

**Confidence: 4 (Confident)** 

## Priority List (To move up one point)
1. Provide a clearer theoretical justification distinguishing between testing for *information sufficiency* (what the masked-stem test does) and testing for *operation necessity* (what the tags claim), particularly addressing the example in Section 4.3.
2. Acknowledge the limitations of using LLMs as item-level coders for cognitive demand, citing recent 2026 literature on automated Q-matrix generation.
3. Discuss the possibility of abstract template memorization (beyond exact number memorization) as a driver of the NY Regents results.

## Hackathon Audience Note
An audience of assessment researchers (Minds and Machines hackathon) would immediately object to the premise that an LLM's ability to shortcut an item says anything meaningful about the human cognitive processes elicited by that item. They would argue that standard tests are designed for human cognitive architectures, which do not process text via token probabilities or possess billions of parameters of prior structural exposure. Even if an LLM can parse the abstract form of a NY Regents question without the numbers, a 9th grader taking the test is almost certainly actually solving the math. The researchers would challenge the paper's implicit assumption that a vulnerability to a synthetic programmatic attack constitutes a failure of construct validity in human educational measurement.