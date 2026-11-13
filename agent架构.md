上下文压缩：无压缩基础 → History → 智能压缩 → 自适应窗口化
# context(上下文压缩)
## 一、冻结首期开发范围
### 1.1 首期要实现
**纳入首期**

|模块|首期职责|
|----|----|
|ModelConfig|提供当前模型的上下文窗口、最大输出 Token 等限制|
|TokenCounter|统计文本、消息、工具定义的 Token|
|ContextBudgetConfig|配置安全余量|
|OutputTokenBudgetEstimator|根据任务类型估算输出预算|
|HistorySelector|按轮次窗口或 Token 预算选择近期历史|
|SummaryPolicy|首期只实现 DefaultSummaryPolicy|
|SummaryGenerator|生成文本历史摘要|
|SummaryQualityChecker|检查摘要中的关键遗漏、错误和预算|
|SummaryManager|协调摘要复用、更新、重建|
|ContextManager|统一计算预算、协调组件、组装 AgentContext|

### 1.2 明确暂缓
**首期不实现**

|暂缓项目|处理决定|
|----|-----|
|图片、音频、视频 Token 计数 |首期只支持文本、消息、工具 |
|多模态消息压缩和摘要|后续学习到相关内容再设计|
|完整多模型路由和适配框架|首期使用当前模型配置|
|独立 TokenBudgetManager	|预算协调先放在 ContextManager|
|独立 AgentContextAssembler|先由 ContextManager 组装|
|独立 SummaryRepository|暂不引入独立仓储抽象|
|复杂 revision、fingerprint、乐观锁|首期采用简单摘要覆盖范围有效性检查|
|通用 Strategy Registry|暂不抽象统一策略框架|
|多种 SummaryPolicy|首期只使用 DefaultSummaryPolicy|
|复杂 P1 恢复分级与动态预算竞争|首期只做必要恢复和预算冲突报告|
|独立 OmittedItemSelector|由 ContextManager 协调|
|独立 ToolResultCompressor|工具结果暂时随完整轮次参与摘要|
|部分轮次压缩|首期不拆分 ConversationTurn|
|并发摘要提交和复杂重试机制|后续遇到实际需求再设计|

这里需要特别说明：暂缓的是高级机制，不是已经确认的基本约束。

例如，首期虽然不实现复杂 fingerprint 体系，但仍然必须知道摘要覆盖了哪些轮次；首期虽然不实现复杂 P1 恢复调度，但仍然不能静默丢失已确认的关键约束。