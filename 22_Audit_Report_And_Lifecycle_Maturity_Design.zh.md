# 22 审核报告与生命周期成熟度设计

## 1. 目的

本文定义 PQRETS 的审核报告模型，以及用于生成报告视图的生命周期成熟度模型。

这里的审核报告不是一次单独的 Gate 执行记录，而是项目在某一个时间点的项目级审核快照。

```text
审核报告
= 项目 + 快照时间 + 当前 Gate + 最新已复核评估数据 + 当前风险 + 生命周期成熟度
```

Dashboard 是风险展示和关注提示机制。它不维护审批结论、管理层最终决定或决策记录。

本设计扩展了 `20_Gate_Assessment_Design.md` 中的 Gate Assessment 模型，以及 `21_AI_Agent_Integration_Spec.md` 中的 AI Agent 工作流。

参考输入：

- `input/qualityGateDefinition.drawio.png`：用于 QG0-QG5 Gate 进展，以及 QM/FuSA/CS 的 Gate 检查结构。
- `input/aspice_process_maturity.png`：用于过程域成熟度条形图的视觉参考。
- `image/AGENTS/1780380843105.png`：用于 ISO/PAS 8800 AI Safety 生命周期结构参考。
- ISO 官方公开页面：
  - ISO 26262 overview: https://www.iso.org/publication/PUB200262.html
  - ISO/SAE 21434: https://www.iso.org/standard/70918.html
  - ISO/PAS 8800: https://www.iso.org/standard/83303.html

---

## 2. 报告视图

审核报告应包含一个快照区，以及三个固定分析视图。

```text
0. Audit Snapshot
1. Quality Gate Maturity
2. Project Risk Posture
3. Lifecycle & Process Maturity
```

### 2.1 Audit Snapshot

Audit Snapshot 用于汇总：

- 项目信息
- 产品线和质量方面
- 快照日期/时间
- 当前 Gate
- 总体准备度
- Recommended Attention Level
- Product Risk
- Process Maturity Risk
- Gate Readiness and Gate Progression Signal
- Risk Confidence
- 官方成熟度得分
- 草稿成熟度得分
- 开放风险汇总
- 待人工确认项数量

示例：

| 字段 | 示例值 |
| --- | --- |
| 项目 | ADAS L2 Camera Fusion ECU |
| 产品线 | ADAS L2/L2+ |
| 快照时间 | 2026-06-02 10:00 JST |
| 当前 Gate | QG2 System Architecture Baseline |
| 启用质量方面 | QM, FuSA, CS, SOTIF, AI Safety |
| Recommended attention | At Risk |
| Product risk | Medium |
| Process maturity risk | High |
| Gate progression signal | Conditional |
| Risk confidence | Low |
| 官方集成得分 | 45% Insufficient |
| 草稿集成得分 | 69% In progress |
| 评估覆盖率 | 60% |
| 待人工确认 | 18 个 Activity x Gate 结果 |
| 当前 Gate 影响 | 3 个阻塞缺口，5 个条件性风险 |

项目在草稿状态下可能看起来更成熟，因为 AI 或系统已经给出了一些结果；但在这些评估结果被人工确认前，官方报告仍然保持较低分数。

### 2.1.1 Executive Dashboard Risk Signals

Audit Snapshot 应展示五个管理层风险信号：

```text
Recommended Attention Level
Product Risk
Process Maturity Risk
Gate Readiness
Risk Confidence
```

这些信号用于风险关注和优先级判断，不是审批决定。

Dashboard 不应保存：

- 管理层最终决定
- 审批流程状态
- 管理决策记录
- 残余风险接受签名

如果需要审批或残余风险接受，dashboard 可以链接到外部流程或记录，但不负责维护该流程。

### 2.1.2 Recommended Attention Level

Recommended Attention Level 是 dashboard 级别的汇总信号，用于表示当前项目需要多少管理层关注。

| Level | 含义 |
| --- | --- |
| Normal | 当前没有明显风险信号 |
| Watch | 存在轻微风险或覆盖率不足，需要关注 |
| At Risk | 存在明确风险，可能影响当前 Gate 或后续交付 |
| Critical | 存在严重风险、P0 blocker 或 critical unknown |
| Escalation Needed | 风险、资源或责任问题超出项目团队控制范围 |

Recommended Attention Level 由以下维度共同驱动：

```text
Product Risk
Process Maturity Risk
Gate Readiness
Risk Confidence
```

示例规则：

| 条件 | Recommended Attention Level |
| --- | --- |
| 无明显风险，coverage 达标，Gate ready | Normal |
| 轻微覆盖率不足或中等风险 | Watch |
| Gate readiness 不足，或 Product Risk 为 High | At Risk |
| 存在 P0 blocker、P0 Fail 或 critical unknown | Critical |
| 跨团队资源、责任或授权问题被阻塞 | Escalation Needed |

### 2.1.3 Product Risk

Product Risk 描述当前产品本身的风险暴露。它独立于过程是否看起来成熟。

| Level | 含义 |
| --- | --- |
| Low | 当前没有明显产品风险 |
| Medium | 存在产品风险，但已被控制或边界清楚 |
| High | 产品风险可能影响 Gate readiness 或发布 |
| Critical | 产品风险在采取行动前不可接受 |
| Unknown | 基于当前数据无法判断产品风险 |

Product Risk 应考虑 FuSA、CS、SOTIF、AI Safety、QM 风险、证据缺口、失败检查项和未解决残余风险。

### 2.1.4 Process Maturity Risk

Process Maturity Risk 描述由生命周期活动不成熟、证据薄弱、评审薄弱或过程执行不完整导致的风险。

| Level | 含义 |
| --- | --- |
| Low | 生命周期活动对当前 Gate 来说足够成熟 |
| Medium | 存在一些过程缺口，但可控 |
| High | 过程缺口可能导致风险结论不可靠 |
| Critical | 存在 P0 过程阻塞项或关键生命周期活动失败 |
| Unknown | 基于当前评估数据无法判断过程成熟度 |

Product Risk 和 Process Maturity Risk 必须分开展示。产品风险低但过程成熟度弱时，可能说明风险判断本身并不可信。

### 2.1.5 Gate Readiness 与 Gate Progression Signal

Gate Readiness 描述当前 Gate 是否具备足够的官方成熟度、证据和 P0 状态来支持推进。

Gate Readiness 应包含：

- Current Gate Official maturity score
- Current Gate P0 status
- Current Gate blocking gaps
- Gate Progression Signal

Gate Progression Signal 保留 Go/No-Go 的含义，但不成为审批决定。

| Signal | 含义 |
| --- | --- |
| Ready | 当前 Gate 看起来具备推进条件 |
| Conditional | 可以考虑推进，但仍存在条件性风险或覆盖率缺口 |
| Blocked | 当前 Gate 被 P0 Fail、关键风险或关键证据缺口阻塞 |
| Unknown | 数据不足，无法判断 Gate 推进状态 |

示例规则：

| 条件 | Gate Progression Signal |
| --- | --- |
| Current Gate Official maturity >= 70%，无 P0 Fail，Official coverage >= 80% | Ready |
| 当前 Gate 接近阈值，或仍有条件性风险 | Conditional |
| 存在 P0 Fail、关键证据缺口，或当前 Gate maturity 明显低于阈值 | Blocked |
| 缺少必要评估数据 | Unknown |

### 2.1.6 Risk Confidence

Risk Confidence 描述 dashboard 风险判断本身有多可信。

它不同于 Product Risk 或 Process Maturity Risk。

```text
Product Risk = 产品本身看起来有多大风险
Process Maturity Risk = 过程成熟度看起来有多大风险
Risk Confidence = 上述判断有多可信
```

Risk Confidence 应由以下因素计算：

- Evidence coverage
- Trace coverage
- Official assessment coverage
- Review freshness
- Unknown 或 unassessed critical item ratio

阈值：

| 输入 | 基准阈值 |
| --- | ---: |
| Evidence coverage | >=70% |
| Trace coverage | >=70% |
| Official assessment coverage | >=80% |

Risk Confidence 分档：

| Level | 含义 |
| --- | --- |
| High | 证据、trace、official coverage 都较强，且无 critical unknown |
| Medium | 达到基准阈值，剩余 unknown 可控 |
| Low | 一个或多个基准阈值未达到，或存在 critical unknown |
| Unknown | 数据不足，无法判断风险结论可信度 |

Risk Confidence 必须影响 Recommended Attention Level：

| Risk Confidence | 对 Recommended Attention Level 的影响 |
| --- | --- |
| High | 若其他风险较低，可以支持 Normal 或 Watch |
| Medium | 根据其他风险，可支持 Watch 或 At Risk |
| Low | 即使 Product Risk 看起来是 Low，也不能支持 Normal |
| Unknown | 根据缺失数据严重程度，应提升到 At Risk 或 Critical |

当 Risk Confidence 为 Low 或 Unknown 时，dashboard 必须显示原因分解。

示例：

```text
Risk Confidence: Low
Primary reason: Official assessment coverage below threshold

Breakdown:
- Evidence coverage: 58%
- Trace coverage: 64%
- Official assessment coverage: 42%
- Review freshness: 71%
- Critical unknown items: 7
```

### 2.2 Quality Gate Maturity

Quality Gate Maturity 是以 Gate 为中心的视图。

它回答的问题是：

```text
当前项目在 QG0-QG5 各个 Gate 上，按质量方面和质量属性看，成熟度如何？
```

它按如下维度聚合 Activity Gate Results：

```text
Gate -> Quality Aspect -> Quality Characteristic/Subcharacteristic
```

该视图应覆盖五个质量方面：

```text
QM
FuSA
CS
SOTIF
AI Safety
```

示例：

| Gate | QM | FuSA | CS | SOTIF | AI Safety |
| --- | ---: | ---: | ---: | ---: | ---: |
| QG0 | 85% | 75% | 70% | 60% | 55% |
| QG1 | 78% | 50% | 62% | 58% | 46% |
| QG2 | 72% | 50% | 55% | 52% | 44% |

同一组 Activity x Gate Results 也可以按 Quality Characteristic/Subcharacteristic 分组，用于查看更细的质量属性成熟度。

### 2.3 Project Risk Posture

Project Risk Posture 是以项目风险为中心的视图。

它回答的问题是：

```text
在当前快照时间点，项目整体风险状态如何？
```

该视图应展示：

- 开放风险总数
- 风险严重度分布
- 按 Quality Aspect 的风险分布
- 按 Quality Characteristic/Subcharacteristic 的风险分布
- 证据缺口
- Action item 状态
- Current Gate Impact，即当前 Gate 被哪些风险或证据缺口阻塞或条件性影响

默认范围是所有开放项目风险。当前 Gate 影响需要单独高亮。

示例：

| 风险视图 | 示例值 |
| --- | --- |
| 开放风险 | 18 |
| 高风险 | 5 |
| 当前 Gate 阻塞项 | 3 |
| 最大风险质量方面 | FuSA |
| 最大证据缺口 | Safety analysis and SOTIF scenarios |

### 2.4 Lifecycle & Process Maturity

Lifecycle & Process Maturity 是以框架和活动为中心的视图。

它回答的问题是：

```text
项目在 QM、FuSA、CS、SOTIF、AI Safety 各生命周期活动上的成熟度如何？
```

它按如下维度聚合 Activity Gate Results：

```text
Framework -> Lifecycle Phase -> Activity -> Gate progression
```

该视图可以采用类似 ASPICE 过程域成熟度条形图的视觉形式，但得分不能表述为正式 ASPICE capability level。

示例：

| Framework | Score | Main Blocker |
| --- | ---: | --- |
| QM | 78% | Architecture review not accepted |
| FuSA | 50% | P0 FSC below Evidence complete |
| CS | 55% | TARA treatment rationale missing |
| SOTIF | 52% | Scenario coverage incomplete |
| AI Safety | 44% | AI safety argument not evaluated |

---

## 3. 生命周期框架库

PQRETS 应提供内置生命周期活动库。该活动库需要按项目进行适用性裁剪，类似 Project Quality Scope tailoring。

固定的五个框架组为：

```text
QM Lifecycle
FuSA Lifecycle / ISO 26262
CS Lifecycle / ISO/SAE 21434
SOTIF Lifecycle / ISO 21448
AI Safety Lifecycle / ISO/PAS 8800
```

SOTIF 和 AI Safety 应保持为两个独立框架。它们之间可以存在显式追踪关系，但不能合并为一个框架。

### 3.1 QM Lifecycle 活动族

QM 活动覆盖通用工程质量管理，以及非安全专项的交付成熟度。

推荐活动族：

| 活动族 | 典型证据 |
| --- | --- |
| 项目范围与质量计划 | 范围定义、质量计划、职责矩阵 |
| 进度、资源与方法对齐 | 计划基线、工具/过程清单、评审记录 |
| 需求基线 | 软件/系统需求评审记录 |
| 架构基线 | 系统/软件架构评审记录 |
| 实现完成度 | 实现完成报告、代码评审记录 |
| 集成与资格测试 | 集成测试报告、资格测试报告 |
| 发布准备度 | 发布评审记录、开放问题清单 |
| 项目关闭与经验教训 | LLBP 记录、文档清理记录 |

### 3.2 FuSA Lifecycle / ISO 26262 活动族

FuSA 活动覆盖功能安全生命周期。

推荐活动族：

| 活动族 | 典型证据 |
| --- | --- |
| 安全管理计划 | Safety plan、confirmation measure plan |
| Item definition | Item definition document |
| HARA | Hazard analysis and risk assessment |
| Safety goals and ASIL | Safety goal list、ASIL rationale |
| Functional safety concept | FSC document |
| Technical safety concept | TSC document |
| System safety requirements | System safety requirement baseline |
| Hardware/software safety requirements | HW/SW safety requirement baseline |
| Safety analysis | FMEA、FTA、DFA、dependent failure analysis |
| Verification and validation | Safety verification report、validation report |
| Safety case | Safety argument and evidence package |
| Production, operation, service, decommissioning | Production control、field monitoring、service/decommissioning plan |

### 3.3 CS Lifecycle / ISO/SAE 21434 活动族

CS 活动覆盖从概念、开发、生产、运行到退役的网络安全工程活动。

推荐活动族：

| 活动族 | 典型证据 |
| --- | --- |
| Cybersecurity management planning | CS plan、role assignment |
| Cybersecurity item definition | CS item definition |
| TARA | Threat analysis and risk assessment |
| Cybersecurity goals and claims | CS goals、claims、rationale |
| Cybersecurity concept | CS concept |
| Cybersecurity requirements | CS requirement baseline |
| Product development cybersecurity activities | Design controls、implementation evidence |
| Cybersecurity verification and validation | Pen test report、vulnerability test report、review records |
| Production cybersecurity controls | Production security control evidence |
| Operations and monitoring | Monitoring plan、vulnerability monitoring records |
| Incident response and remediation | Incident response plan、remediation records |
| Decommissioning | Decommissioning security plan |
| Cybersecurity case | CS case or assurance argument |

### 3.4 SOTIF Lifecycle / ISO 21448 活动族

SOTIF 活动必须被显式包含。

推荐活动族：

| 活动族 | 典型证据 |
| --- | --- |
| Intended functionality definition | Function definition、assumptions |
| ODD and use-case definition | ODD document、use-case list |
| Hazard identification for intended functionality | SOTIF hazard analysis |
| Triggering condition analysis | Triggering condition catalogue |
| Known unsafe scenario analysis | Known scenario analysis |
| Unknown unsafe scenario discovery | Exploration strategy、field data analysis |
| Scenario coverage | Scenario catalogue、coverage report |
| Verification and validation | Simulation、proving ground、road test reports |
| Residual risk evaluation | Residual risk rationale |
| Field monitoring and update loop | Monitoring plan、update records |
| SOTIF argument and evidence | SOTIF assurance argument |

### 3.5 AI Safety Lifecycle / ISO/PAS 8800 活动族

AI Safety 活动应遵循 `image/AGENTS/1780380843105.png` 中展示的 ISO/PAS 8800 生命周期概念。

推荐活动族：

| 活动族 | 典型证据 |
| --- | --- |
| AI safety requirements allocation | 分配到 AI system 的 AI safety requirements |
| AI system definition | AI element/system definition |
| Data requirements | Data requirements、data acceptance criteria |
| Dataset definition | Dataset specification |
| Data collection | Collection plan、source record |
| Data labelling and annotation | Labelling guideline、annotation quality record |
| Data quality and completeness | Data quality report、completeness analysis |
| Training/validation/test split control | Split strategy、leakage check |
| Model training evidence | Training configuration and result record |
| Model verification | Model verification report |
| Model validation | Model validation report |
| ODD and scenario coverage for AI behaviour | Scenario coverage report |
| Robustness and generalisation evidence | Robustness tests、stress tests |
| AI safety argument | AI safety argument package |
| Evaluation of safety argument | Safety argument evaluation record |
| Operation and monitoring | Runtime monitoring and assurance maintenance records |

AI Safety 可能依赖 SOTIF 输出，例如 ODD、triggering conditions、scenario coverage、residual risk。该依赖关系应可追踪，但两个框架仍保持独立。

AI Safety 与 SOTIF 关联示例：

| 字段 | 示例值 |
| --- | --- |
| Framework | AI Safety Lifecycle / ISO/PAS 8800 |
| Lifecycle activity | Evaluation of safety argument |
| Gate | QG4 Validation Complete |
| Expected maturity | 4 Deliverable accepted |
| Required evidence | AI safety argument、model validation report、scenario coverage report、runtime monitoring plan |
| Dependency link | SOTIF ODD definition、SOTIF scenario coverage、SOTIF residual risk evaluation |

该关联用于从 AI Safety drill-down 到 SOTIF 证据，但不合并两个框架的成熟度得分。

---

## 4. Project Lifecycle Scope

内置生命周期活动库需要按项目进行裁剪。

每个 Activity Definition 都应有项目适用性状态：

```text
Applicable
Partially applicable
Not applicable
Deferred
Covered by platform
Covered by supplier
Out of project scope
```

当状态不是 `Applicable` 时，必须填写适用性理由。

默认成熟度计算只包含 applicable、partially applicable、deferred 活动。被排除的活动仍应在裁剪 UI 中可查看和复核。

---

## 5. 评估最小单元：Activity x Gate

最小评估单元是：

```text
Lifecycle Activity x Quality Gate
```

这是必须的，因为同一个活动在 QG0-QG5 的期望成熟度不同。

示例：

| Activity | QG0 | QG1 | QG2 | QG3 | QG4 | QG5 |
| --- | --- | --- | --- | --- | --- | --- |
| HARA | Planned | Initial HARA complete | Updated after design change | Assumptions verified | Accepted in safety case | Lessons learned captured |

### 5.1 Definition Object

`LifecycleActivityDefinition`：

| 字段 | 含义 |
| --- | --- |
| `id` | 稳定 UUID |
| `framework` | QM, FuSA, CS, SOTIF, AI Safety |
| `standard_context` | ISO 26262、ISO/SAE 21434、ISO 21448、ISO/PAS 8800 或 QM |
| `lifecycle_phase` | Concept、development、V&V、operation、closure 等 |
| `activity_name` | 标准活动名称 |
| `description` | 简短说明 |
| `typical_evidence` | 预期证据交付物 |
| `related_quality_aspects` | 通常为一个，也可包含依赖关系 |
| `related_subcharacteristics` | 可选 ISO 25010 链接 |

`GateLifecycleCheckDefinition`：

| 字段 | 含义 |
| --- | --- |
| `id` | 稳定 UUID |
| `gate_id` | QG0-QG5 |
| `activity_id` | LifecycleActivityDefinition 引用 |
| `expected_maturity` | 该 Gate 下的预期活动成熟度 |
| `pass_criteria` | Gate 判定标准 |
| `required_evidence` | 评估所需证据 |
| `blocking_level` | P0、P1、P2 |
| `weight` | 对框架得分的相对贡献 |

GateLifecycleCheckDefinition 示例：

| 字段 | 示例值 |
| --- | --- |
| Framework | FuSA Lifecycle / ISO 26262 |
| Lifecycle activity | HARA |
| Gate | QG1 Concept Baseline |
| Expected maturity | 3 Evidence complete |
| Required evidence | HARA report、safety goal list、ASIL rationale |
| Blocking level | P0 |
| Weight | 2 |

---

## 6. Activity Gate Result

每个适用的 Activity x Gate 结果同时保存成熟度和 Gate 判定。

| 字段 | 含义 |
| --- | --- |
| `maturity_state` | 活动/证据/交付物成熟度 |
| `judgement` | Gate 判定：Pass、Fail、Waived、Not Assessed |
| `source` | manual、ai_agent、imported |
| `ai_maturity_state` | AI 建议成熟度 |
| `ai_judgement` | AI 建议判定 |
| `ai_confidence` | AI 置信度 0.0-1.0 |
| `ai_rationale` | AI 推理理由 |
| `human_confirmed_maturity_state` | 人工确认后的评估结果 |
| `human_confirmed_judgement` | 人工确认后的 Gate 判定 |
| `assessment_reviewed_by` | 确认评估结果的人 |
| `assessment_reviewed_at` | 确认时间 |
| `evidence_ids` | 关联 Evidence Items |
| `risk_ids` | 关联 Risk Items |
| `trace_node_ids` | 可选，关联 Trace Chain 节点 |

ActivityGateResult 示例：

| 字段 | 示例值 |
| --- | --- |
| maturity_state | 3 Evidence complete |
| judgement | Fail |
| source | ai_agent |
| ai_maturity_state | 3 Evidence complete |
| ai_judgement | Fail |
| ai_confidence | 0.91 |
| ai_rationale | HARA exists, but severity/exposure/controllability rationale is incomplete |
| human_confirmed_maturity_state | 3 Evidence complete |
| human_confirmed_judgement | Fail |
| evidence_ids | HARA-001, SG-001 |
| risk_ids | R-FUSA-004 |

证据包存在，因此成熟度可以达到 3。交付物尚未被接受，因此成熟度不能达到 4。由于 P0 判定标准未满足，Gate judgement 为 Fail。

### 6.1 Maturity State

Maturity state 描述活动、证据或交付物本身的成熟度。它不表示 AI 结果是否被人工复核。

| State | 名称 | 含义 |
| --- | --- | --- |
| N/A | Not applicable | 该活动不适用于当前项目 |
| 0 | Not assessed | 尚无评估依据 |
| 1 | Insufficient | 证据缺失或明显不足 |
| 2 | In progress | 活动进行中，证据不完整 |
| 3 | Evidence complete | 必要证据包已完整到足以评估 |
| 4 | Deliverable accepted | 必要交付物/证据已经完成技术或过程评审，并被接受 |

### 6.2 Judgement

Judgement 回答 Activity x Gate 项是否满足 Gate 标准。

```text
Pass
Fail
Waived
Not Assessed
Not Applicable
```

Maturity state 和 judgement 相关，但不是同一个概念。

示例：

```text
Activity: HARA
Gate: QG1
maturity_state: 3 Evidence complete
judgement: Fail
reason: HARA exists but rating rationale is incomplete
```

### 6.3 Review 术语区分

必须区分两类 review：

| Review 类型 | 影响对象 | 含义 |
| --- | --- | --- |
| Deliverable / Evidence Review | `maturity_state` | 交付物本身已经经过技术评审、过程评审、批准或接受 |
| Assessment Result Review | 官方/草稿报告状态 | 人工确认或覆盖 AI/系统对成熟度的判断 |

`Deliverable accepted` 表示交付物被接受，不表示 AI 评估结果被接受。

---

## 7. 成熟度上限

成熟度状态受证据条件限制。

| 条件 | maturity_state 上限 |
| --- | --- |
| 没有关联证据 | 2 In progress |
| 有证据但证据不完整 | 2 In progress |
| 证据包完整 | 3 Evidence complete |
| 证据/交付物已被接受 | 4 Deliverable accepted |

对于适用的 P0 检查项：

| 条件 | 框架成熟度上限 |
| --- | --- |
| 任一 P0 judgement = Fail | Framework maturity max = 2 |
| 任一 P0 maturity_state < 3 | Framework maturity max = 2 |
| 任一 P0 maturity_state = 3 | Framework maturity max = 3 |
| 所有 P0 maturity_state >= 4 且无 P0 Fail | Framework may reach 4 |

Overall integrated maturity 应显示 P0 blocking warning。总体得分是否也被 cap，可由产品线策略决定。

P0 cap 示例：

| Activity x Gate Item | Human-confirmed maturity_state | Numeric State | P0? |
| --- | --- | ---: | --- |
| Item definition QG2 | 4 Deliverable accepted | 4 | Yes |
| HARA QG2 | 3 Evidence complete | 3 | Yes |
| FSC QG2 | 2 In progress | 2 | Yes |
| Safety analysis QG2 | 0 Not assessed | 0 | No |

```text
Raw score = (4 + 3 + 2 + 0) / (4 items * max state 4) = 56.25%
FSC QG2 is P0 and maturity_state = 2.
Framework maturity max = 2 / 4 = 50%.
Final FuSA QG2 score = min(56.25%, 50%) = 50% In progress.
```

---

## 8. 官方得分与草稿得分

报告应计算两个得分。

### 8.1 Official Score

Official score 只使用人工确认后的评估结果。

规则：

- 适用的 Activity x Gate 项如果没有人工确认结果，在 Official score 中按 0 Not assessed 计入。
- Not applicable 项排除。
- 单独显示 assessment coverage。

```text
Official coverage
= human-confirmed applicable items / total applicable items
```

### 8.2 Draft Score

Draft score 使用：

- 人工确认结果，满权重
- 尚未人工确认的 AI 建议结果，按置信度加权

AI 置信度加权：

| AI confidence | Draft weight |
| --- | --- |
| >= 0.80 | Full weight |
| 0.60-0.79 | Half weight |
| < 0.60 | Treated as 0 for draft score |

报告显示：

```text
Official maturity: 62% In progress
Draft maturity: 78% Review-ready
Pending human confirmation: 12 items
Assessment coverage: 68%
```

`Review-ready` 可以作为显示 band，但底层 maturity state 名称仍是 `Evidence complete`。

Official vs Draft 示例：

| Item Group | Count | Contribution Rule | Numerator |
| --- | ---: | --- | ---: |
| Human-confirmed applicable items | 6 | Full weight | 18.0 |
| AI confidence >= 0.80 | 2 | Full draft weight, states 4 and 4 | 8.0 |
| AI confidence 0.60-0.79 | 1 | Half draft weight, state 3 | 1.5 |
| AI confidence < 0.60 | 1 | Treated as 0 | 0.0 |

假设共有 10 个适用且等权重的项：

```text
Maximum numerator = 10 * 4 = 40
Official score = 18.0 / 40 = 45%
Official coverage = 6 / 10 = 60%
Draft score = (18.0 + 8.0 + 1.5) / 40 = 68.75%
```

---

## 9. 得分显示

内部计算使用 0-4 的 maturity state。

报告显示为百分比加 band。

| Percentage | Band |
| --- | --- |
| 0-24% | Not assessed / no basis |
| 25-49% | Insufficient |
| 50-69% | In progress |
| 70-89% | Evidence complete |
| 90-100% | Deliverable accepted |

Framework score：

```text
weighted average of applicable Activity x Gate maturity states within the framework
then apply P0 gating cap
then convert 0-4 to percentage
```

Integrated score：

```text
weighted average of framework scores
```

默认框架权重：

| Framework | Default Weight |
| --- | ---: |
| QM | 20% |
| FuSA | 25% |
| CS | 20% |
| SOTIF | 15% |
| AI Safety | 20% |

权重可按产品线调整。ADAS 和 AI-heavy ADAS 项目可以提高 FuSA、SOTIF、AI Safety 的权重。

---

## 10. 追踪关系

Activity x Gate Results 必须能追踪到项目证据和风险。

必要或推荐链接：

| 链接 | 要求 |
| --- | --- |
| Evidence Item | maturity_state 3 或 4 必须关联 |
| Risk Item | judgement 为 Fail 或 Conditional 时推荐关联 |
| Quality Subcharacteristic | 按质量属性报告成熟度时推荐关联 |
| Quality Goal / Requirement | 详细追踪时推荐关联 |
| Test Result | 验证证据来自测试时推荐关联 |
| Sankey Trace Node | 可选，但对 drill-down 有用 |

如果没有关联 Evidence Item，maturity_state 不得超过 2。

从任何低成熟度或失败项 drill-down 时，应显示：

- Activity 和 Gate
- Required evidence
- Linked evidence
- Missing evidence gaps
- Related risks
- Related quality aspect and subcharacteristic
- Related trace chain nodes when available

低成熟度 drill-down 示例：

| 字段 | 示例值 |
| --- | --- |
| Framework | CS Lifecycle / ISO/SAE 21434 |
| Activity | TARA |
| Gate | QG1 Concept Baseline |
| maturity_state | 2 In progress |
| judgement | Fail |
| Required evidence | TARA report、threat scenarios、treatment rationale |
| Linked evidence | TARA draft v0.3 |
| Missing evidence gap | Treatment option rationale missing |
| Related risk | R-CS-003 High |
| Related quality aspect | CS |
| Related subcharacteristic | Integrity |
| Related trace chain node | Cybersecurity requirement CSR-017 |

---

## 11. 与现有 Gate Assessment 的关系

当前 `20_Gate_Assessment_Design.md` 中的 Gate Assessment 模型是 Gate checklist 模型。

本文将该模型泛化为：

```text
assessment_gate_definitions
-> GateLifecycleCheckDefinition

assessment_check_results
-> ActivityGateResult
```

V6.2 可以保留当前 Gate 表作为第一版实现切片。后续版本应逐步迁移到 Activity x Gate definitions，使 QM、FuSA、CS、SOTIF、AI Safety 的生命周期活动都被表示出来。

---

## 12. 验收标准

该功能满足以下条件时视为完成：

1. 可以在某个快照时间为项目生成审核报告。
2. 报告包含 Audit Snapshot、Quality Gate Maturity、Project Risk Posture、Lifecycle & Process Maturity。
3. Audit Snapshot 展示 Recommended Attention Level、Product Risk、Process Maturity Risk、Gate Readiness、Risk Confidence。
4. Dashboard 不保存审批决定、管理层最终决定或决策记录。
5. Gate Readiness 包含 Gate Progression Signal：Ready、Conditional、Blocked、Unknown。
6. Risk Confidence 使用 Evidence coverage、Trace coverage、Official assessment coverage、review freshness、unknown item ratio。
7. Risk Confidence 为 Low 或 Unknown 时显示原因分解。
8. Quality Gate Maturity 展示 QG0-QG5 下 QM、FuSA、CS、SOTIF、AI Safety 的成熟度。
9. Lifecycle & Process Maturity 包含 QM、ISO 26262、ISO/SAE 21434、ISO 21448、ISO/PAS 8800 活动族。
10. SOTIF 和 AI Safety 是两个独立框架。
11. Activity x Gate 是最小评估单元。
12. Activity x Gate 同时保存 maturity_state 和 judgement。
13. Official score 只使用人工确认后的评估结果。
14. Draft score 使用人工确认结果，以及按置信度加权的 AI 建议结果。
15. 适用但未确认的项在 Official score 中按 0 计入，并体现在 coverage 中。
16. Maturity state 名称必须区分“交付物/证据被接受”和“评估结果被人工确认”。
17. 低成熟度报告项可以 drill down 到关联证据、风险和 Trace Chain 上下文。
