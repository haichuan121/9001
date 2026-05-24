# 9001 — 元修正评分系统

> 打分之后再打分，用满意度修正原始分，并识别水军干扰。

## 核心思路

传统评分系统的问题：
- 用户给出的分数不代表真实满意度
- 水军刷分会严重扭曲结果

本项目的解法：
1. **原始评分** — 用户对目标打分（0–10）
2. **满意度修正** — 用户对"自己给出的这个分数"再打一个满意度（0–1），用于加权修正原始分
3. **水军识别** — 通过行为特征检测异常评分，过滤后再参与汇总

## 项目结构

```
9001/
├── scorer/
│   ├── core.py         # 评分聚合与修正逻辑
│   ├── meta_score.py   # 满意度加权计算
│   └── bot_detect.py   # 水军识别
└── tests/
    └── test_core.py
```

## 快速开始

```bash
pip install -r requirements.txt
python -m scorer
```

## 修正公式

```
adjusted_score = raw_score * satisfaction_weight + global_mean * (1 - satisfaction_weight)
```

满意度越低，分数越向全局均值收缩，降低极端打分的影响。
