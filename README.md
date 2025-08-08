# PharmaMind AI - 智慧药店运营平台

**一个专为连锁药店行业设计的、深度集成AI能力的商业智能与运营优化平台。**

`PharmaMind AI` 的核心目标不是提供复杂的报表，而是通过深度整合的AI能力，将海量的业务数据转化为**看得懂的洞察、可执行的策略、可追踪的任务**，全面赋能药店在商品、库存、门店、员工和会员等所有核心运营环节的精细化管理和持续增长。

本项目是 `PharmaMind AI` 的核心后端与前端代码库，与之配套的还有一个独立的 [DataConnector](https://github.com/your-repo/dataconnector) 项目，用于实现与客户本地数据库的数据同步。

---

## 核心特性

* **AI驱动的洞察**:
    * **一键复盘**: 对当日/当周/当月的经营状况，一键生成包含数据分析、问题归因和改进建议的综合性报告。
    * **智能商品管理**: AI自动为商品打上标准品类标签、划分价格带、挖掘重点与滞销品种。
    * **智能会员管理**: AI自动为会员画像，根据消费记录为其打上疾病、消费习惯和风险标签。
    * **AI策略生成**: 基于企业自身数据，生成定制化的营销策划、品类优化、库存优化和员工培训方案。
* **全面的BI分析中心**:
    * 提供从企业全局到单个门店、单个员工的多维度数据钻取能力。
    * 通过丰富的可视化图表，直观展示销售、毛利、客流、坪效、人效等核心经营指标。
* **精细化的运营管理**:
    * 覆盖商品、门店、员工、会员等所有核心主数据的管理。
    * 专业的KPI考核中心，支持从目标设定到进度追踪，再到AI指导的全流程管理。
* **安全可扩展的多租户架构**:
    * **数据隔离**: 保证每个企业客户的数据都经过严格的物理和逻辑隔离。
    * **权限分明**: 内置了从“企业管理员”到“店员”的多层级角色权限体系，确保不同岗位的员工只能访问其权限范围内的数据。
    * **模块化设计**: 采用清晰的模块化架构，便于未来的功能扩展。

## 系统架构

`PharmaMind AI` 平台由三个核心部分组成：

1.  **后端API (`pharma_mind_ai`)**: 基于 `Python` 和 `Django` 构建，负责所有业务逻辑、数据处理、AI分析和API接口。
2.  **前端应用 (`vue-pure-admin`)**: 基于 `Vue 3`, `TypeScript` 和 `pure-admin` 模板构建的现代化单页应用，为用户提供丰富的交互体验。
3.  **数据连接器 (`DataConnector`)**: 一个独立的C# Windows服务，部署在客户本地，负责将客户的业务数据安全、稳定地同步到云端平台。

## 技术栈

* **后端**: Python, Django, Django REST Framework, djangorestframework-simplejwt, djangorestframework-api-key
* **前端**: Vue 3, Vite, TypeScript, Element-Plus, Pinia, Tailwind CSS, ECharts
* **数据库**: MySQL

## 本地开发环境部署

#### **前提条件**

* Python 3.10+
* Node.js 16+
* pnpm
* MySQL 5.7+

---
### **后端 (`pharma_mind_ai`) 部署指南**

1.  **克隆项目**:
    ```bash
    git clone [https://github.com/your-repo/pharma_mind_ai.git](https://github.com/your-repo/pharma_mind_ai.git)
    cd pharma_mind_ai
    ```

2.  **创建并激活虚拟环境**:
    ```bash
    python -m venv venv
    source venv/bin/activate  # on Windows: venv\Scripts\activate
    ```

3.  **安装依赖**:
    ```bash
    pip install -r requirements.txt
    ```

4.  **配置数据库**:
    * 在您的MySQL中创建一个新的数据库 (例如 `pharma_mind_db`)。
    * 将 `config/settings.py` 文件中的 `DATABASES` 配置，修改为您自己的数据库连接信息。

5.  **执行数据库迁移**:
    ```bash
    python manage.py makemigrations
    python manage.py migrate
    ```

6.  **创建超级管理员**:
    ```bash
    python manage.py createsuperuser
    ```

7.  **启动后端开发服务器**:
    ```bash
    python manage.py runserver 0.0.0.0:8000
    ```
    现在，您应该可以通过 `http://127.0.0.1:8000/admin/` 访问Django后台了。

---
### **前端 (`vue-pure-admin`) 部署指南**

1.  **进入前端项目目录**:
    ```bash
    cd frontend  # 假设您的Vue项目位于frontend目录下
    ```

2.  **安装依赖**:
    ```bash
    pnpm install
    ```

3.  **配置API地址**:
    * 打开 `.env.development` 文件。
    * 将 `VITE_PROXY_DOMAIN_REAL` 的值，修改为您后端API的地址 `http://127.0.0.1:8000`。

4.  **启动前端开发服务器**:
    ```bash
    pnpm dev
    ```
    现在，您应该可以通过浏览器访问 `http://localhost:8848` (或您命令行中提示的其他端口) 来查看前端应用了。

## 许可证

本项目采用 [MIT许可证](https://opensource.org/licenses/MIT)。



【PHARMA MIND AI】项目技术栈


【后端】
基础语言Python3             #虚拟隔离环境运行
前后端隔离技术
前后端对接Django

【前端】
管理工具 Node.js
前端框架 Vue
npap
构建工具 Vite
UI模板 vue-pure-admin
图表库 ECharts？

【数据库】
Mysql //后期更换为PgSQL?

【工具】
开发操作系统：Windows 10
IDE工具：Visual Studio Code 
API测试工具：Postman 
GitHub下载工具：Git
数据库管理工具 Navicat

【AI】
Google Gemini 2.5Pro    #Ultra 收费账户
智谱 GLM4.5

【网络】
V2ray          #


【组件】
Django


接下来我们来考虑如何对接客户的数据库。
1.客户的数据库有的部署在云服务器上，有的部署在私有服务器上，大部分有固定IP，可以直接通过internet连接，个别没有部署专线，不能通过数据库链接字符串链接。
2.客户的数据库类型不尽相同，有mssqlserver、oracle两种。
3.客户数据库链接的可靠性存在一定的疑问。
4.客户的ERP系统各不相同，对应的数据库结构也完全不同。
结合这些情况，请给出一个你最推荐的获取客户数据的方案。

我个人的想法：制作一个独立的数据同步软件，软件可以连接客户的数据库，根据我们的系统的需求，可以定义数据提取sql语句，获取统一的数据内容后，传输到我们的数据库。
