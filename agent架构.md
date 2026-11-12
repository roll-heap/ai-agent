上下文压缩：无压缩基础 → History → 智能压缩 → 自适应窗口化
# context职责
1. 解析历史
调用 HistoryParser，将原始消息解析为：
```python
list[ConversationTurn]
```
Context 不自己解析消息轮次，也不重复实现 History 的逻辑。
2. 历史选择
决定哪些历史轮次需要进入本次 Agent 上下文。
例如：
- 保留最近若干轮。
- 保留与当前问题相关的历史。
- 保留必要的系统信息。
- 根据 Token 预算筛选历史。
当前阶段先不实现复杂筛选。
3. 历史压缩
当历史过长时，对历史进行裁剪、摘要或其他压缩处理。
必须遵守一个原则：
**压缩只作用于本轮构建的上下文，绝不修改 Session 中的原始历史。**
4. 构建 AgentContext
将处理后的历史与当前用户输入组合，形成 Agent 可以直接消费的上下文。



# 第二阶段：
第一步
理解你现在的 messages 到底是不是完整 Memory
        ↓
第二步
理解 Agent State 和你手动维护 messages 的区别
        ↓
第三步
实现 LangGraph 的短期记忆
        ↓
第四步
处理 Context 无限增长
        ↓
第五步
滑动窗口 / Message Trimming
        ↓
第六步
摘要记忆
        ↓
第七步
长期记忆
        ↓
第八步
用户记忆 + RAG