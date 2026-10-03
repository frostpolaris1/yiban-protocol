# yiban-protocol

易班（Yiban）**网页 OAuth + nightAttendance 签到链路**的洁净室协议解析库。

只做两件事——**解析**（bytes/dict → 结构化数据）与**构造**（结构化参数 → 请求体/URL）。
不做网络请求、会话/cookie 管理、重试、验证码求解、异步 API。全部同步纯函数，
无 I/O、无日志、无全局状态，**核心仅依赖 Python 标准库**（≥3.10）。

> 本库按[洁净室纪律](PROVENANCE.md)实现：唯一规格来源是对**自有账号**签到流量的
> 第一手黑盒旁路记录（已脱敏），实现过程未参考任何第三方易班项目的源代码。
> 上游行为变化时以新的实拍证据修订规格，而不是靠猜。

## 上游契约（六步链路）

本库覆盖的是这条经过实拍验证的链路（端到端实测 < 1 秒）：

| 步 | 请求 | 本库职责 |
|---|---|---|
| ① | `GET oauth.yiban.cn/code/html`（授权页） | `page.py`：提取 `page_use` 令牌 + 登录 RSA 公钥 |
| ② | `POST oauth.yiban.cn/code/usersure?ajax_sign=…`（**登录+授权合一**） | `forms.py`：构造表单；`envelopes.py`：解析 `s200/reUrl`；`crypto.py`：密码加密 |
| ③ | `GET f.yiban.cn/iframe/index`（302 下发 `verify_request`） | `location.py`：令牌提取（query 末位容错） |
| ④ | `GET api.uyiban.com/base/c/auth/yiban`（换取会话+身份） | `identity.py`：身份/应用清单 |
| ⑤ | `GET …/nightAttendance/student/index/signPosition` | `position.py`：多候选签到点/边界多边形/时间窗/照片要求 |
| ⑥ | `POST …/nightAttendance/student/index/signIn` | `forms.py`：构造 `SignInfo` 请求体（逐字节同构）；`envelopes.py`：解析结果 |

## 模块总览

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

尚未发布 PyPI，当前请直接从仓库安装或 vendoring：

```bash
pip install git+https://github.com/frostpolaris1/yiban-protocol.git            # 纯解析/构造，零第三方依赖
pip install 'yiban-protocol[crypto] @ git+https://github.com/frostpolaris1/yiban-protocol.git'  # 追加 RSA 加密
```

`[crypto]` extra 仅用于 `yiban_protocol.crypto`。不安装时核心模块完全可用；
未装依赖而导入 crypto 会抛出带安装指引的 `ImportError`。
核心只有标准库，也可以直接把 `src/yiban_protocol/` 拷进你的项目（vendoring）。

## 用法示例

```python
# 以下全部为纯函数，不发起任何请求；网络/会话由调用方自行负责。
from yiban_protocol import (
    parse_authorize_page, parse_usersure_response, parse_identity,
    parse_sign_position, build_usersure_form, build_sign_in_body, encrypt_password,
)

# 1. 授权页 -> page_use（即 usersure 的 ajax_sign）+ 登录公钥
page = parse_authorize_page(html)
# 2. 用公钥加密密码（需 [crypto] extra）
pwd = encrypt_password("secret", page.public_key_pem)
# 3. 构造 usersure 请求体，然后由调用方 POST 到
#    https://oauth.yiban.cn/code/usersure?ajax_sign={page.page_use}
body = build_usersure_form("13800000000", pwd, client_id, redirect_uri)
# 4. 解析 usersure 响应 -> 是否成功 + 跳转地址
result = parse_usersure_response(raw)
# 5. 解析身份响应 -> 学校/人员/应用（含 nightattendance 的 AuthCode）
ident = parse_identity(envelope_data)
# 6. 解析签到点（candidates 可能多于一个）并构造签到请求体
config = parse_sign_position(sign_position_data)
sign_body = build_sign_in_body(
    lnglat=config.positions[0].lnglat, address=config.positions[0].address
)
```

## 错误模型

- `ParseError`：输入不符合已知形态（带字段名与 ≤120 字符片段摘要）；
- `SessionExpired`：信封 `code == 999`（会话失效，调用方必须重登）；
- 业务失败码（如 usersure `e001`）**作为数据返回**，不抛异常；
- `looks_like_challenge` 只检测风控/挑战页，**不提供任何绕过手段**——命中即应停止并人工介入。

## 测试与夹具

```bash
pip install -e '.[dev]'
pytest
```

`tests/fixtures/` 中的夹具来自真实上游响应的**合成化副本**：字段结构与实拍逐一对应，
所有个人数据（姓名/学号/学校/坐标/电话/令牌）均已替换为合成值。
测试不触网；`build_sign_in_body` 与夹具整串相等断言保证编码形态不漂移。

## 文档

- [SPEC.md](SPEC.md) —— 解析器契约（唯一规格来源：模块 API、容错规则、错误分类法、测试矩阵）
- [PROVENANCE.md](PROVENANCE.md) —— 洁净室溯源声明
- [DISCLAIMER.md](DISCLAIMER.md) —— 免责与合规声明

## 路线图

- **0.1**（当前）解析/构造核心
- **0.2** `inspector`：离线流量/夹具自检工具（对照本库契约逐跳校验）
- **0.3** `mock`：本地假上游，用于不触网端到端演练

## 声明

本项目与易班官方及其运营方**无任何关联**；仅供学习研究及对自有账号的合规自动化使用，
不提供任何风控/验证码绕过手段。完整内容见 [DISCLAIMER.md](DISCLAIMER.md)。

## 许可

[MIT](LICENSE)。
