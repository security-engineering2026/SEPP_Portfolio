# SOFTWARE FORGE — MASTER PRODUCT MANIFEST v1.1

Status: PRODUCT CONTRACT — APPROVED REVISION FROM v1.0

## 1. Product Identity
Software Forge is a Software Lifecycle Control Plane / Product Lifecycle Orchestrator. It is not merely an AI coding assistant, IDE, Git client, CI/CD server, test framework, code generator, project manager, LLM wrapper, or competitive-analysis tool.

Lifecycle:
Intent -> Contract -> Requirements -> Architecture -> Implementation -> Build -> Installation -> Execution -> Functional Validation -> UI Validation -> Security -> Red Team -> Blue Team -> Evidence -> Independent Verification -> Release -> Evolution.

## 2. Core Modes
BUILD NEW: Natural Language -> Intent -> Requirements -> Architecture -> Manifest -> Approval -> Project Creation -> Build -> Test -> Repair -> Verification -> Release.

REPAIR IMPORTED: ZIP / Repository / Local Project / AI-generated Project is untrusted. No inherited PASS. Import -> Inventory -> Manifest Discovery -> Contract Validation -> Architecture Discovery -> Build -> Install -> Run -> Functional Test -> UI Test -> Security -> Red Team -> Blue Team -> Evidence -> Diagnose -> Repair -> Rebuild -> Regression -> Verify -> Release.

EVOLVE EXISTING: Existing Product -> Existing Contract -> Existing Architecture -> User Request -> Change Analysis -> Manifest Delta -> Impact Analysis -> Approval -> Implementation -> Build -> Test -> Repair -> Regression -> Verification -> Release.

## 3. Fundamental Principles
User Intent Preservation: the approved Product Contract is authoritative. Forge, agents and providers must not silently remove requirements, weaken acceptance criteria, remove target platforms, disable security requirements, delete tests, or redefine Definition of Done. Contract changes require Change Request -> Diff -> Reason -> Impact -> Approval -> New Manifest Version.

Evidence Over Claims: PASS is not evidence. AI claims and previous developer claims are not independent verification.

Independent Verification: the builder/repair agent cannot be the sole authority. Builder -> Product -> Independent Verifier -> Evidence -> Gate.

No Artificial Iteration Limit: repair cycles are not capped by an arbitrary count. Resource policies may control CPU, RAM, disk, wall time, API cost, network and human approval. Resource exhaustion produces PAUSED, not false PASS.

Pattern Borrowing, Not Assumption: external products and engineering sources may be studied for documented capabilities, workflows, UX patterns and architectural patterns, but observations do not automatically become requirements, truth, or permission to copy protected implementation. Every external insight must retain provenance and evidence.

## 4. Resolution Cascade
Failure -> Local Diagnosis -> Project Knowledge -> Previous Successful Strategies -> Alternative Tool/Toolchain -> Official Documentation -> Internet Research -> Repository/Issue Research -> AI Provider #1 -> AI Provider #2 -> AI Provider #N -> Candidate Solution -> Sandbox -> Patch -> Build -> Test -> Independent Verification.

If unsuccessful, diagnose again and continue with another strategy. Stop only at a real PASS, BLOCKED condition, or policy-driven PAUSE.

## 5. Hardware / Environment Failure
Forge must distinguish software, environment, network, provider, OS and hardware failures.

For genuine hardware problems:
Hardware Diagnosis -> Root Cause -> Workaround -> Required Hardware Change -> Recovery Procedure -> Resume.

The result must include evidence, practical workaround where possible, required changes and a resume point.

## 6. Persistent Engineering Memory
Project knowledge must not depend on a chat session.

Product DNA includes: Intent, Manifest History, Requirements, Architecture, Components, Dependencies, Toolchains, Environments, Providers, Tests, Failures, Successful Strategies, Failed Strategies, Security Findings, Decisions, Approvals, Evidence, Releases and Current State.

Chat closure, time gaps, provider/model changes or Forge restart must not destroy project state.

## 7. Upload Independence
Forge must not depend on AI-service upload limits. Projects should be accessible directly from Local Disk, Local Repository, Git, approved network storage or approved remote repositories. AI providers receive only the context required for the current task.

## 8. Portable Project Knowledge
Project knowledge must be exportable/importable, e.g. Product.forgepack, containing Manifest, Product DNA, Architecture, Decisions, Failures, Strategies, Evidence, Environment, Releases and Integrity Metadata.

Export -> Transfer -> Import -> Integrity Verification -> Restore -> Resume.

## 9. Product Contract / Manifest
The Manifest is the formal product contract.

Required baseline fields:
forge_manifest_version
product.id
product.name
product.version
intent.description
targets
requirements.functional
requirements.ui
requirements.security
requirements.reliability
requirements.performance
requirements.compatibility
deliverables
validation.unit
validation.integration
validation.runtime
validation.ui
validation.security
validation.red_team
validation.blue_team
validation.regression
validation.independent_verification
release.evidence_required
release.clean_install_required
release.clean_uninstall_required

## 10. Manifest Builder
Natural Language -> Intent Understanding -> Requirement Extraction -> Architecture Proposal -> Manifest Draft -> User Review -> Approval -> FORGE_MANIFEST.

For existing products:
Existing Product -> Existing Contract -> User Request -> Change Analysis -> Manifest Delta -> Impact Graph -> Approval.

## 11. Requirement System
Every requirement should have ID, Description, Priority, Acceptance Criteria, Dependencies, Affected Components, Tests, Evidence and Verification State.

## 12. Requirement Lineage
User Intent -> Manifest -> Requirement -> Architecture -> Component -> Code Change -> Build -> Test -> Runtime -> Evidence -> Verification -> Release.

## 13. Seven Architectural Planes
1. PRODUCT PLANE: Intent, Contract, Manifest, Requirements, Requirement Graph, Change Management.
2. ORCHESTRATION PLANE: Planner, Scheduler, State Machine, Agent Orchestrator, Policy, Approval, Recovery.
3. ENGINEERING PLANE: Code, Build, Dependency, Package, Git, Migration, Refactoring.
4. EXECUTION PLANE: Windows, Linux, Android, Web, VM, Container, Physical Device, Remote Runner.
5. ASSURANCE PLANE: Tests, Security, Red Team, Blue Team, Reliability, Fuzzing, Regression.
6. EVIDENCE PLANE: Logs, Screenshots, Video, Artifacts, Hashes, Test Results, Provenance, Evidence Bundles.
7. RELEASE PLANE: Release Gates, Packaging, Signing, SBOM, Artifact Integrity, Installation, Uninstallation, Release.

## 14. Provider Independence
External providers are adapters, not the Core architecture.

Git: GitHub, GitLab, Local Git, Self-hosted Git.
AI: Local AI, OpenAI, Anthropic, Google, other approved providers.
Build: Local, self-hosted runner, remote runner, CI provider.
UI: Playwright, Appium, native automation, other approved providers.
Security: SAST, dependency scanner, fuzzer, custom tests, Red Team agents.

GitHub must never be a single point of architectural dependency.

## 15. Network Resilience
Network is an Environment State with modes: direct, vpn, proxy, restricted, offline. Fallback is policy-controlled. Approved fallback may be Direct -> VPN -> Proxy -> Alternative Provider -> Offline. Network failure must not destroy state.

## 16. Language / Toolchain Independence
Forge is not Python-first or Kotlin-first.
Python: uv/pip/pytest.
Go: go/go test/go build/go vet.
Rust: cargo/rustc/clippy.
Java/Kotlin: Gradle/Maven/Android SDK.
C#: dotnet/MSBuild.
C/C++: CMake/MSVC/Ninja.
JavaScript/TypeScript: npm/pnpm/yarn/Playwright.

Language is an implementation choice, not the Product Contract.

## 17. Project Discovery
Before modification discover language, framework, build system, package manager, test framework, runtime, entry points, database, UI, external services, deployment model, CI and Manifest.

## 18. Target-Native Execution
If the Manifest requires Windows 11 x64, validate in Windows 11 x64 or a valid equivalent execution environment. Same principle for Android, Linux, Web and other targets. Build -> Install -> Run -> Test -> Verify.

## 19. Environment as Requirement
Environment is part of the contract. Record OS, SDK, compiler, runtime, dependencies, environment variables, policies, drivers and build tools. Detect drift.

## 20. Golden Environment
Golden Environment -> Hash -> Actual Environment -> Compare -> Drift Detection.

## 21. Reproducible Build Identity
Source Hash + Manifest Hash + Environment Hash + Dependency Lock + Build Recipe = Artifact Identity.

## 22. Autonomous Engineering Loop
Plan -> Implement -> Build -> Install -> Run -> Test -> UI Test -> Security -> Red Team -> Blue Team -> Evidence -> Independent Verification.

On failure:
Diagnose -> Research -> Strategy -> Sandbox -> Patch -> Build -> Test -> Regression -> Repeat.

## 23. Failure Knowledge Graph
Failure -> Cause -> Strategy -> Patch -> Experiment -> Result.
Similar future failures should reuse appropriate previous knowledge.

## 24. Strategy Learning
Track Successful, Failed, Partially Successful, Unsafe, Provider-specific and Environment-specific strategies. Knowledge must be exportable and auditable.

## 25. Sandbox
Unknown/high-risk patches should be tested in controlled environments before final application:
Candidate Fix -> Sandbox -> Build -> Test -> Security -> Regression -> Result.

## 26. Checkpoint / Rollback
Support Git branches/worktrees, snapshots, VM snapshots and artifact checkpoints. Failure path: Checkpoint -> Patch -> Build -> Test -> FAIL -> Rollback.

## 27. Change Impact Engine
User Request -> Impact Analysis -> Affected Requirements -> Components -> Files -> Tests -> Security Impact -> Migration Impact.

## 28. Regression Firewall
Every new feature must create/update regression coverage for existing API, DB, UI, Auth, Packaging and other affected capabilities.

## 29. Migration Intelligence
For migrations such as Python -> Go, analyze boundary, API contract, data compatibility, performance, security, build matrix, migration plan, parallel validation, cutover and rollback.

## 30. Product Intelligence / Similar Product Analysis
When the user asks to improve an existing product, Forge may perform evidence-backed external product and engineering intelligence.

Scope:
External Product Discovery -> Comparison Scope -> Evidence Collection -> Capability Extraction -> Workflow Pattern Analysis -> UX Pattern Analysis -> Architecture Pattern Analysis where allowed -> Current Product Comparison -> Gap Analysis -> Improvement Candidates -> Change Impact Analysis -> Approval -> Implementation -> Build -> Validation -> Regression -> Independent Verification.

Required outputs:
- Product Comparison
- Capability Matrix
- Pattern Catalog
- Gap Analysis
- Improvement Candidates
- Evidence Graph
- Impact Analysis

Rules:
1. External observations are evidence-backed observations, not automatic requirements.
2. Forge must preserve provenance for each external observation.
3. Similarity does not establish correctness, quality, legality, security, or suitability.
4. Forge must distinguish documented fact, observed behavior, inference and recommendation.
5. Forge may borrow patterns and concepts but must not silently copy proprietary implementation or bypass access controls.
6. No external comparison may silently change the Product Contract.
7. Any proposed requirement or contract change requires explicit approval and a new Manifest version.
8. Improvement candidates must be traceable to the user request, evidence, gap, impact analysis and resulting change.
9. If external research is unavailable, the capability may continue with available local/project evidence and must record the limitation as UNKNOWN where applicable.
10. Product Intelligence itself is subject to the same Evidence, Security, Red Team, Blue Team, Regression and Independent Verification gates.

## 31. Red Team
Only in authorized and controlled environments. Cover malformed inputs, fuzzing, authentication/authorization abuse, replay, races, resource exhaustion, state manipulation, workflow abuse, tampering, UI abuse and security regression.

## 32. Blue Team
Validate security, reliability, integrity, authentication, authorization, secrets, dependencies, logging, recovery, configuration and supply chain.

## 33. Evidence System
Every gate requires evidence such as test-result JSON, screenshots, runtime logs, video, build hash, environment record and evidence hash. Evidence should contain timestamp, source, environment, build/test identity, provenance and integrity hash.

## 34. Evidence Graph
Requirement -> Test -> Execution -> Evidence -> Verification -> Release.

For Product Intelligence:
User Request -> Research Scope -> Source -> Observation -> Evidence -> Comparison -> Gap -> Candidate -> Impact -> Approval -> Change -> Test -> Verification.

## 35. Approval Ledger
Manifest v1.0 -> Change Request -> Product Intelligence capability expansion -> Diff -> User Approved -> Manifest v1.1. Ledger must be tamper-evident.

## 36. Autonomy Levels
Level 0: Analysis Only.
Level 1: Propose Changes.
Level 2: Automatic Code Changes.
Level 3: Automatic Build/Test/Repair.
Level 4: Full Autonomous Engineering.
Level 5: Autonomous Engineering + Release.

Agents must not exceed the configured maximum autonomy level.

## 37. Human Override
Support PAUSE, INSPECT, APPROVE, DENY, ROLLBACK, CHANGE PROVIDER, CHANGE STRATEGY and RESUME according to policy.

## 38. Resource Policy
No artificial repair iteration cap. Resource controls may include CPU, RAM, disk, wall time, API cost, network and human approval. Resource exhaustion should result in PAUSED unless a real failure occurred.

## 39. Resume Capability
Support recovery after restart, crash, network failure, VPN disconnect/reconnect, AI provider failure, Git provider failure, build failure and machine restart:
Interrupted -> Recover State -> Validate Integrity -> Resume.

## 40. Self-Verification of Forge
Forge itself must be tested for crashes, provider failure, VPN disconnect/reconnect, GitHub unavailability, AI provider unavailability, build failure, low disk, corrupted projects, incomplete Manifest, recovery, resume, rollback, environment drift and evidence tampering.

## 41. Release Definition
RELEASE_READY requires actual verification of Requirements, Build, Install, Clean Run, Functional Tests, UI/Workflow Tests, Security, Red Team, Blue Team, Regression, Evidence, Independent Verification, Packaging, Artifact Integrity and Release Policy.

If a critical gate is open: RELEASE BLOCKED.

## 42. Truth Model
UNKNOWN -> CLAIMED -> OBSERVED -> TESTED -> VERIFIED -> PASSED -> RELEASED.

“AI says PASS” is only CLAIMED until independently tested and verified.

## 43. Security / Isolation
Untrusted code should use appropriate sandbox/VM/container/restricted-user/network/filesystem/secret isolation controls. Imported projects must not execute with unrestricted access to the user's primary environment.

## 44. Secret Isolation
Agent/project access to secrets must be explicit, scoped, auditable, revocable and time-bound.

## 45. Provider Health
Track availability, latency, failure rate, capabilities, network requirements, authentication state, cost and trust policy. Provider failure should support policy-controlled failover.

## 46. Offline Capability
When offline, continue local build, local tests, local static analysis, local evidence, local knowledge, local Git and local recovery where possible. Internet-dependent work must be explicit.

## 47. Product DNA
Every product retains Intent, Manifest, Manifest History, Architecture, Components, Dependencies, Providers, Environments, Known Failures, Successful Strategies, Security Rules, Tests, Decisions, Evidence and Release History.

## 48. Anti-Lock-In
Users must be able to export Manifest, Product DNA, Evidence, Failure Knowledge, Decisions and Release History.

## 49. Core Non-Negotiable Requirements
Build New; Repair Imported; Evolve Existing; Product Contract; Manifest Builder; Intent Preservation; Independent Verification; Evidence-First Engineering; Autonomous Repair; No Artificial Iteration Limit; Resource-Based Pause; Persistent Project Memory; Product DNA; Portable Knowledge; Internet Research; External Product Intelligence; Similar Product Analysis; Capability Extraction; Pattern Analysis; Evidence-Backed Comparison; Gap Analysis; Improvement Candidate Generation; Approval Before Contract Change; AI Provider Fallback; Provider Independence; Network/VPN Resilience; Offline Continuation; Hardware/Environment Diagnosis; Target-Native Execution; Multi-Language Toolchains; Failure Knowledge Graph; Sandbox; Checkpoint/Rollback; Change Impact Analysis; Regression Firewall; Red Team; Blue Team; Evidence Graph; Approval Ledger; Release Gates; Self-Verification; Human Override; Security Isolation; Reproducible Build Identity.

## 50. Forbidden Success Conditions
Never declare success merely because code was generated, AI said PASS, build started, tests were only written, some tests passed, a previous developer/AI claimed PASS, an iteration limit was reached, resources were exhausted, the Manifest was weakened, a requirement/test/target was removed, or a security gate was disabled.

## 51. BLOCKED State
When authorized resolution paths are exhausted: BLOCKED.

Blocked Report must include root cause, evidence, attempts, strategies tried, providers/tools tried, environment, network state, hardware findings, remaining options, required human action and resume point.

Temporary resource exhaustion is PAUSED, not BLOCKED.

## 52. UI
Dashboard should expose Product Health, Current Cycle, Requirements, Environment, Build, Test, Runtime, Current Failure, Agent Activity, Evidence Timeline, Red Team, Blue Team, Product Intelligence, Release Gates, Git Diff, Approvals and Requirement Lineage. UI should be purpose-built for Forge, not a copy of another product.

## 53. Final Engineering Principles
1. Forge must build, execute, test, attack, defend, collect evidence, independently verify, repair and release — not merely claim success.
2. Project Knowledge belongs to the Project, not to a chat, session, model or AI provider.
3. AI is a replaceable tool/provider. Product Contract, Evidence, Verification and Product DNA are authoritative.
4. A real blocker triggers diagnosis and resolution attempts before stopping.
5. A hardware blocker results in evidence-backed diagnosis, workaround or required hardware/environment change, and a resumable recovery path where possible.
6. External product intelligence informs improvement analysis but never silently changes the contract.

## 54. Definition of Done
RELEASE_READY only when all required gates are verified:
Product Intent Defined; Manifest Approved; Requirements Traceable; Architecture Known; Target Environment Defined; Dependencies Resolved; Build Successful; Installation Verified; Clean Runtime Verified; Functional Requirements Verified; UI/Workflow Verified; Security Verified; Red Team Completed; Blue Team Completed; Regression Completed; Evidence Collected; Evidence Integrity Verified; Independent Verification Completed; Packaging Verified; Artifact Integrity Verified; Release Gates Passed.

Otherwise: NOT RELEASE READY.

## 55. Final Contract Rule
No component, agent, provider, AI model, developer, repair strategy or automation process may silently change the approved Contract to obtain PASS.

Contract genuinely impossible under current conditions: BLOCKED.
Resources temporarily unavailable: PAUSED.
Implementation/testing genuinely fails: FAIL.
Evidence insufficient: UNKNOWN.
Only real evidence plus valid independent verification may produce PASS.

---
END OF SOFTWARE FORGE MASTER PRODUCT MANIFEST v1.1
