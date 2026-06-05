# PQRETS 系统启动说明书

本文说明如何在本机启动 PQRETS，并让同事通过浏览器访问。

## 1. 当前启动方式

当前推荐使用本机开发部署方式：

```text
浏览器
-> 前端 Vite dev server: http://本机IP:5174
-> 后端 FastAPI: http://localhost:9000
-> PostgreSQL database
```

同事只需要访问前端地址：

```text
http://你的电脑IP:5174
```

前端会通过本机代理访问后端 API。

## 2. 端口

| 服务 | 端口 | 说明 |
|---|---:|---|
| Frontend | 5174 | 给浏览器访问 |
| Backend | 9000 | 前端代理访问 |
| Database | Docker 内部端口 | 一般不需要同事访问 |

Windows 防火墙通常只需要放行 `5174`。

## 3. 首次准备

### 3.1 安装依赖

需要安装：

- Docker Desktop
- Node.js
- npm

### 3.2 安装前端依赖

在项目根目录执行：

```bash
cd frontend
npm install
```

如果已经安装过依赖，后续不需要每次执行。

## 4. 启动系统

### 4.1 启动数据库和后端

在项目根目录执行：

```bash
docker compose -f docker-compose.dev.yml --env-file .env.dev up -d db backend
```

检查是否启动：

```bash
docker compose -f docker-compose.dev.yml ps
```

后端地址：

```text
http://localhost:9000
```

### 4.2 启动前端

打开另一个终端，在项目根目录执行：

```bash
cd frontend
npm run dev
```

当前 `npm run dev` 已配置为：

```json
"dev": "vite --host 0.0.0.0"
```

因此启动后会显示类似：

```text
Local:   http://localhost:5174/
Network: http://172.xx.xx.xx:5174/
```

自己访问：

```text
http://localhost:5174/
```

同事访问：

```text
http://显示出来的 Network 地址:5174/
```

## 5. 让同事访问

### 5.1 放行 Windows 防火墙

只需要做一次。用管理员 PowerShell 执行：

```powershell
New-NetFirewallRule -DisplayName "PQRETS Frontend 5174" -Direction Inbound -Protocol TCP -LocalPort 5174 -Action Allow -Profile Private,Domain
```

确认规则存在：

```powershell
Get-NetFirewallRule -DisplayName "PQRETS Frontend 5174"
```

如果显示 `Enabled: True`，说明规则已生效。

### 5.2 选择正确的访问地址

前端启动后可能显示多个 `Network` 地址，例如：

```text
Network: http://192.168.160.1:5174/
Network: http://172.18.18.243:5174/
```

优先让同事尝试公司网络/VPN 对应的地址。通常可以先试：

```text
http://172.18.18.243:5174/
```

如果打不开，再试另一个 `Network` 地址。

## 6. 每次开机后需要做什么

每次电脑重启后，需要重新启动服务：

```bash
docker compose -f docker-compose.dev.yml --env-file .env.dev up -d db backend
```

然后：

```bash
cd frontend
npm run dev
```

防火墙规则不需要每次创建。它是持久规则，重启后仍然存在。

## 7. 常见问题

### 7.1 同事打不开页面

检查：

1. 前端终端是否还在运行。
2. 前端是否显示 `Network: http://...:5174/`。
3. Windows 防火墙是否放行 `5174`。
4. 同事是否和你在同一个公司网络或 VPN。
5. 同事访问的是 `Network` 地址，不是 `localhost`。

### 7.2 页面打开了，但数据加载失败

检查后端是否运行：

```bash
docker compose -f docker-compose.dev.yml ps
```

如果后端没运行，重新启动：

```bash
docker compose -f docker-compose.dev.yml --env-file .env.dev up -d backend
```

### 7.3 Assessment Dashboard 显示 unavailable

先刷新页面：

```text
Ctrl + F5
```

如果仍然失败，重启后端：

```bash
docker compose -f docker-compose.dev.yml --env-file .env.dev up -d backend
```

再刷新前端页面。

### 7.4 IP 地址变了

电脑换网络、重启 VPN、切换 Wi-Fi 后，IP 可能变化。

重新启动前端或查看 Vite 输出里的 `Network` 地址，把新的地址发给同事即可。

防火墙规则不需要修改，因为它放行的是端口 `5174`，不是固定 IP。

## 8. 停止系统

停止前端：

```text
在前端终端按 Ctrl + C
```

停止后端和数据库：

```bash
docker compose -f docker-compose.dev.yml down
```

如果只是暂时不用，可以只关闭前端终端；数据库和后端也可以继续后台运行。

## 9. 注意事项

- 本机部署适合临时演示和小范围试用。
- 你的电脑关机、休眠或断网后，同事无法访问。
- 不建议在公共网络开放端口。
- 长期给团队使用时，建议部署到固定服务器。
