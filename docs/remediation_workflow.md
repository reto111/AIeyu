# Remediation Workflow Prototype

> 本文档记录批改后生成中文复习建议和巩固练习包的第一版流程。
> 当前是规则版原型，后续会接入大模型，生成更像私人俄语老师的详细讲解。

## 1. 脚本位置

```text
scripts/generate_remediation_pack.py
```

## 2. 输入

输入是批改报告 JSON，例如：

```text
data\processed\reports\tem8_quiz_20260817_sample_report_persisted.json
```

报告来自：

```text
scripts\grade_quiz.py
```

## 3. 生成复习包

运行：

```text
.venv\Scripts\python.exe scripts\generate_remediation_pack.py --report data\processed\reports\tem8_quiz_20260817_sample_report_persisted.json --per-weakness 3 --seed 20260817
```

默认输出：

```text
data\processed\remediation\
```

## 4. 输出内容

复习包包含：

- 本次测试总题数
- 答对题数
- 正确率
- 中文总评
- 每个薄弱知识点的中文建议
- 对应巩固练习题
- 每道巩固题的来源标签、选项和答案
- 阅读题的文章内容

## 5. 当前验证结果

已基于一次 10 题测试报告生成复习包：

- 薄弱方向：3 个
- 每个薄弱方向：3 道巩固练习
- 已验证中文建议、来源标签、选项、答案和阅读文章关联可输出

测试薄弱方向：

- 俄罗斯文学
- 俄罗斯国情
- 阅读理解

## 6. 后续升级方向

当前建议是规则版，只能说明“哪里薄弱”和“做哪些题巩固”。

后续需要接入大模型，生成更像私人老师的内容：

- 每道错题中文讲解
- 为什么正确答案对
- 为什么其他选项错
- 阅读题原文定位
- 知识点复习路径
- 同类题练习建议
- 支持学生继续追问
