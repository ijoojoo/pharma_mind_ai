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