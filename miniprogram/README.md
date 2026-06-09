# Codebook 微信小程序

这个小程序默认连接本地 FastAPI 后端演示接口：

```text
http://127.0.0.1:8000/api/v1
```

在微信开发者工具本地调试 HTTP 接口时，请在详情/本地设置中勾选：

```text
不校验合法域名、web-view（业务域名）、TLS 版本以及 HTTPS 证书
```

真机预览时，登录页的 API 地址需要改成 Mac mini 在局域网里的地址，例如：

```text
http://192.168.1.20:8000/api/v1
```

正式发布时，需要换成已经在微信公众平台配置过的 HTTPS 域名：

```text
https://your-domain.example/api/v1
```

页面结构：

- 登录页：配置后端 API 地址，并生成演示数据。
- 身份选择：进入学员/家长端、教师端、校区端。
- 学员/家长端：查看课表、考勤状态、课时余额和课时流水。
- 教师端：查看课次，并手动确认到课、迟到、缺勤、请假等消课规则。
- 校区端：查看校区概览、模拟 USB 摄像头打卡、管理学员课时和课次。

本地类型检查：

```powershell
cd miniprogram
npm install --registry=https://registry.npmmirror.com
npm run typecheck
```
