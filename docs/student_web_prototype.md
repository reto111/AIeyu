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
- 随机组卷已接入题目曝光记录，优先未做题和需要回流的旧错题，降低近期做对题重复出现概率。
- 页面作答。
- 提交后自动批改。
- 显示正确率、错题和薄弱知识点。
- 批改后更新本地默认学生的题型掌握度、知识点掌握度和下一步弱项训练建议。
- 批改和 DeepSeek 深度错题讲解同步返回，页面等待二者完成后一起显示。
- 展示真题来源标签，例如 `2021 年俄语专八真题`。
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

提交批改并同步生成讲解：

```text
POST /api/grade
```

读取用户画像：

```text
GET /api/profile
```

内部调试用单独讲解接口：

```text
POST /api/explain
```

内部读取已保存 AI 讲解：

```text
GET /api/thread?id=1
```

继续追问：

```text
POST /api/followup
```

`/api/grade` 会完成批改并同步把本次错题、选项、学生答案、正确答案、来源标签和薄弱点发送到 DeepSeek。前端等待同一个响应完成后，一次性显示批改结果和讲解。追问会把该对话线程历史和学生新问题发送到 DeepSeek，前端仍保留追问前确认。

## 5. 当前验证结果

已验证：

- 首页可访问。
- `/api/status` 返回 150 道已审核题。
- `/api/quiz` 可生成练习，默认不包含阅读题，且不会把正确答案提前返回给前端。
- `/api/quiz` 已参考 `question_exposures` 做基础避重排序。
- `/api/grade` 可批改、写入数据库、同步生成深度错题讲解，并返回完整页面渲染所需数据。
- `/api/profile` 可返回题型掌握度、知识点掌握度、前三个薄弱项和下一步专项训练建议。
- `/api/explain` 保留为内部调试入口。
- DeepSeek 返回内容按结构拆分：逐题讲解显示在对应错题下方；薄弱点排序、复习方案和可追问问题显示在 AI 对话区。
- `/api/thread?id=1` 只返回 assistant 讲解消息，不把系统提示词和底层 JSON 暴露给学生端；学生端不再提供“读取讲解”按钮。

## 6. 后续升级

下一阶段建议：

- 把当前本地服务拆成正式后端 API。
- 将静态页面升级为 React 或 Next.js。
- 加入真实用户账号。
- 增加错题本和复习计划页面。
- 增加背单词、听力和新闻材料模块。
