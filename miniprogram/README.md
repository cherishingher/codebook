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
- 登录页：配置后端 API 地址，支持生成演示数据，也支持手动填写 campusId / studentId / teacherId 进入真实接口调试。
- 身份选择：进入学员/家长端、教师端、校区端，并保留已填写的真实身份 ID。
- 学员/家长端：通过真实接口查看课表、考勤状态、课时余额和课时流水；接口失败时回退演示数据。
- 教师端：通过真实接口查看课次、快捷新建课次，并逐个学员确认到课、迟到、缺勤、请假。
- 校区端：通过真实接口查看校区看板、学员列表、创建学员、开课时账户/加课时、创建课次、保存消课规则、运行缺勤任务。

当前小程序已经接入的真实接口：

- `/campus/dashboard`
- `/campus/students`
- `/campus/courses`
- `/campus/teachers`
- `/campus/lessons`
- `/campus/hour-accounts`
- `/campus/hour-ledgers`
- `/campus/deduction-rules`
- `/teacher/lessons`
- `/teacher/lessons/{lesson_id}/attendance/confirm`
- `/learner/dashboard`
- `/learner/lessons`
- `/learner/hour-accounts`
- `/learner/hour-ledgers`

本地类型检查：

```powershell
cd miniprogram
npm install --registry=https://registry.npmmirror.com
npm run typecheck
```
