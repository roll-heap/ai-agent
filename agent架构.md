上下文压缩：无压缩基础 → History → 智能压缩 → 自适应窗口化
# context职责
## 已确认、待定稿、未确认的完整清单
为了后续继续设计时不再丢失决策，我把目前状态集中列出。
### A. 已确认
领域	决策
核心架构	Session、Conversation、History、Context、Agent 五层
History 调用	ContextManager 调用 HistoryTurnParser
原始历史	Session 保存完整原始历史
轮次模型	ConversationTurn 包含 messages、is_complete
轮次选择	按完整轮次，不拆消息
历史策略	Fixed Turn Window 与 Token Budget 二选一
TokenCounter	归属 Model，按模型适配
TokenCounter 接口	count_text、count_messages、count_tools
TokenCounter 注入	ContextManager 与 OutputTokenBudgetEstimator 共享实例
多模态 Token 计数	首期暂不实现
输出预算策略	OutputTokenBudgetStrategy 按 TaskType 选择
多任务输出预算	多个策略命中时取最大值
输出预算失败	全部失败时使用默认预算并降级，不中断请求
新 TaskType	必须同步增加识别和预算策略，缺失则初始化失败
摘要	原始历史的派生数据，不替代原始历史
摘要模式	支持增量更新和完整重建
摘要质量	通过检查后才能提交
摘要规则	P0/P1/P2/P3 和信息状态体系
摘要策略	SummaryPolicy 按 TaskType 扩展
多任务摘要策略	按优先级选择一套，不合并
Agent	只消费 AgentContext，负责模型调用和工具执行

### B. 已有实现或实际验证
内容	状态
Agent 初始化及工具注册	已有代码
Conversation 执行流程	已有代码
ContextManager	已有代码，已调用 HistoryTurnParser
HistoryTurnParser	已有代码并通过测试
ConversationTurn	已有设计和测试
消息保存逻辑	已通过实际运行验证
工具调用历史保存	已通过实际运行验证

注意：这里的“已确认架构”不等于所有新讨论的组件都已经编码实现。比如 SummaryManager 和 OutputTokenBudgetEstimator 的完整设计不能误认为已经写进项目。
C. 已有方向，但接口仍待定稿
- TaskClassificationResult 的最终字段。
- OutputTokenBudgetStrategy 的最终完整签名。
- TokenCounter 结构化结果模型的字段。
- HistorySelectionConfig 的最终字段。
- SummaryManager 的完整接口。
- SummaryPolicyRegistry 的注册结构。
- ConversationSummary 的最终字段。
- AgentContext 的最终完整结构。
- ContextManager 的最终构造参数和 build_context 参数。
D. 尚未确认
1. TokenBudgetManager 是否独立成组件。
2. Context 内部最终预算分配顺序。
3. 摘要与近期历史预算的具体分配规则。
4. HistorySelector 和 SummaryManager 如何传递 selected_turns、excluded_turns。
5. SummaryRepository 是否独立。
6. 摘要由谁持久化和提交。
7. turn_id、revision、source_fingerprint 的最终设计。
8. 摘要质量检查的修复与重试细节。
9. 工具结果压缩是否独立存在。
10. 图片、音频、视频的消息表示、Token 计数和压缩接口。
11. 两套 TaskType 策略是否共享通用 Registry 基础设施。

### 建议后续设计顺序
我建议按下面的顺序继续，不要再跳到单个组件的实现细节：
顺序	设计内容	目的
1	ContextManager 完整执行流程	把所有已有组件串起来
2	Token 预算管理	明确输入、固定开销、输出、摘要、近期历史的预算关系
3	HistorySelector 与 SummaryManager 协作	明确摘要覆盖范围
4	SummaryRepository	明确摘要持久化
5	AgentContext	明确最终传给 Agent 的结构
6	多模态扩展接口	为图片、音频、视频预留能力
7	各模块最终接口	再进入代码实现