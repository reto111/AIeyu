# Student Web Prototype

> 本文档记录 AIeyu 学生端本地网页原型。
> 当前版本用于验证学习闭环体验，不是最终商业化前端。

## 1. 当前定位

当前学生端原型只面向学生使用，不包含教师端。

已支持：

- 查看已审核题库概况。
- 按题型选择练习范围。
- 按年份选择练习范围。
- 设置题目数量。
- 随机生成俄语专八练习，默认不包含阅读题。
- 页面作答。
- 提交后自动批改。
- 显示正确率、错题和薄弱知识点。
- 勾选同意后，为本次测试生成 DeepSeek 深度错题讲解。
- 展示真题来源标签，例如 `2021 年俄语专八真题`。
- 读取已保存的 DeepSeek 中文讲解。
- 预留学生继续追问入口。

## 2. 启动方式

```text
.venv\Scripts\python.exe scripts\serve_student_app.py --port 8765
```

打开：

```text
http://127.0.0.1:8765/
```

## 3. 文件位置

本地服务：

```text
scripts\serve_student_app.py
```

前端文件：

```text
apps\student_web\static\index.html
apps\student_web\static\styles.css
apps\student_web\static\app.js
```

## 4. API

题库状态：

```text
GET /api/status
```

生成练习：

```text
POST /api/quiz
```

提交批改：

```text
POST /api/grade
```

生成本次错题讲解：

```text
POST /api/explain
```

读取 AI 讲解：

```text
GET /api/thread?id=1
```

继续追问：

```text
POST /api/followup
```

生成讲解会把本次错题、选项、学生答案、正确答案、来源标签和薄弱点发送到 DeepSeek。追问会把该对话线程历史和学生新问题发送到 DeepSeek。前端必须要求学生明确同意后才能发送。

## 5. 当前验证结果

已验证：

- 首页可访问。
- `/api/status` 返回 150 道已审核题。
- `/api/quiz` 可生成练习，默认不包含阅读题，且不会把正确答案提前返回给前端。
- `/api/grade` 可批改并写入数据库。
- `/api/explain` 在学生明确同意后，可根据本次测试生成深度错题讲解并写入 `ai_tutor_threads` / `ai_tutor_messages`。
- `/api/thread?id=1` 只返回 assistant 讲解消息，不把系统提示词和底层 JSON 暴露给学生端。

## 6. 后续升级

下一阶段建议：

- 把当前本地服务拆成正式后端 API。
- 将静态页面升级为 React 或 Next.js。
- 加入真实用户账号。
- 增加错题本和复习计划页面。
- 增加背单词、听力和新闻材料模块。
