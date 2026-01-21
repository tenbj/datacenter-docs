# ⛓️ 项目全链路执行手册：Python Skill 机制实现

> **版本**: v1.0  
> **创建日期**: 2026-01-21  
> **项目目标**: 在 Python 项目中实现类似 Antigravity Agent 的 Skill 扩展机制，使大模型调用具备模块化、可扩展的能力

---

## 1. 产物目录结构 (File System)

*项目所有产出将严格按照以下结构归档：*

```text
output_LLM/Python-Skill机制/
├── 00_context/                      # 原始输入、背景资料
│   └── 00_需求说明.md               # 用户需求描述
├── 01_planning/                     # 规划阶段产物
│   ├── 01_需求分析.md               # 结构化需求文档
│   └── 02_架构设计.md               # 系统架构方案
├── 02_execution/                    # 执行阶段产物
│   ├── 03_skill_base.py             # Skill 基类实现
│   ├── 04_skill_manager.py          # Skill 管理器实现
│   ├── 05_agent.py                  # 主代理实现
│   ├── 06_example_skill/            # 示例 Skill
│   │   ├── skill.yaml
│   │   ├── prompt.md
│   │   └── tools.py
│   └── 07_main.py                   # 入口示例
└── 03_delivery/                     # 最终交付
    ├── 08_使用说明.md               # 使用文档
    └── 09_测试报告.md               # 功能验证报告
```

---

## 2. 产物依赖流 (Artifact Flow)

> *箭头表示数据的流向：前一个文件的内容是生成后一个文件的必要条件。*

```mermaid
graph TD
    subgraph 阶段一：定义与设计
        Input[用户需求] -->|生成| Doc1(01_需求分析.md)
        Doc1 -->|作为依据| Doc2(02_架构设计.md)
    end
    
    subgraph 阶段二：核心落地
        Doc2 -->|指导| Code1(03_skill_base.py)
        Doc2 -->|指导| Code2(04_skill_manager.py)
        Code1 & Code2 -->|依赖| Code3(05_agent.py)
        Code1 -->|作为基类| Code4(06_example_skill/)
        Code3 & Code4 -->|调用| Code5(07_main.py)
    end
    
    subgraph 阶段三：整合与交付
        Code5 -->|验证| Test1(09_测试报告.md)
        Code1 & Code2 & Code3 -->|说明| Doc3(08_使用说明.md)
    end
    
    style Doc1 fill:#e1f5fe,stroke:#01579b
    style Doc2 fill:#e1f5fe,stroke:#01579b
    style Code1 fill:#fff3e0,stroke:#ff6f00
    style Code2 fill:#fff3e0,stroke:#ff6f00
    style Code3 fill:#fff3e0,stroke:#ff6f00
    style Code4 fill:#fff3e0,stroke:#ff6f00
    style Code5 fill:#fff3e0,stroke:#ff6f00
    style Doc3 fill:#c8e6c9,stroke:#2e7d32
    style Test1 fill:#c8e6c9,stroke:#2e7d32
```

---

## 3. 分步执行链 (Execution Chain)

### 🟢 阶段一：定义与设计

*此阶段建立项目的"真理来源 (Source of Truth)"。*

- [ ] **Step 1.1: 需求分析**
    - 📥 **Input (依赖)**: 用户对话描述（本次会话内容）
    - 📤 **Output (产出)**: `01_planning/01_需求分析.md`
    - 💡 **执行逻辑**: 将模糊需求转化为结构化文档，明确功能边界。
    - > **🤖 AI指令**: 请根据用户描述，生成 `01_需求分析.md`。内容包含：
      > - 核心目标：实现可扩展的 Skill 机制
      > - 功能需求：Skill 加载、路由、执行、多轮对话
      > - 非功能需求：易扩展、低耦合、配置化

- [ ] **Step 1.2: 架构设计**
    - 📥 **Input (依赖)**: `01_planning/01_需求分析.md` (必须读取)
    - 📤 **Output (产出)**: `01_planning/02_架构设计.md`
    - 💡 **执行逻辑**: **严禁脱离需求文档设计**。基于需求约束设计技术方案。
    - > **🤖 AI指令**: 请**详细阅读** `01_需求分析.md`。设计系统架构，输出为 `02_架构设计.md`。包含：
      > - 模块划分：BaseSkill / SkillManager / Agent
      > - 类图/流程图 (Mermaid)
      > - 技术选型理由（OpenAI / 其他大模型 API）

---

### 🟡 阶段二：核心落地 (代码生产)

- [ ] **Step 2.1: Skill 基类实现**
    - 📥 **Input (依赖)**: 
        - `01_planning/01_需求分析.md` (核对目标)
        - `01_planning/02_架构设计.md` (遵循设计)
    - 📤 **Output (产出)**: `02_execution/03_skill_base.py`
    - 💡 **执行逻辑**: 实现 Skill 的基类，定义标准接口。
    - > **🤖 AI指令**: 结合 `01_需求分析.md` 和 `02_架构设计.md`，编写 `03_skill_base.py`。包含：
      > - `BaseSkill` 抽象类
      > - 配置加载（skill.yaml）
      > - Prompt 加载（prompt.md）
      > - `get_tools()` 和 `execute_tool()` 抽象方法

- [ ] **Step 2.2: Skill 管理器实现**
    - 📥 **Input (依赖)**: 
        - `01_planning/02_架构设计.md` (遵循设计)
        - `02_execution/03_skill_base.py` (依赖基类)
    - 📤 **Output (产出)**: `02_execution/04_skill_manager.py`
    - 💡 **执行逻辑**: 实现 Skill 扫描、加载、路由功能。
    - > **🤖 AI指令**: 读取 `02_架构设计.md` 和 `03_skill_base.py`，编写 `04_skill_manager.py`。包含：
      > - 技能目录扫描与动态加载
      > - 关键词/语义路由匹配
      > - 技能信息汇总（用于 System Prompt 注入）

- [ ] **Step 2.3: 主代理实现**
    - 📥 **Input (依赖)**: 
        - `01_planning/02_架构设计.md`
        - `02_execution/03_skill_base.py`
        - `02_execution/04_skill_manager.py`
    - 📤 **Output (产出)**: `02_execution/05_agent.py`
    - 💡 **执行逻辑**: 整合 SkillManager，实现与大模型 API 的交互。
    - > **🤖 AI指令**: 读取架构设计和前序代码文件，编写 `05_agent.py`。包含：
      > - System Prompt 动态构建（注入 Skill 信息）
      > - Function Calling 支持
      > - 工具调用结果处理与多轮对话

- [ ] **Step 2.4: 示例 Skill 实现**
    - 📥 **Input (依赖)**: `02_execution/03_skill_base.py` (作为基类)
    - 📤 **Output (产出)**: `02_execution/06_example_skill/` 目录
    - 💡 **执行逻辑**: 提供一个完整的 Skill 示例，展示如何扩展。
    - > **🤖 AI指令**: 基于 `03_skill_base.py` 的接口规范，创建 `06_example_skill/` 目录，包含：
      > - `skill.yaml` - 技能配置
      > - `prompt.md` - 专用 Prompt
      > - `tools.py` - 继承 BaseSkill 的具体实现

- [ ] **Step 2.5: 入口示例编写**
    - 📥 **Input (依赖)**: 
        - `02_execution/05_agent.py`
        - `02_execution/06_example_skill/`
    - 📤 **Output (产出)**: `02_execution/07_main.py`
    - 💡 **执行逻辑**: 提供可直接运行的入口脚本。
    - > **🤖 AI指令**: 读取 Agent 和示例 Skill，编写 `07_main.py`。展示：
      > - 初始化 Agent
      > - 普通对话调用
      > - 触发 Skill 的调用

---

### 🔴 阶段三：整合与交付

- [ ] **Step 3.1: 使用文档编写**
    - 📥 **Input (依赖)**: 
        - `02_execution/03_skill_base.py`
        - `02_execution/04_skill_manager.py`
        - `02_execution/05_agent.py`
        - `02_execution/06_example_skill/`
    - 📤 **Output (产出)**: `03_delivery/08_使用说明.md`
    - 💡 **执行逻辑**: 撰写面向用户的使用文档。
    - > **🤖 AI指令**: 综合所有代码文件，编写 `08_使用说明.md`。包含：
      > - 快速开始指南
      > - 如何创建自定义 Skill
      > - 配置说明
      > - API 参考

- [ ] **Step 3.2: 功能验证**
    - 📥 **Input (依赖)**: `02_execution/07_main.py` + 所有核心代码
    - 📤 **Output (产出)**: `03_delivery/09_测试报告.md`
    - 💡 **执行逻辑**: 运行示例，验证功能正确性。
    - > **🤖 AI指令**: 执行 `07_main.py`，验证以下场景：
      > - Skill 加载成功
      > - 路由匹配正确
      > - 工具调用正常
      > - 输出测试报告

---

## 4. 验证计划

### 自动化测试
- 运行 `python 07_main.py`，验证控制台输出
- 检查 Skill 加载日志
- 验证 Function Calling 返回结果

### 手动验证
- 修改 `skill.yaml` 的 triggers，验证路由变化
- 添加新 Skill，验证热加载

---

## 5. 风险与注意事项

> [!WARNING]
> **API Key 安全**：示例代码中使用环境变量管理，禁止硬编码

> [!IMPORTANT]
> **依赖管理**：需要安装 `openai`, `pyyaml` 等依赖

> [!TIP]
> **扩展建议**：后续可增加语义路由（Embedding 匹配）替代关键词匹配

---

## 6. 版本记录

| 版本 | 日期       | 更新内容 |
| ---- | ---------- | -------- |
| v1.0 | 2026-01-21 | 初始版本 |
