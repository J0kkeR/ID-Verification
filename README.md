# ID-Verification 身份证信息校验工具

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![历史数据许可: CC0 1.0](https://img.shields.io/badge/%E5%8E%86%E5%8F%B2%E6%95%B0%E6%8D%AE%E8%AE%B8%E5%8F%AF-CC0%201.0-lightgrey)](LICENSE.areacodes)

一个基于中华人民共和国国家标准 GB 11643《公民身份号码》规则的身份证号码校验与归属地查询工具，支持 **Excel 批量校验**、**命令行单条查询** 和 **浏览器网页查询** 三种使用方式。

- 地区编码、出生日期、性别顺序码、校验码四项独立校验
- 内置民政部现行区划、历年区划（1981—2025）与乡级（乡镇街道）数据
- 数据可通过民政部接口在线更新，网页端纯本地运行、无需服务器

> **注意**：规则校验通过只能说明号码符合编码规则，不能证明证件真实或仍在有效期内。

---

## 特点

| 特点 | 说明 |
| --- | --- |
| 四项规则校验 | 地区编码、出生日期（含年龄计算）、性别（第 17 位顺序码）、末位校验码（ISO 7064:1983 MOD 11-2） |
| 三种使用方式 | Excel 批量处理（`main.py`）、命令行交互（`id_cli.py`）、离线网页（`index.html`，双击即用） |
| 乡级数据 | 县级区划下可查全部下辖乡镇街道；支持直接输入九位、十二位乡级代码反查名称 |
| 历史区划追溯 | 内置 1981—2025 年历年区划资料，历史代码自动标注“历史区域”并列出各年末版本归属 |
| 数据可更新 | 一键从民政部接口获取最新年度版数据，自动同步当前库、历史库与网页数据 |
| 跨年份快照 | 每次更新按版本年份留存完整快照（`年度数据/年份.json`），可对比历年区划变化 |
| 来源清晰 | 现行、补充、历史三类代码分级标注，许可见 `LICENSE` 系列文件 |

## 使用来源

### 代码来源

本项目基于 [ifzzh/ID-Verification](https://github.com/ifzzh/ID-Verification)（上游 README 署名作者 HaoZ-zzh，[MIT License](LICENSE)）二次开发，在其校验框架上扩展了乡级数据、历史区划、在线更新和命令行、网页界面。

**沿用上游、未作修改的文件**：

- 校验模块：`checkNum.py`（校验码）、`checkGender.py`（性别）、`checkBirthdate.py`（出生日期）
- 数据工具脚本：`genData.py`、`belong.py`、`all.py`
- `LICENSE`（MIT）

**在上游基础上修改的文件**：

| 文件 | 上游版本 | 本项目改动 |
| --- | --- | --- |
| `checkArea.py` | 仅查六位县级码的静态字典 | 扩展为支持六位/九位/十二位代码、历史归属库、年度快照与乡级索引 |
| `main.py` | 输出 9 列校验字段 | 新增第 10 列“区划记录”、第 11 列“历史备注” |
| `index.html` | 约 1.4 MB 单文件、内嵌数据 | 页面（约 22 KB）与数据（`area_data.js`）分离，新增乡级清单、历史归属与结果筛选 |
| `requirements.txt` | openpyxl | 新增 `requests`（在线更新用） |

**本项目新增**：`id_cli.py`、`update_area.py`、`build_historical_area.py`、`build_web_data.py`，以及全部数据文件（`归属地.json`、`历史归属地.json`、`历史数据源.csv`、`年度数据/`、`area_data.js`）。

与上游项目的功能对比：

| 对比项 | ifzzh/ID-Verification | 本项目 |
| --- | --- | --- |
| 四项规则校验 | 有 | 有（沿用上游模块） |
| 区划数据 | 静态文件，手动更换 | 民政部接口在线更新，按版本年留存快照 |
| 乡级（乡镇街道）数据 | 无 | 38,827 条九位代码 + 84 条十二位兼容码 |
| 历史区划（1981—2025） | 无 | 6,462 个代码、6,835 段记录，自动标注历史区域 |
| 命令行单条查询 | 无（仅 Excel 批量） | `id_cli.py` 支持身份证号与 6/9/12 位区划代码 |
| 网页界面 | 单文件内嵌数据 | 页面与数据分离，可筛选、可查乡级清单 |

### 数据来源

| 来源 | 内容 | 许可 |
| --- | --- | --- |
| [民政部行政区划代码接口](https://dmfw.mca.gov.cn/interface.html)（[发布页](https://dmfw.mca.gov.cn/XzqhVersionPublish.html)） | 现行省、地、县、乡四级区划代码，按发布页标明的版本年份获取 | 官方发布 |
| [kk-418/cn-division](https://github.com/kk-418/cn-division) 2026.0.1 | 部分补充和兼容代码 | 见 `LICENSE.cn-division` |
| [yescallop/areacodes](https://github.com/yescallop/areacodes) | 1981—2025 年历年县级及以上区划资料，原始表为 `历史数据源.csv`（SHA-256：`c371ded17c23b6e2f5b57bf0eb0c1f66bf869f34a45e34d78c53013b8a5729e8`） | CC0 1.0，见 `LICENSE.areacodes` |

### 数据规模

| 文件 | 内容 |
| --- | --- |
| `归属地.json` | 现行省、地、县、乡及兼容代码，共 42,133 条（六位 3,222、九位 38,827、十二位 84） |
| `历史归属地.json` | 历年资料与年度快照的六位记录，共 6,462 个代码、6,835 段记录 |
| `年度数据/2025.json` | 2025 年版完整快照（版本年份以民政部发布页标明的 2025 年 12 月 31 日为准） |
| `area_data.js` | 由上述数据自动生成的网页本地数据，供 `index.html` 直接使用 |

更详细的字段与版本规则见 [数据说明.md](数据说明.md)。

## 安装

要求 Python 3.x。

```bash
git clone <仓库地址>
cd ID-Verification-master
pip install -r requirements.txt
```

依赖：`openpyxl`（读写 Excel）、`requests`（在线更新数据）。

## 用法

### 方式一：Excel 批量校验（main.py）

1. 在项目目录准备 `身份证.xlsx`：第一行为表头，第一列从第二行起存放待校验的 18 位身份证号码。
2. 运行：

   ```bash
   python main.py
   ```

3. 结果写回原文件，第 2—9 列为校验字段，第 10 列“区划记录”区分现行/补充/历史代码，第 11 列“历史备注”列出旧归属的年末版本记录。

输出示例：

| 身份证号码 | 整体有效性 | 校验码 | 省份 | 城市 | 区域 | 数据来源 | 生日 | 性别 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 110101199001011245 | 有效 | OK | 北京市 | 市辖区 | 东城区 | 民政部 | 1990年1月1日 | 女 |

### 方式二：命令行单条查询（id_cli.py）

无需准备 Excel 文件，支持 18 位身份证号及 6/9/12 位区划代码：

```bash
python id_cli.py 110101199001011245   # 身份证号：四项校验 + 归属地 + 历史归属
python id_cli.py 110101               # 六位县级码：列出下辖全部乡镇街道
python id_cli.py 110101001            # 九位乡级码：显示对应乡镇街道名称
```

省略参数时会提示输入。输入六位代码列出的乡镇街道清单覆盖该县级区划，**不能**凭身份证号确定持证人的具体乡镇街道；历史区域缺少乡级资料时会显示“无可用数据”。

### 方式三：网页界面（index.html）

1. 保持 `index.html` 与 `area_data.js` 在同一目录，直接用浏览器打开 `index.html`，无需联网和服务器。
2. 输入或粘贴身份证号或 6/9/12 位区划代码，多条查询可换行或用逗号分隔。
3. 点击“开始校验”，可查看归属地、下辖乡镇街道清单、数据版本及历史归属；清单可展开，结果可按通过、历史区域、异常筛选。
4. 手动修改本地 JSON 后，运行 `python build_web_data.py` 同步网页数据。

## 更新

### 在线更新区划数据

```bash
python update_area.py
```

程序先读取民政部发布页标明的数据截止年份，再按接口文档获取对应年度版，完成后同步替换 `归属地.json`、`历史归属地.json`、`area_data.js`，完整结果保存为 `年度数据/年份.json`（同一版本年重复更新时替换该年快照）。

| 参数 | 作用 |
| --- | --- |
| `--resume` | 完整更新涉及数千次请求，中断后复用本次已获取的数据继续 |
| `--county-only` | 只更新省、地、县三级，沿用原有乡级数据（速度快） |
| `--year 2025` | 指定版本年份，不读取发布页 |
| `--dry-run` | 只检查结果，不替换任何文件 |
| `--insecure` | 跳过证书校验，仅在已信任的代理环境中使用 |

### 手动重建数据文件

更新历史 CSV 或本地 JSON 后：

```bash
python build_historical_area.py   # 由 历史数据源.csv + 年度快照重新生成 历史归属地.json
python build_web_data.py          # 由当前库 + 历史库重新生成网页数据 area_data.js
```

## 项目结构

```
├── main.py                  # Excel 批量校验入口
├── id_cli.py                # 命令行单条查询入口
├── index.html               # 网页界面（配合 area_data.js 离线使用）
├── checkArea.py             # 地区编码校验（六位/九位/十二位）
├── checkBirthdate.py        # 出生日期校验
├── checkGender.py           # 性别顺序码校验
├── checkNum.py              # 校验码校验（MOD 11-2）
├── update_area.py           # 民政部接口在线更新
├── build_historical_area.py # 历史库生成
├── build_web_data.py        # 网页数据生成
├── 归属地.json               # 现行区划数据库
├── 历史归属地.json           # 历史区划数据库
├── 历史数据源.csv            # 历年区划原始资料
├── 年度数据/                 # 按版本年份留存的完整快照
├── area_data.js             # 网页本地数据
└── 数据说明.md               # 数据来源与版本规则详细说明
```

## 许可证

本项目在 [MIT License](LICENSE) 下发布（沿用上游项目 ifzzh/ID-Verification 的许可）；第三方数据许可分别见 `LICENSE.cn-division` 与 `LICENSE.areacodes`。
