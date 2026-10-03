# yiban-protocol

易班（Yiban）网页 OAuth + nightAttendance 签到链路的协议解析库。

只做两件事——**解析**（bytes/dict → 结构化数据）与**构造**（结构化参数 → 请求体/URL）。
不做网络请求、会话/cookie 管理、重试、验证码求解。全部同步纯函数，无 I/O、无日志、
无全局状态，**核心仅依赖 Python 标准库**（≥3.10）。

## 覆盖范围

| 步 | 请求 | 本库职责 |
|---|---|---|
| ① | `GET oauth.yiban.cn/code/html`（授权页） | 提取 `page_use` 令牌 + 登录 RSA 公钥 |
| ② | `POST oauth.yiban.cn/code/usersure`（登录+授权） | 构造表单、解析 `s200/reUrl`、密码加密（可选） |
| ③ | `GET f.yiban.cn/iframe/index`（302） | 提取 `verify_request` 令牌 |
| ④ | `GET api.uyiban.com/base/c/auth/yiban` | 解析身份/应用清单 |
| ⑤ | `GET …/nightAttendance/…/signPosition` | 解析签到点（多候选/边界/时间窗/照片要求） |
| ⑥ | `POST …/nightAttendance/…/signIn` | 构造 `SignInfo` 请求体、解析结果 |

## 模块

| 模块 | 内容 |
|---|---|
| `page` | `AuthorizePage`、`parse_authorize_page` |
| `location` | `extract_verify_request` |
| `envelopes` | `parse_api_envelope`、`parse_usersure_response`、`looks_like_challenge` |
| `identity` | `Identity`、`App`、`parse_identity` |
| `position` | `SignPositionConfig`、`TimeWindow`、`Position`、`parse_sign_position` |
| `forms` | `build_usersure_form`、`build_sign_in_body` |
| `crypto`（可选） | `encrypt_password`（RSA-1024 PKCS#1 v1.5 → base64） |
| `errors` | `ParseError`、`SessionExpired` |

完整契约（签名、容错规则、脏数据形态）见 [SPEC.md](SPEC.md)。

## 安装

```bash
pip install git+https://github.com/frostpolaris1/yiban-protocol.git            # 纯解析/构造，零第三方依赖
pip install 'yiban-protocol[crypto] @ git+https://github.com/frostpolaris1/yiban-protocol.git'  # 追加 RSA 加密
```

也可以直接把 `src/yiban_protocol/` 拷进你的项目（vendoring）。
未装 `pycryptodome` 时核心完全可用；导入 crypto 模块会抛出带安装指引的 `ImportError`。

## 用法

```python
from yiban_protocol import (
    parse_authorize_page, parse_usersure_response, parse_identity,
    parse_sign_position, build_usersure_form, build_sign_in_body, encrypt_password,
)

page = parse_authorize_page(html)                      # ① -> page_use + 公钥
pwd = encrypt_password("secret", page.public_key_pem)  # ② 密码加密（需 [crypto]）
body = build_usersure_form("13800000000", pwd, client_id, redirect_uri)
result = parse_usersure_response(raw)                  # ② -> s200 + reUrl
ident = parse_identity(envelope_data)                  # ④ -> 学校/人员/应用
config = parse_sign_position(sign_position_data)       # ⑤ -> 签到点（可能多个）
sign_body = build_sign_in_body(                        # ⑥ -> SignInfo 请求体
    lnglat=config.positions[0].lnglat, address=config.positions[0].address
)
# 以上全部为纯函数，不发起任何请求；网络/会话由调用方自行负责。
```

## 错误模型

- `ParseError`：输入不符合已知形态（带字段名与 ≤120 字符片段摘要）；
- `SessionExpired`：信封 `code == 999`（会话失效，调用方必须重登）；
- 业务失败码（如 usersure `e001`）**作为数据返回**，不抛异常；
- `looks_like_challenge` 只检测风控/挑战页，**不提供任何绕过手段**。

## 测试

```bash
pip install -e '.[dev]'
pytest
```

夹具为脱敏合成数据（结构对应真实响应，个人数据全部虚构）；测试不触网。

## 文档

- [SPEC.md](SPEC.md) —— 解析器契约（API、容错规则、错误分类、测试矩阵）
- [PROVENANCE.md](PROVENANCE.md) —— 实现溯源说明
- [DISCLAIMER.md](DISCLAIMER.md) —— 免责与合规声明（**使用前必读**）

## 路线图

- **0.1**（当前）解析/构造核心
- **0.2** `inspector`：离线流量/夹具自检工具
- **0.3** `mock`：本地假上游，用于不触网端到端演练

## 许可

[MIT](LICENSE)。
